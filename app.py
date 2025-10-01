# -*- coding: utf-8 -*-
#app.py is the main file that sets up the Dash app using dash-bootstrap-components
# and enables multi-page routing via use_pages=True.

import dash
from dash import html, dcc, dash_table
import dash_bootstrap_components as dbc
import webbrowser
import threading

app = dash.Dash(
    __name__,
    #use_pages=True,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    suppress_callback_exceptions=True
)

# app.layout = dbc.Container([
#     dbc.Navbar(
#         dbc.Container([
#             html.Div([
#                 html.Img(
#                     src="/assets/Tel_Aviv_university_logo-white.svg.png",
#                     style={"height": "40px", "marginRight": "10px"}
#                 ),
#                 html.Span("Agrivoltaic ››\u00A0", style={"fontWeight": "bold", "fontSize": "2em", "color": "white"}),
#                 html.Span("Optimization Tool", style={"fontWeight": "normal", "fontSize": "2em", "color": "white"})
#             ], style={
#                 "display": "flex",
#                 "alignItems": "center",
#                 "justifyContent": "flex-start",  # forces left alignment
#                 "width": "100%",
#                 "marginLeft": "20px"# expands to navbar width
#             }),
#             dbc.Nav([
#                 dbc.NavItem(dcc.Link("", href="/", className="nav-link")), # home button
#             ], className="ml-auto", navbar=True)
#         ], fluid=True, style={"paddingLeft": "0"}),  # ← updated container
#         color=None,
#         style={"backgroundColor": "#333a39"},
#         dark=False,
#         className="mb-4"
#     ),
#     dash.page_container
# ], fluid=True)


from home import layout
app.layout = layout


def open_browser():
    webbrowser.open_new("http://127.0.0.1:8050/")

if __name__ == "__main__":
    threading.Timer(1.5, open_browser).start()
    app.run(debug=True, use_reloader=False)


# The app will open at: http://127.0.0.1:8050/
# If the browser doesn’t open, copy the address manually from the console.

# Dash Gallery (for examples and design inspiration): https://dash.gallery/Portal/

#################################################################################

# === HOW TO RUN THIS DASH APP ===

# Option 1 – From Spyder:
# 1. Open Anaconda Navigator
# 2. Go to Environments → agri_dash_env → Launch Spyder
# 3. Open this file (app.py) and click Run
# 🔗 The browser will open automatically at: http://127.0.0.1:8050/

# Option 2 – From Anaconda Prompt (recommended for sharing):
# 1. Open Anaconda Prompt
# 2. Run:
#    conda activate agri_dash_env
#    python C:/Users/nisni/OneDrive/Documents/Python/Agri_OPTI_UI/app.py
#    python C:/Users/nisni/OneDrive/Documents/Python/Agri_OPTI_UI/app.py
#    ↑ Replace this path with the full path to your own `app.py` file
#      (You can drag the file into the terminal to auto-fill the correct path)
# 🔗 The browser will open automatically at: http://127.0.0.1:8050/

# This method works without Spyder.
# You can share this with others — they only need to install Anaconda, set up the environment, and run the two commands above.

# === SETUP INSTRUCTIONS FOR NEW USERS ===
# 1. Install Anaconda: https://www.anaconda.com
# 2. Open Anaconda Prompt and run:
#    conda create -n agri_dash_env python=3.11
#    conda activate agri_dash_env
#    pip install dash dash-bootstrap-components pandas plotly
# 3. To install Spyder (optional, for development):
#    conda install spyder -c conda-forge
# 4. Use Option 1 or 2 above to run the app

# No need to repeat setup unless the environment is deleted.
