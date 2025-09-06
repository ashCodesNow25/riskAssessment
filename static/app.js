
fetch('/api/species')
    .then(res => res.json())
    .then(speciesList => {
        const speciesSelect = document.getElementById('species');
        speciesSelect.innerHTML = '<option value="">Select Species</option>';
        speciesList.forEach(species => {
            speciesSelect.innerHTML += `<option value="${species}">${species.charAt(0).toUpperCase() + species.slice(1)}</option>`;
        });
    });
document.getElementById('pdeForm').addEventListener('submit', function(e) {
    e.preventDefault();
    // Hide results while loading
    document.getElementById('results').classList.add('hidden');
    // Gather input values
    const noael = parseFloat(document.getElementById('noael').value);
    const doseType = document.getElementById('doseType').value;
    const species = document.getElementById('species').value;
    const humanWeight = parseFloat(document.getElementById('humanWeight').value);
    const f2 = parseFloat(document.getElementById('f2').value);
    const f3 = document.getElementById('f3').value;
    const f4 = parseFloat(document.getElementById('f4').value);
    const f5 = parseFloat(document.getElementById('f5').value);
    fetch('/api/calculate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            noael, doseType, species, humanWeight, f2, f3, f4, f5
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            document.getElementById('results').classList.remove('hidden');
            document.getElementById('f1Value').textContent = '-';
            document.getElementById('totalFactor').textContent = '-';
            document.getElementById('pdeValue').textContent = 'Error';
            document.getElementById('formulaDisplay').textContent = data.error;
            document.getElementById('warnings').style.display = 'none';
            return;
        }
        document.getElementById('f1Value').textContent = data.f1;
        document.getElementById('totalFactor').textContent = data.totalFactor.toFixed(0);
        document.getElementById('pdeValue').textContent = data.pde.toFixed(3) + ' mg/day';
        const formulaText = `PDE = (${noael} mg/kg/day × ${humanWeight} kg) ÷ (${data.f1} × ${data.f2} × ${data.f3} × ${data.f4} × ${data.f5})\nPDE = ${(noael * humanWeight).toFixed(3)} ÷ ${data.totalFactor} = ${data.pde.toFixed(3)} mg/day`;
        document.getElementById('formulaDisplay').textContent = formulaText;
        // Warnings
        let warnings = [];
        if (doseType === 'loael') warnings.push('• Calculation based on LOAEL rather than NOAEL - additional safety considerations may be needed');
        if (parseInt(data.f3) >= 5) warnings.push('• Short-term study duration - may not adequately represent chronic exposure risks');
        if (parseInt(data.f4) >= 5) warnings.push('• Severe toxicity reported in animal studies - consider additional safety measures');
        if (parseInt(data.f5) >= 5) warnings.push('• Data quality concerns - consider additional studies or conservative interpretation');
        if (humanWeight !== 50) warnings.push('• Non-standard body weight used - ensure appropriate for target population');
        warnings.push('• PDE values qualify general systemic toxicity only - not local effects like irritation/sensitization');
        warnings.push('• Consider reproductive toxicity data separately if relevant to patient population');
        warnings.push('• PDE is a safety threshold, not an acceptable analytical limit');
        if (warnings.length > 0) {
            document.getElementById('warningText').innerHTML = warnings.join('<br>');
            document.getElementById('warnings').style.display = 'block';
        } else {
            document.getElementById('warnings').style.display = 'none';
        }
        document.getElementById('results').classList.remove('hidden');
        document.getElementById('results').scrollIntoView({ behavior: 'smooth' });
    })
    .catch(err => {
        document.getElementById('results').classList.remove('hidden');
        document.getElementById('f1Value').textContent = '-';
        document.getElementById('totalFactor').textContent = '-';
        document.getElementById('pdeValue').textContent = 'Error';
        document.getElementById('formulaDisplay').textContent = 'API error: ' + err;
        document.getElementById('warnings').style.display = 'none';
    });
});
