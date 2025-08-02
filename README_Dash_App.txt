
# Agrivoltaic Optimization Tool – Dash App

## ✅ How to Run This Dash App

### 📌 Option 1 – From Spyder (after setup)
1. Open Anaconda Navigator
2. Go to **Environments** → `agri_dash_env` → **Launch Spyder**
3. Open `app.py` and click Run
4. ✅ The browser will open automatically at: [http://127.0.0.1:8050](http://127.0.0.1:8050)

---

### 📌 Option 2 – From Anaconda Prompt (recommended for sharing)
1. Open **Anaconda Prompt**
2. Run:
   conda activate agri_dash_env
   python C:/Users/nisni/OneDrive/Documents/Python/Agri_OPTI_UI/app.py
   ↑ Replace this path with the full path to your own `app.py` file  
     (Tip: you can drag the file into the terminal to auto-fill the correct path)
3. ✅ The browser will open automatically at: [http://127.0.0.1:8050](http://127.0.0.1:8050)

This method works without opening Spyder.
You can share this with others — they only need to install Anaconda, set up the environment, and run the two lines above.

---

## 🛠️ Environment Setup for New Users

1. Install Anaconda: https://www.anaconda.com
2. Open **Anaconda Prompt** and run:
   conda create -n agri_dash_env python=3.11
   conda activate agri_dash_env
   pip install dash dash-bootstrap-components pandas plotly

(Optional) Install Spyder:
   conda install spyder -c conda-forge

Then use Option 1 or 2 to run the app.

---

## 🌐 Helpful Links

- Localhost (your app will run here): http://127.0.0.1:8050/
- Dash Gallery (examples and design inspiration): https://dash.gallery/Portal/
