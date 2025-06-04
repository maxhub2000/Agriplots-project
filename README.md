# Agriplots Linear Programming Optimization

This project optimizes photovoltaic (PV) installations on agricultural land using linear programming. It aims to maximize energy production while minimizing impacts on agricultural revenue and satisfying various energy distribution constraints.

---

## 🔧 Requirements

- Python 3.8+
- IBM ILOG CPLEX Optimization Studio  
  (You **must use the full version**, not the Community Edition — see below)

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

## ⚙️ IBM CPLEX Setup and `oplrun` Configuration

This project relies on **IBM ILOG CPLEX Optimization Studio** to solve the optimization model via the `oplrun` command-line tool.

> ⚠️ **Important:** The free **Community Edition of CPLEX will NOT work** — the model exceeds its problem size limits. You must use the **full version**, which is freely available via IBM’s Academic Initiative.

### ✅ Step 1: Install CPLEX

#### Option A: Academic Use (Free License)
1. Visit [https://www.ibm.com/academic/home](https://www.ibm.com/academic/home)
2. Sign in using your university email
3. Search for **CPLEX Optimization Studio** and download the full version
4. Install it with default options

#### Option B: Trial or Commercial
Get it from [https://www.ibm.com/products/ilog-cplex-optimization-studio](https://www.ibm.com/products/ilog-cplex-optimization-studio) via a free trial or commercial license.

---

### ✅ Step 2: Add `oplrun` to System PATH

After installation, locate the `oplrun` executable:

- Windows:  
  `C:\Program Files\IBM\ILOG\CPLEX_Studio<version>\opl\bin\x64_win64`

- macOS:  
  `/Applications/CPLEX_Studio<version>/opl/bin/x86-64_osx`

- Linux:  
  `/opt/ibm/ILOG/CPLEX_Studio<version>/opl/bin/x86-64_linux`

Then:

#### Windows
1. Open Start → search **Environment Variables**
2. Click "Edit the system environment variables"
3. Click **Environment Variables**
4. Edit the `Path` variable under "System Variables"
5. Add a **new entry**:
   ```
   C:\Program Files\IBM\ILOG\CPLEX_Studio<version>\opl\bin\x64_win64
   ```
6. Click OK and restart your terminal

#### macOS/Linux
Edit your shell config:
```bash
nano ~/.zshrc   # or ~/.bashrc
```
Add:
```bash
export PATH="/path/to/opl/bin/x86-64_osx:$PATH"
```
Apply changes:
```bash
source ~/.zshrc
```

### ✅ Step 3: Confirm it Works

Run:
```bash
oplrun -h
```
If you see usage instructions, the setup is complete.

---

### ❗ Community Edition Limitation

If you see this error:
```
CPLEX Error 1016: Community Edition. Problem size limits exceeded.
```
It means you are using the **Community Edition**, which only supports models with ≤ 1000 variables or constraints. This project exceeds those limits — please install the **full academic version** as described above.

---

## 🧩 How to Use `oplrun` in the Code

This project does not rely on system-wide PATH only — the full path to `oplrun` is set explicitly in the code for reliability.

In `Agriplots_solve_opl.py`, near the top of the file, define:

```python
# Windows example:
OPLRUN_PATH = r"C:\Program Files\IBM\ILOG\CPLEX_Studio<version>\opl\bin\x64_win64\oplrun.exe"
```

Then in the `solve_opl_model()` function, the script uses this path directly:

```python
def solve_opl_model(mod_file, dat_file, output_file=None):
    oplrun_path = OPLRUN_PATH
    ...
```

Replace `<version>` with the actual installed version, such as `CPLEX_Studio2211`.

---

## 🏗 Contributing

This project is research-oriented. Feel free to fork it, modify it, or reuse it for your own agrivoltaic optimization research.
