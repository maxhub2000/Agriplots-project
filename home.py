
# -*- coding: utf-8 -*-
import dash
from dash import html, dcc, Output, Input, State, dash_table
import dash_bootstrap_components as dbc
import pandas as pd
import os
import sys

#dash.register_page(__name__, path="/")

# Add optimisation_tool to sys.path for importing main
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'optimisation_tool')))
from Agriplots_solve_opl import main as run_optimization_tool

# === Load Filter Options ===
def get_unique_values(excel_path: str, column_name: str):
    df = pd.read_excel(excel_path)
    if column_name not in df.columns:
        raise KeyError(f"Column '{column_name}' not found in {excel_path}")
    col = df[column_name].dropna()
    if col.dtype == object:
        col = col.astype(str).str.strip()
        col = col[col != ""]
    unique_sorted = sorted(set(col.tolist()))
    return [{"label": v, "value": v} for v in unique_sorted]

def safe_get_options(excel_path: str, column_name: str):
    try:
        return get_unique_values(excel_path, column_name)
    except Exception as e:
        print(f"Warning: Could not load options for '{column_name}' from '{excel_path}'. Error: {e}")
        return []

excel_path = "data-Agri_OPTI_UI/Agriplots dataset - 1,000 rows.xlsx"
yeshuv_options = safe_get_options(excel_path, "YeshuvName")
machoz_options   = safe_get_options(excel_path, "Machoz")
crop_type_options  = safe_get_options(excel_path, "AnafSub")
cluster_options    = [{"label": str(i), "value": str(i)} for i in range(1, 11)]

# === Layout ===
layout = dbc.Container([
    dbc.Row([
        dbc.Col(
            dbc.Tabs([

                # Filters Tab
                dbc.Tab(label="Filters", children=[
                    html.Div([
                        dbc.Label("Yeshuv"),
                        dcc.Dropdown(id="yeshuv-dropdown", options=yeshuv_options, multi=True),
                        html.Br(),
                        dbc.Label("machoz"),
                        dcc.Dropdown(id="machoz-dropdown", options=machoz_options, multi=True),
                        html.Br(),
                        dbc.Label("Cluster"),
                        dcc.Dropdown(id="cluster-dropdown", options=cluster_options, multi=True),
                        html.Br(),
                        dbc.Label("Crop Type"),
                        dcc.Dropdown(id="crop-dropdown", options=crop_type_options, multi=True),
                        html.Br()
                    ], style={"padding": "20px", "backgroundColor": "#f0f0f0", "color": "black"})
                ]),

                # Model Tab
                dbc.Tab(label="Model", children=[
                    html.Div([
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
                        html.Label("Revenue Constraint (%)"),
                        dcc.Input(id="rev-input", type="number", value=90, className="form-control", style={"marginBottom": "15px"}),
                        html.Label("Max Area (Dunam)"),
                        dcc.Input(id="area-input", type="number", value=20000, className="form-control", style={"marginBottom": "15px"}),
                        html.Label("Total Installation Cost Upper Bound (NIS)"),
                        dcc.Input(id="cost-input", type="number", value=500000, className="form-control", style={"marginBottom": "15px"}),
                        html.Label("Total Energy Lower Bound"),
                        dcc.Input(id="energy-input", type="number", value=1000, className="form-control", style={"marginBottom": "15px"}),
                        dbc.Button("Run Optimization", id="run-button", className="mt-2", style={"backgroundColor": "#005e66", "color": "white", "border": "none"})
                    ], style={"padding": "20px", "backgroundColor": "#f0f0f0", "color": "black"})
                ])
            ]),
            width=4
        )
    ])
], fluid=True)

# === Callback ===
@dash.callback(
    Output("run-button", "n_clicks"),
    Input("run-button", "n_clicks"),
    State("yeshuv-dropdown", "value"),
    State("machoz-dropdown", "value"),
    State("cluster-dropdown", "value"),
    State("crop-dropdown", "value"),
    State("objective-type", "value"),
    State("main-constraint", "value"),
    State("continuous-model", "value"),
    State("common-constraints", "value"),
    State("rev-input", "value"),
    State("area-input", "value"),
    State("cost-input", "value"),
    State("energy-input", "value"),
    prevent_initial_call=True
)
def print_selected_inputs(n_clicks, yeshuv, machoz, cluster, crop,
                          objective, constraint, continuous, common,
                          revenue, area, cost, energy):
    print("=== User Selections ===")
    print(f"Yeshuv: {yeshuv}")
    print(f"Machoz: {machoz}")
    print(f"Cluster: {cluster}")
    print(f"Crop Type: {crop}")
    print(f"Objective Function Type: {objective}")
    print(f"Main Constraint: {constraint}")
    print(f"Full Continuous Model: {continuous}")
    print(f"Common Constraints: {common}")
    print(f"Revenue Constraint (%): {revenue}")
    print(f"Max Area (Dunam): {area}")
    print(f"Total Installation Cost Upper Bound (NIS): {cost}")
    print(f"Total Energy Lower Bound: {energy}")
    print("========================")
    run_optimization_tool(
        yeshuv_filter=yeshuv,
        machoz_filter=machoz,
        cluster_filter=cluster,
        crop_filter=crop,
        objective_function_type=objective,
        main_constraint=constraint,
        full_continuous_model=continuous,
        common_constraints=common,
        parameters={
            "total_energy_lower_bound": energy if energy is not None else 1000,
            "total_area_upper_bound": area if area is not None else 20000,
            "Remaining_percentage_of_revenue_after_influence_on_crops_lower_bound": revenue / 100 if revenue is not None else 0.9,
            "total_installation_cost_upper_bound": cost if cost is not None else 500000
        },
        run_from_ui=True
    )
    return n_clicks
