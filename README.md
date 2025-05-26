# Agriplots Linear Programming Optimization

This project optimizes photovoltaic (PV) installations on agricultural land using linear programming. It aims to maximize energy production while minimizing impacts on agricultural revenue and satisfying various energy distribution constraints.

---

## 🔧 Requirements

- Python 3.8+
- IBM ILOG CPLEX Optimization Studio  
  (Ensure `oplrun` is available in your system `PATH`)

### Install Python packages

```bash
pip install -r requirements.txt
```

---

## 📁 Key Files

- `Agriplots_solve_opl.py` — Main script to run the model
- `prepare_data_for_model.py` — Builds the data dictionary required by the OPL `.mod` file
- `data_preprocessing.py` — Cleans and augments the input dataset
- `output_opl_results_to_excel.py` — Formats and exports model results to Excel
- `utils.py` — Decorators and helper functions
- `Agriplots.mod` / `Agriplots_base_model.mod` — OPL model files defining the optimization logic
- `Agriplots.dat` — Data file generated dynamically for the model

---

## 🚀 How to Run

### 1. Set up Python environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure paths and parameters

Open `Agriplots_solve_opl.py` and adjust file paths and model parameters as needed:
- Dataset paths
- Energy consumption data
- Output locations
- Constraint values

### 4. Run the optimization

```bash
python Agriplots_solve_opl.py
```

---

## 📤 Output

The model generates:
- `installation_decisions_results.xlsx`
- `final_results.xlsx`
- `output.txt` (optional raw OPL output)

---

## 🛠 Notes

- The `.mod` file defines the mathematical optimization model and constraints.
- The `.dat` file is automatically generated from the dataset and model parameters.
- This version is **command-line only** — no PyQt GUI is used.

---

## 🏗 Contributing

This project is research-oriented. Feel free to fork it, modify it, or reuse it for your own agrivoltaic optimization research.
