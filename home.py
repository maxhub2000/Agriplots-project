# -*- coding: utf-8 -*-
import dash
from dash import html, dcc, Output, Input, State
import dash_bootstrap_components as dbc
import pandas as pd
import os
import sys
import time

# Add optimisation_tool to sys.path for importing main (keep if your files aren't in same dir)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'optimisation_tool')))
from Agriplots_solve_opl import main as run_optimization_tool

# === Load Filter Options (bulk) ===
def get_unique_values_bulk(df: pd.DataFrame, columns: list[str]) -> dict[str, list[dict]]:
    """
    Return a dict mapping each requested column name to a list
    of Dash dropdown options: [{"label": v, "value": v}, ...].
    - Trims strings, drops NaNs and empty strings
    - Sorts values
    """
    options_by_col: dict[str, list[dict]] = {}
    for colname in columns:
        if colname not in df.columns:
            print(f"Warning: Column '{colname}' not found in {excel_path}")
            options_by_col[colname] = []
            continue

        col = df[colname].dropna()
        if col.dtype == object:
            col = col.astype(str).str.strip()
            col = col[col != ""]

        unique_sorted = sorted(set(col.tolist()))
        options_by_col[colname] = [{"label": v, "value": v} for v in unique_sorted]

    return options_by_col

# excel_path = "data-Agri_OPTI_UI/Agriplots dataset - 1,000 rows.xlsx"
excel_path = "data-Agri_OPTI_UI/Agriplots_final - Full data - including missing rows.xlsx"
csv_path = "data-Agri_OPTI_UI/Agriplots_final - Full data - including missing rows.csv"
csv_path = "data-Agri_OPTI_UI/agrivoltaics_fix_13.8.25- main data.csv"

cols_needed = ["YeshuvName", "Machoz", "AnafSub"]

start_time_ = time.time()
try:
    # df = pd.read_excel(excel_path)
    df = pd.read_csv(csv_path)
except Exception as e:
    print(f"Error reading '{excel_path}': {e}")

unique_opts = get_unique_values_bulk(df, cols_needed)
elapsed_time = time.time() - start_time_
print(f"loading of UI took {elapsed_time:.2f} seconds")

yeshuv_options    = unique_opts.get("YeshuvName", [])
machoz_options    = unique_opts.get("Machoz", [])
crop_type_options = unique_opts.get("AnafSub", [])

# --- Small control styles ---
DD_STYLE    = {"width": "260px"}        # dropdowns smaller
NUM_STYLE   = {"width": "120px"}        # number inputs compact
LABEL_STYLE = {"marginBottom": "4px"}
OP_STYLE    = {"width": "76px", "marginRight": "6px"}  # operator dropdown size

def build_eshkol_inputs_grouped():
    rows = []

    # Row 1: Eshkol 1–5 Lower
    row1 = []
    for i in range(1, 6):
        row1.append(
            dbc.Col(
                [
                    html.Label(f"Eshkol {i} Lower (%)", style=LABEL_STYLE),
                    dcc.Input(id=f"eshkol-{i}-lower", type="number", value=0, className="form-control", style={**NUM_STYLE, "marginBottom": "6px"}),
                ],
                md=2, sm=4, xs=6
            )
        )
    rows.append(dbc.Row(row1, className="g-2"))

    # Row 2: Eshkol 1–5 Upper
    row2 = []
    for i in range(1, 6):
        row2.append(
            dbc.Col(
                [
                    html.Label(f"Eshkol {i} Upper (%)", style=LABEL_STYLE),
                    dcc.Input(id=f"eshkol-{i}-upper", type="number", value=100, className="form-control", style={**NUM_STYLE, "marginBottom": "6px"}),
                ],
                md=2, sm=4, xs=6
            )
        )
    rows.append(dbc.Row(row2, className="g-2"))

    # Row 3: Eshkol 6–10 Lower
    row3 = []
    for i in range(6, 11):
        row3.append(
            dbc.Col(
                [
                    html.Label(f"Eshkol {i} Lower (%)", style=LABEL_STYLE),
                    dcc.Input(id=f"eshkol-{i}-lower", type="number", value=0, className="form-control", style={**NUM_STYLE, "marginBottom": "6px"}),
                ],
                md=2, sm=4, xs=6
            )
        )
    rows.append(dbc.Row(row3, className="g-2"))

    # Row 4: Eshkol 6–10 Upper
    row4 = []
    for i in range(6, 11):
        row4.append(
            dbc.Col(
                [
                    html.Label(f"Eshkol {i} Upper (%)", style=LABEL_STYLE),
                    dcc.Input(id=f"eshkol-{i}-upper", type="number", value=100, className="form-control", style={**NUM_STYLE, "marginBottom": "6px"}),
                ],
                md=2, sm=4, xs=6
            )
        )
    rows.append(dbc.Row(row4, className="g-2"))

    return rows

# === Layout ===
layout = dbc.Container([
    dcc.Store(id="run-state", data="idle"),
    dbc.Row([
        dbc.Col(
            dbc.Tabs([
                # Filters Tab
                dbc.Tab(label="Filters", children=[
                    html.Div([
                        html.H4("Filter the dataset (optional)"),
                        html.P("Use any of the filters below to narrow the dataset the optimization model will run on. "
                               "You can also leave them blank to run on the full dataset."),
                        html.Div([
                            dbc.Label("Yeshuv"),
                            dcc.Dropdown(id="yeshuv-dropdown", options=yeshuv_options, multi=True,
                                         placeholder="All Yeshuvim", style=DD_STYLE),
                        ], style={"marginBottom": "10px"}),

                        html.Div([
                            dbc.Label("Machoz"),
                            dcc.Dropdown(id="machoz-dropdown", options=machoz_options, multi=True,
                                         placeholder="All Machozot", style=DD_STYLE),
                        ], style={"marginBottom": "10px"}),

                        html.Div([
                            dbc.Label("Crop Type"),
                            dcc.Dropdown(id="crop-dropdown", options=crop_type_options, multi=True,
                                         placeholder="All Crop Types", style=DD_STYLE),
                        ], style={"marginBottom": "10px"}),

                        # --- Numeric filters (labels updated) ---
                        html.Hr(),
                        html.H5("Numeric filters"),
                        html.Div([
                            html.Label("Energy production per location filter", style=LABEL_STYLE),
                            dcc.Dropdown(
                                id="op-energy-fix",
                                options=[{"label": s, "value": s} for s in [">=", ">", "=", "<=", "<"]],
                                value=">=",
                                clearable=False,
                                style=OP_STYLE
                            ),
                            dcc.Input(
                                id="val-energy-fix",
                                type="number",
                                placeholder="Value",
                                className="form-control",
                                style=NUM_STYLE
                            ),
                        ], style={"display": "flex", "alignItems": "center", "gap": "8px", "marginBottom": "8px"}),

                        html.Div([
                            html.Label("Area in dunam per location filter", style=LABEL_STYLE),
                            dcc.Dropdown(
                                id="op-dunam",
                                options=[{"label": s, "value": s} for s in [">=", ">", "=", "<=", "<"]],
                                value=">=",
                                clearable=False,
                                style=OP_STYLE
                            ),
                            dcc.Input(
                                id="val-dunam",
                                type="number",
                                placeholder="Value",
                                className="form-control",
                                style=NUM_STYLE
                            ),
                        ], style={"display": "flex", "alignItems": "center", "gap": "8px"}),

                        html.Hr(),

                        dbc.Checkbox(
                            id="limit-eshkol-energy",
                            value=False,
                            label="Limit energy production per Eshkol"
                        ),

                        # Render inputs always (avoid nonexistent ID errors); toggle visibility via style
                        html.Div(
                            id="eshkol-bounds-container",
                            children=build_eshkol_inputs_grouped(),
                            style={"marginTop": "12px", "display": "none"}
                        ),
                    ], style={"padding": "20px", "backgroundColor": "#f0f0f0", "color": "black"})
                ]),

                # Model Tab
                dbc.Tab(label="Model", children=[
                    html.Div([
                        html.H4("Configure the optimization model"),
                        html.P("Choose the main configuration of the model: objective function and the constraints to enforce."),
                        html.H5("OBJECTIVE FUNCTION TYPE"),
                        dbc.RadioItems(
                            id="objective-type",
                            options=[
                                {"label": "maximum energy", "value": "maximum energy"},
                                {"label": "minimum area", "value": "minimum area"},
                                {"label": "maximum remaining percentage of revenue", "value": "maximum remaining percentage of revenue"},
                                {"label": "minimum installation cost", "value": "minimum installation cost"},
                            ],
                            value="maximum energy",
                            labelStyle={"display": "block"}
                        ),
                        html.Br(),

                        html.H5("MAIN CONSTRAINT"),
                        dbc.RadioItems(
                            id="main-constraint",
                            options=[
                                {"label": "total_energy_constraint", "value": "total_energy_constraint"},
                                {"label": "total_area_constraint", "value": "total_area_constraint"},
                                {"label": "remaining_percentage_of_revenue_constraint", "value": "remaining_percentage_of_revenue_constraint"},
                                {"label": "total_installation_cost_constraint", "value": "total_installation_cost_constraint"},
                            ],
                            value="total_area_constraint",
                            labelStyle={"display": "block"}
                        ),
                        html.Br(),

                        html.H5("FULL CONTINUOUS MODEL"),
                        dbc.Checkbox(id="continuous-model", value=False, label="Use full continuous model"),
                        html.Br(),

                        html.H5("COMMON CONSTRAINTS"),
                        dbc.Checklist(
                            id="common-constraints",
                            options=[
                                {"label": "energy_production_per_yeshuv_constraint", "value": "energy_production_per_yeshuv_constraint"},
                                {"label": "energy_production_per_machoz_constraint", "value": "energy_production_per_machoz_constraint"},
                                {"label": "energy_production_per_eshkol_upper_bounding_constraint", "value": "energy_production_per_eshkol_upper_bounding_constraint"},
                                {"label": "energy_production_per_eshkol_lower_bounding_constraint", "value": "energy_production_per_eshkol_lower_bounding_constraint"},
                            ],
                            value=[
                                "energy_production_per_yeshuv_constraint",
                                "energy_production_per_machoz_constraint",
                                "energy_production_per_eshkol_upper_bounding_constraint",
                                "energy_production_per_eshkol_lower_bounding_constraint"
                            ],
                            labelStyle={"display": "block"}
                        ),
                        html.Br(),
                    ], style={"padding": "20px", "backgroundColor": "#f0f0f0", "color": "black"})
                ]),

                # Parameters Tab
                dbc.Tab(label="Parameters", children=[
                    html.Div([
                        html.H4("Set parameter values"),
                        html.P("Provide the parameter values the model should run with."),
                        html.Div([
                            html.Label("Revenue Constraint (%)", style=LABEL_STYLE),
                            dcc.Input(id="rev-input", type="number", value=90, className="form-control", style=NUM_STYLE),
                        ], style={"marginBottom": "10px"}),

                        html.Div([
                            html.Label("Max Area (Dunam)", style=LABEL_STYLE),
                            dcc.Input(id="area-input", type="number", value=20000, className="form-control", style=NUM_STYLE),
                        ], style={"marginBottom": "10px"}),

                        html.Div([
                            html.Label("Total Installation Cost Upper Bound (NIS)", style=LABEL_STYLE),
                            dcc.Input(id="cost-input", type="number", value=500000, className="form-control", style=NUM_STYLE),
                        ], style={"marginBottom": "10px"}),

                        html.Div([
                            html.Label("Total Energy Lower Bound", style=LABEL_STYLE),
                            dcc.Input(id="energy-input", type="number", value=1000, className="form-control", style=NUM_STYLE),
                        ], style={"marginBottom": "16px"}),
                    ], style={"padding": "20px", "backgroundColor": "#f0f0f0", "color": "black"})
                ]),
            ]),
            width=12
        )
    ]),

    # Run button outside Tabs so it's always visible
    dbc.Row([
        dbc.Col(
            html.Div([
                dcc.Loading(
                    id="run-loading",
                    type="default",
                    children=dbc.Button("Run Optimization", id="run-button",
                                        className="mt-3",
                                        n_clicks=0,
                                        style={"backgroundColor": "#005e66", "color": "white", "border": "none"})
                )
            ], style={"padding": "0 20px 20px 20px"}),
            width=12
        )
    ])
], fluid=True)

# === Toggle visibility of Eshkol bounds ===
@dash.callback(
    Output("eshkol-bounds-container", "style"),
    Input("limit-eshkol-energy", "value"),
    prevent_initial_call=False
)
def toggle_eshkol_bounds(show_bounds):
    base = {"marginTop": "12px"}
    if show_bounds:
        return {**base, "display": "block"}
    return {**base, "display": "none"}

# === Run optimization ===
@dash.callback(
    Output("run-state", "data"),
    Input("run-button", "n_clicks"),
    State("yeshuv-dropdown", "value"),
    State("machoz-dropdown", "value"),
    State("crop-dropdown", "value"),
    # numeric filter state (separate variables)
    State("op-energy-fix", "value"),
    State("val-energy-fix", "value"),
    State("op-dunam", "value"),
    State("val-dunam", "value"),
    # eshkol toggles + values
    State("limit-eshkol-energy", "value"),
    *[State(f"eshkol-{i}-lower", "value") for i in range(1, 10+1)],
    *[State(f"eshkol-{i}-upper", "value") for i in range(1, 10+1)],
    # model config
    State("objective-type", "value"),
    State("main-constraint", "value"),
    State("continuous-model", "value"),
    State("common-constraints", "value"),
    # parameters
    State("rev-input", "value"),
    State("area-input", "value"),
    State("cost-input", "value"),
    State("energy-input", "value"),
    prevent_initial_call=True
)
def run_model(n_clicks, yeshuv, machoz, crop,
              op_energy_fix, val_energy_fix, op_dunam, val_dunam,
              limit_eshkol, *args):

    # Unpack arguments from *args
    lower_vals = list(args[:10])
    upper_vals = list(args[10:20])
    objective, constraint, continuous, common, revenue, area, cost, energy = args[20:]

    # Build separate numeric filter variables
    energy_production_per_location_filter = None
    if val_energy_fix is not None:
        energy_production_per_location_filter = {"op": op_energy_fix, "value": float(val_energy_fix)}

    dunam_per_location_filter = None
    if val_dunam is not None:
        dunam_per_location_filter = {"op": op_dunam, "value": float(val_dunam)}

    # Build bounds dicts
    if not limit_eshkol:
        # no constraints: pass exact 0.0 and 1.0
        lower_bounds = {i+1: 0.0 for i in range(10)}
        upper_bounds = {i+1: 1.0 for i in range(10)}
    else:
        # convert % -> fraction; fall back to 0/1 if None
        lower_bounds = {i+1: ((lower_vals[i] / 100.0) if lower_vals[i] is not None else 0.0) for i in range(10)}
        upper_bounds = {i+1: ((upper_vals[i] / 100.0) if upper_vals[i] is not None else 1.0) for i in range(10)}

    print("=== User Selections ===")
    print(f"Yeshuv: {yeshuv}")
    print(f"Machoz: {machoz}")
    print(f"Crop Type: {crop}")
    print(f"Energy production per location filter: {energy_production_per_location_filter}")
    print(f"Area in dunam per location filter: {dunam_per_location_filter}")
    print(f"Eshkol Lower Bounds (fractions): {lower_bounds}")
    print(f"Eshkol Upper Bounds (fractions): {upper_bounds}")
    print(f"Objective Function Type: {objective}")
    print(f"Main Constraint: {constraint}")
    print(f"Full Continuous Model: {continuous}")
    print(f"Common Constraints: {common}")
    print(f"Revenue Constraint (%): {revenue}")
    print(f"Max Area (Dunam): {area}")
    print(f"Total Installation Cost Upper Bound (NIS): {cost}")
    print(f"Total Energy Lower Bound: {energy}")
    print("========================")

    # Run the tool
    run_optimization_tool(
        data=df,  # preloaded DF retained
        yeshuv_filter=yeshuv,
        machoz_filter=machoz,
        cluster_filter=None,  # cluster filter removed from UI
        crop_filter=crop,
        # new numeric filters as separate variables
        energy_production_per_location_filter=energy_production_per_location_filter,
        dunam_per_location_filter=dunam_per_location_filter,
        objective_function_type=objective,
        main_constraint=constraint,
        full_continuous_model=continuous,
        common_constraints=common,
        eshkol_lower_bounds=lower_bounds,
        eshkol_upper_bounds=upper_bounds,
        parameters={
            "total_energy_lower_bound": energy if energy is not None else 1000,
            "total_area_upper_bound": area if area is not None else 20000,
            "Remaining_percentage_of_revenue_after_influence_on_crops_lower_bound": (revenue / 100.0) if revenue is not None else 0.9,
            "total_installation_cost_upper_bound": cost if cost is not None else 500000
        },
        run_from_ui=True
    )

    # Signal completion to re-enable the button (if you still use run-state logic)
    return "done"

# === Clientside: disable button on click, re-enable on completion ===
app = dash.get_app()

app.clientside_callback(
    """
    function(n_clicks, run_state) {
        // Disable after any click until server marks 'done'
        if (n_clicks && run_state !== "done") { return true; }
        // Re-enable when run_state becomes 'done'
        if (run_state === "done") { return false; }
        return window.dash_clientside.no_update;
    }
    """,
    Output("run-button", "disabled"),
    Input("run-button", "n_clicks"),
    State("run-state", "data")
)

# Reset run-state to 'idle' after it becomes 'done' so subsequent runs work cleanly
@dash.callback(
    Output("run-state", "data", allow_duplicate=True),
    Input("run-state", "data"),
    prevent_initial_call=True
)
def reset_state_if_done(state):
    if state == "done":
        return "idle"
    return dash.no_update
