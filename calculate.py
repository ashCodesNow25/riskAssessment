# --- Flask API for PDE calculation ---
from flask import Flask, request, jsonify
from flask_cors import CORS
from dataclasses import dataclass
from typing import Optional

app = Flask(__name__)
CORS(app)

SPECIES_F1 = {
    "mouse": 12.0,
    "rat": 5.0,
    "rabbit": 2.5,
    "dog": 2.0,
    "human": 1.0,
}

DURATION_F3 = {
    "1": 1.0,
    "2": 2.0,
    "5": 5.0,
    "10": 10.0,
}

@dataclass
class PDEInputs:
    effect_dose_mg_per_kg_day: float
    body_weight_kg: float = 50.0
    species: str = "rat"
    f1: Optional[float] = None
    f2: float = 10.0
    duration_key: Optional[str] = "1"
    f3: Optional[float] = None
    f4: float = 1.0
    f5: float = 1.0
    is_loael: bool = False
    enforce_default_loael_f5: bool = True
    label: Optional[str] = None

    def resolved_f1(self) -> float:
        if self.f1 is not None:
            return float(self.f1)
        if self.species is None:
            raise ValueError("Provide 'species' or explicit f1")
        key = self.species.strip().lower()
        if key not in SPECIES_F1:
            raise ValueError(f"Unknown species '{self.species}'. Known: {list(SPECIES_F1.keys())}")
        return SPECIES_F1[key]

    def resolved_f3(self) -> float:
        if self.f3 is not None:
            return float(self.f3)
        if self.duration_key is None:
            raise ValueError("Provide 'duration_key' or explicit f3")
        key = str(self.duration_key).strip().lower()
        if key not in DURATION_F3:
            raise ValueError(f"Unknown duration_key '{self.duration_key}'. Known: {list(DURATION_F3.keys())}")
        return DURATION_F3[key]

@dataclass
class PDEResult:
    pde_mg_per_day: float
    f1: float
    f2: float
    f3: float
    f4: float
    f5: float

    def as_dict(self):
        return {
            "PDE (mg/day)": self.pde_mg_per_day,
            "F1": self.f1,
            "F2": self.f2,
            "F3": self.f3,
            "F4": self.f4,
            "F5": self.f5,
        }

def compute_pde(inputs: PDEInputs) -> PDEResult:
    f1 = inputs.resolved_f1()
    f2 = float(inputs.f2)
    f3 = inputs.resolved_f3()
    f4 = float(inputs.f4)
    f5 = float(inputs.f5)
    if inputs.is_loael and inputs.enforce_default_loael_f5 and f5 < 10.0:
        f5 = 10.0
    numerator = inputs.effect_dose_mg_per_kg_day * inputs.body_weight_kg
    denominator = f1 * f2 * f3 * f4 * f5
    if denominator <= 0:
        raise ValueError("Composite denominator must be > 0")
    pde = numerator / denominator
    return PDEResult(pde_mg_per_day=pde, f1=f1, f2=f2, f3=f3, f4=f4, f5=f5)

@app.route('/api/calculate', methods=['POST'])
def api_calculate():
    data = request.get_json()
    try:
        effect_dose = float(data.get('noael'))
        body_weight = float(data.get('humanWeight', 50))
        species = data.get('species', 'rat')
        f2 = float(data.get('f2', 10))
        f3 = float(data.get('f3', 1))
        f4 = float(data.get('f4', 1))
        f5 = float(data.get('f5', 1))
        dose_type = data.get('doseType', 'noael')
        is_loael = dose_type == 'loael'
        duration_key = str(data.get('f3', '1'))
        inputs = PDEInputs(
            effect_dose_mg_per_kg_day=effect_dose,
            body_weight_kg=body_weight,
            species=species,
            f2=f2,
            duration_key=duration_key,
            f4=f4,
            f5=f5,
            is_loael=is_loael
        )
        result = compute_pde(inputs)
        return jsonify({
            'pde': result.pde_mg_per_day,
            'f1': result.f1,
            'f2': result.f2,
            'f3': result.f3,
            'f4': result.f4,
            'f5': result.f5,
            'totalFactor': result.f1 * result.f2 * result.f3 * result.f4 * result.f5
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400


# Add a simple homepage route
@app.route('/')
def home():
    return '''<h2>PDE Calculator API</h2>
    <p>This is the backend for the PDE Calculator.</p>
    <ul>
        <li>POST to <code>/api/calculate</code> with JSON to calculate PDE.</li>
        <li>Use the <b>frontend</b> (index.html) for a user interface.</li>
    </ul>
    '''

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
    app.run(host='0.0.0.0', port=5000, debug=True)
    res_ba_inh = pde_from_noael(
        noael_mg_per_kg_day=182.0, species="rat", duration_key="short", f2=10.0, f4=1.0
    )
    print("BA inhalation 28d rat -> PDE (mg/day):", res_ba_inh.pde_mg_per_day)

    # 3) Thalidomide, rabbit embryonic LOAEL 10 mg/kg/day, F1=2.5 (rabbit), F2=10, F3=1, F4=5 (repro), F5=10 (LOAEL) -> ~0.4 mg/day
    res_thal_repro = pde_from_loael(
        loael_mg_per_kg_day=10.0, species="rabbit", duration_key="chronic", f2=10.0, f4=5.0, f5=10.0
    )
    print("Thalidomide rabbit repro LOAEL -> PDE (mg/day):", res_thal_repro.pde_mg_per_day)

    # 4) Maleic anhydride, 1-month inhalation rat LOAEL 1.7 mg/kg/day, severe lung effects -> F4 can be high (e.g., 10)
    # Paper's table implies F1=5, F2=10, F3=10 (short), F4=10 (serious), F5=10 (LOAEL) -> ~0.0017 mg/day
    res_ma_inh = pde_from_loael(
        loael_mg_per_kg_day=1.7, species="rat", duration_key="short", f2=10.0, f4=10.0, f5=10.0
    )
    print("Maleic anhydride 1mo inhalation rat -> PDE (mg/day):", res_ma_inh.pde_mg_per_day)

    # Example: Special population (preterm neonate, 0.5 kg) for BA oral NOAEL 400 mg/kg/day
    from pde import PDEInputs, compute_pde
    res_ba_preterm = compute_pde(PDEInputs(
        effect_dose_mg_per_kg_day=400.0,
        body_weight_kg=0.5,
        species="rat",
        duration_key="chronic",
        f2=10.0,
        f4=1.0,
        f5=1.0,
        is_loael=False
    ))
print("BA oral rat NOAEL w/0.5 kg BW -> PDE (mg/day):", res_ba_preterm.pde_mg_per_day)

SPECIES_F1 = {
    "mouse": 12.0,
    "rat": 5.0,
    "rabbit": 2.5,
    "dog": 2.0,
    "human": 1.0,
}

DURATION_F3 = {
    "1": 1.0,
    "2": 2.0,
    "5": 5.0,
    "10": 10.0,
}

@dataclass
class PDEInputs:
    effect_dose_mg_per_kg_day: float
    body_weight_kg: float = 50.0
    species: str = "rat"
    f1: Optional[float] = None
    f2: float = 10.0
    duration_key: Optional[str] = "1"
    f3: Optional[float] = None
    f4: float = 1.0
    f5: float = 1.0
    is_loael: bool = False
    enforce_default_loael_f5: bool = True
    label: Optional[str] = None

    def resolved_f1(self) -> float:
        if self.f1 is not None:
            return float(self.f1)
        if self.species is None:
            raise ValueError("Provide 'species' or explicit f1")
        key = self.species.strip().lower()
        if key not in SPECIES_F1:
            raise ValueError(f"Unknown species '{self.species}'. Known: {list(SPECIES_F1.keys())}")
        return SPECIES_F1[key]

    def resolved_f3(self) -> float:
        if self.f3 is not None:
            return float(self.f3)
        if self.duration_key is None:
            raise ValueError("Provide 'duration_key' or explicit f3")
        key = str(self.duration_key).strip().lower()
        if key not in DURATION_F3:
            raise ValueError(f"Unknown duration_key '{self.duration_key}'. Known: {list(DURATION_F3.keys())}")
        return DURATION_F3[key]

@dataclass
class PDEResult:
    pde_mg_per_day: float
    f1: float
    f2: float
    f3: float
    f4: float
    f5: float

    def as_dict(self):
        return {
            "PDE (mg/day)": self.pde_mg_per_day,
            "F1": self.f1,
            "F2": self.f2,
            "F3": self.f3,
            "F4": self.f4,
            "F5": self.f5,
        }

def compute_pde(inputs: PDEInputs) -> PDEResult:
    f1 = inputs.resolved_f1()
    f2 = float(inputs.f2)
    f3 = inputs.resolved_f3()
    f4 = float(inputs.f4)
    f5 = float(inputs.f5)
    if inputs.is_loael and inputs.enforce_default_loael_f5 and f5 < 10.0:
        f5 = 10.0
    numerator = inputs.effect_dose_mg_per_kg_day * inputs.body_weight_kg
    denominator = f1 * f2 * f3 * f4 * f5
    if denominator <= 0:
        raise ValueError("Composite denominator must be > 0")
    pde = numerator / denominator
    return PDEResult(pde_mg_per_day=pde, f1=f1, f2=f2, f3=f3, f4=f4, f5=f5)

@app.route('/api/calculate', methods=['POST'])
def api_calculate():
    data = request.get_json()
    try:
        effect_dose = float(data.get('noael'))
        body_weight = float(data.get('humanWeight', 50))
        species = data.get('species', 'rat')
        f2 = float(data.get('f2', 10))
        f3 = float(data.get('f3', 1))
        f4 = float(data.get('f4', 1))
        f5 = float(data.get('f5', 1))
        dose_type = data.get('doseType', 'noael')
        is_loael = dose_type == 'loael'
        duration_key = str(data.get('f3', '1'))
        inputs = PDEInputs(
            effect_dose_mg_per_kg_day=effect_dose,
            body_weight_kg=body_weight,
            species=species,
            f2=f2,
            duration_key=duration_key,
            f4=f4,
            f5=f5,
            is_loael=is_loael
        )
        result = compute_pde(inputs)
        return jsonify({
            'pde': result.pde_mg_per_day,
            'f1': result.f1,
            'f2': result.f2,
            'f3': result.f3,
            'f4': result.f4,
            'f5': result.f5,
            'totalFactor': result.f1 * result.f2 * result.f3 * result.f4 * result.f5
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
