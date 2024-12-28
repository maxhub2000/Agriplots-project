import pandas as pd
import os
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, PatternFill, Font
from openpyxl.utils import get_column_letter

from utils import measure_time


@measure_time
def output_opl_results_to_excel(df_dataset_, df_opl_results, model_params, installation_decisions_output_path, final_results_output_path):
    main_results_df, installed_PVs_results, energy_produced_per_eshkol_results = df_opl_results
    installation_decisions = output_installation_decisions_results_to_excel(df_dataset_, installed_PVs_results, installation_decisions_output_path)
    area_used_per_machoz = installation_decisions[["Machoz", "area in dunam used"]].groupby("Machoz", as_index=False)["area in dunam used"].sum()
    area_used_per_anafSub = installation_decisions[["AnafSub", "area in dunam used"]].groupby("AnafSub", as_index=False)["area in dunam used"].sum()
    if model_params["total_area_upper_bound"] == 1e12:
        model_params["total_area_upper_bound"] = "No Upper Bound"
    model_params_df = pd.DataFrame([model_params])
    full_results = [main_results_df, model_params_df, energy_produced_per_eshkol_results, area_used_per_machoz, area_used_per_anafSub]
    output_final_results_to_excel(full_results, final_results_output_path)

def output_installation_decisions_results_to_excel(df_dataset_, installed_PVs_results, installation_decisions_output_path):
    relevant_columns_from_input = ["location_id", "OBJECTID", "AnafSub", "YeshuvName", "Machoz", "eshkol", "Potential revenue from crops before PV, mln NIS", "Potential revenue from crops after PV, mln NIS"]
    relevant_df_from_input = df_dataset_[relevant_columns_from_input]
    # convert "OBJECTID" and "Location" column to int, so the merge will be successful
    relevant_df_from_input['OBJECTID'] = relevant_df_from_input['OBJECTID'].astype('int')
    installed_PVs_results['location_id'] = installed_PVs_results['location_id'].astype('int')
    # convert "area in dunam used" column to numeric
    installed_PVs_results["area in dunam used"] = pd.to_numeric(installed_PVs_results["area in dunam used"], errors="coerce")
    # left join installed locations from result of opl model to columns from input dataset
    merged_data = pd.merge(installed_PVs_results, relevant_df_from_input, on="location_id", how="left")    
    # exporting results to excel
    print(f"installation decisions results saved to {installation_decisions_output_path}")
    merged_data.to_excel(installation_decisions_output_path)
    return merged_data

def output_final_results_to_excel(full_results, final_results_output_path):
    main_results, model_params, energy_produced_per_eshkol_results, area_used_per_machoz, area_used_per_anafSub = full_results
    # Create a new workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "Results"

    # Apply column widths
    column_widths = [30, 30, 30, 30, 30, 30]
    for i, width in enumerate(column_widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = width

    # Write the "Model Results" table with formatting
    ws.append(["Model Results"])
    style_range(
        ws,
        "A1", "F1",
        alignment=Alignment(horizontal="center", vertical="center", wrap_text=True),
        fill=PatternFill(start_color="FFFF00", end_color="FFFF00", fill_type="solid"),
        font=Font(bold=True, size=16)
    )
    ws.merge_cells("A1:F1")
    ws.row_dimensions[1].height = 30  # Increase row height for better visibility

    ws.append([
        "Total energy produced in mln", "Total area (in dunam) used",
        "Gini Coefficient value", "Potential revenue before installing PV's",
        "Potential revenue after installing PV's", "Percentage change in revenue"
    ])
    style_range(
        ws,
        "A2", "F2",
        alignment=Alignment(horizontal="center", vertical="center", wrap_text=True),
        fill=PatternFill(start_color="D9D9D9", end_color="D9D9D9", fill_type="solid"),
        font=Font(bold=True, size=14)
    )
    ws.row_dimensions[2].height = 40  # Adjust height for header row

    for row in main_results.itertuples(index=False):
        ws.append(row)

    # Add spacing
    ws.append([])

    # Write the "Model Parameters (input)" tables
    ws.append(["Model Parameters (input)"])
    style_range(
        ws,
        f"A{ws.max_row}", f"F{ws.max_row}",
        alignment=Alignment(horizontal="center", vertical="center", wrap_text=True),
        fill=PatternFill(start_color="FFFF00", end_color="FFFF00", fill_type="solid"),
        font=Font(bold=True, size=16)
    )
    ws.merge_cells(f"A{ws.max_row}:C{ws.max_row}")
    ws.row_dimensions[ws.max_row].height = 30  # Increase row height

    ws.append([
        "Percentage change in revenue lower bound", "Total area upper bound",
        "Gini Coefficient upper bound"
    ])
    style_range(
        ws,
        f"A{ws.max_row}", f"F{ws.max_row}",
        alignment=Alignment(horizontal="center", vertical="center", wrap_text=True),
        fill=PatternFill(start_color="D9D9D9", end_color="D9D9D9", fill_type="solid"),
        font=Font(bold=True, size=14)
    )
    ws.row_dimensions[ws.max_row].height = 40  # Adjust height for parameter row

    for row in model_params.itertuples(index=False):
        ws.append(row)

    # Add similar logic for other parameter DataFrames
    ws.append([])
    ws.append(["Energy produced per Eshkol"])
    style_range(
        ws,
        f"A{ws.max_row}", f"B{ws.max_row}",
        alignment=Alignment(horizontal="center", vertical="center", wrap_text=True),
        fill=PatternFill(start_color="D9D9D9", end_color="D9D9D9", fill_type="solid"),
        font=Font(bold=True, size=16)
    )
    ws.merge_cells(f"A{ws.max_row}:B{ws.max_row}")
    ws.row_dimensions[ws.max_row].height = 25

    ws.append(["Eshkol num", "Energy Produced"])
    style_range(
        ws,
        f"A{ws.max_row}", f"B{ws.max_row}",
        alignment=Alignment(horizontal="center", vertical="center", wrap_text=True),
        fill=PatternFill(start_color="D9D9D9", end_color="D9D9D9", fill_type="solid"),
        font=Font(bold=True, size=14)
    )

    for row in energy_produced_per_eshkol_results.itertuples(index=False):
        ws.append(row)

    ws.append([])
    ws.append(["Area used per Machoz"])
    style_range(
        ws,
        f"A{ws.max_row}", f"B{ws.max_row}",
        alignment=Alignment(horizontal="center", vertical="center", wrap_text=True),
        fill=PatternFill(start_color="D9D9D9", end_color="D9D9D9", fill_type="solid"),
        font=Font(bold=True, size=16)
    )
    ws.merge_cells(f"A{ws.max_row}:B{ws.max_row}")
    ws.row_dimensions[ws.max_row].height = 25

    ws.append(["Machoz", "Area in dunam Used"])
    style_range(
        ws,
        f"A{ws.max_row}", f"B{ws.max_row}",
        alignment=Alignment(horizontal="center", vertical="center", wrap_text=True),
        fill=PatternFill(start_color="D9D9D9", end_color="D9D9D9", fill_type="solid"),
        font=Font(bold=True, size=14)
    )

    for row in area_used_per_machoz.itertuples(index=False):
        ws.append(row)

    ws.append([])
    ws.append(["Area used per AnafSub"])
    style_range(
        ws,
        f"A{ws.max_row}", f"B{ws.max_row}",
        alignment=Alignment(horizontal="center", vertical="center", wrap_text=True),
        fill=PatternFill(start_color="D9D9D9", end_color="D9D9D9", fill_type="solid"),
        font=Font(bold=True, size=16)
    )
    ws.merge_cells(f"A{ws.max_row}:B{ws.max_row}")
    ws.row_dimensions[ws.max_row].height = 25

    ws.append(["AnafSub", "Area in dunam Used"])
    style_range(
        ws,
        f"A{ws.max_row}", f"B{ws.max_row}",
        alignment=Alignment(horizontal="center", vertical="center", wrap_text=True),
        fill=PatternFill(start_color="D9D9D9", end_color="D9D9D9", fill_type="solid"),
        font=Font(bold=True, size=14)
    )

    for row in area_used_per_anafSub.itertuples(index=False):
        ws.append(row)

    # Adjust alignment for all cells
    for row in ws.iter_rows():
        for cell in row:
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

    # Save the file

    wb.save(final_results_output_path)
    print(f"final results saved to {final_results_output_path}")
    os.startfile(final_results_output_path)

# Helper function to apply styling in output excel results
def style_range(ws, start_cell, end_cell, alignment=None, fill=None, font=None):
    for row in ws[start_cell:end_cell]:
        for cell in row:
            if alignment:
                cell.alignment = alignment
            if fill:
                cell.fill = fill
            if font:
                cell.font = font

