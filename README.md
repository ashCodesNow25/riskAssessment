# PDE Calculator

A web-based Permitted Daily Exposure (PDE) calculator for risk assessment in pharmaceutical and chemical safety, following ICH guidelines and the Ball & Beierschmitt (2020) methodology.

## Features
- Modern, user-friendly web interface for entering study and modifying factor data
- Backend API (Flask) for robust, validated PDE calculations
- Results display with all calculation factors and warnings
- Reference table for ICH standard modifying factors

## How it Works
- The frontend (HTML/JS) collects user input and sends it to the backend API
- The backend (Flask) computes the PDE and returns results as JSON
- Results are displayed below the form, including all factors and the calculation formula

## Requirements
- Python 3.8+
- Flask
- flask-cors

## Setup & Usage

1. **Clone the repository**
   ```bash
   git clone https://github.com/ashCodesNow25/riskAssessment.git
   cd riskAssessment
   ```

2. **Install dependencies**
   ```bash
   pip install flask flask-cors
   ```

3. **Start the backend server**
   ```bash
   python calculate.py
   ```
   This will start the Flask API at `http://localhost:5000`.

4. **Start a local web server for the frontend**
   In a new terminal, run:
   ```bash
   python3 -m http.server 8000
   ```
   This will serve the frontend at `http://localhost:8000/index.html`.

5. **Open the app in your browser**
   Go to [http://localhost:8000/index.html](http://localhost:8000/index.html)

6. **Enter your data and click "Calculate PDE Now"**
   - The results will appear below the button.

## API Usage
You can also use the backend directly via POST requests:

POST `http://localhost:5000/api/calculate`
```json
{
  "noael": 300,
  "doseType": "noael",
  "species": "dog",
  "humanWeight": 50,
  "f2": 10,
  "f3": "1",
  "f4": 1,
  "f5": 1
}
```

## License
MIT

## Credits
- Ball & Beierschmitt (2020) for the PDE calculation methodology
- ICH Q3C/Q3D guidelines
