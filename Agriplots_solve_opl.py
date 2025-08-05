import subprocess
import shutil
import pandas as pd
import time
from typing import List, Dict, Optional, Callable, Union, Tuple

from output_opl_results_to_excel import output_opl_results_to_excel
from generate_model_inputs import generate_model_inputs
from utils import measure_time, track_row_changes, load_excel, create_copy_of_mod_file
from data_preprocessing import remove_rows_with_missing_values, remove_rows_with_non_feasible_locations, modify_influence_on_crops, add_installation_costs, assign_different_yeshuv_names, add_eshkolot_to_dataset
from opl_results_parser import raw_output_to_df

def write_dat_file(dat_file, data, params):
    yeshuvim_with_locations = data.pop("yeshuvim_with_locations")
    machozot_with_locations = data.pop("machozot_with_locations")
    eshkolot_with_locations = data.pop("eshkolot_with_locations")
    with open(dat_file, 'w') as f:
        for dict in [params, data]:
            for key, val in dict.items():
                f.write(f"{key} = {val};\n")

        f.write("S = [\n")
        for yeshuv, locations in yeshuvim_with_locations.items():
            f.write(f"{locations},\n")
        f.write("];\n")
        
        f.write("M = [\n")
        for machoz, locations in machozot_with_locations.items():
            f.write(f"{locations},\n")
        f.write("];")

        f.write("E = [\n")
        for eshkol, locations in eshkolot_with_locations.items():
            f.write(f"{locations},\n")
        f.write("];")

@measure_time
def solve_opl_model(mod_file, dat_file, oplrun_path, output_file=None):
    if not shutil.which(oplrun_path):
        print(f"{oplrun_path} not found in PATH. Make sure CPLEX Optimization Studio is installed and oplrun is in the PATH.")
        return

    command = [oplrun_path, mod_file, dat_file]
    try:
        result = subprocess.run(command, capture_output=True, text=True)
        if output_file:
            with open(output_file, 'w') as f:
                if result.returncode == 0:
                    f.write("Solution found:\n")
                    f.write(result.stdout)
                else:
                    f.write("Error in solving the model:\n")
                    f.write("Return code: " + str(result.returncode) + "\n")
                    f.write("Standard Output: " + result.stdout + "\n")
                    f.write("Standard Error: " + result.stderr + "\n")
            print(f"Output saved to {output_file}")
        else:
            if result.returncode == 0:
                print("Solution found:")
                print(result.stdout)
            else:
                print("Error in solving the model:")
                print("Return code:", result.returncode)
                print("Standard Output:", result.stdout)
                print("Standard Error:", result.stderr)
        return result.stdout
    except Exception as e:
        print(f"Error running oplrun: {e}")

def test_model(testing_data_and_parameters_path):
    dataset_path = [testing_data_and_parameters_path, "data"]
    influence_on_crops_synthetic_values_path = [testing_data_and_parameters_path, "Influence on crops"]
    energy_consumption_by_yeshuv_path = [testing_data_and_parameters_path, "energy consumption by yeshuv"]
    energy_consumption_by_machoz_path = [testing_data_and_parameters_path, "energy consumption by machoz"]
    params = load_excel([testing_data_and_parameters_path, "parameters"])
    params.columns = ['Remaining_percentage_of_revenue_after_influence_on_crops_lower_bound', 'total_area_upper_bound', 'G_max']
    # convert params to dict so it will be the same type as the PARAMETERS in the main() function
    params = params.to_dict(orient='records')[0]
    return dataset_path, influence_on_crops_synthetic_values_path, energy_consumption_by_yeshuv_path, energy_consumption_by_machoz_path, params

def set_decision_variable_type(file_path, decision_variables_type):
    """
    Modify a .mod file based on the decision_variables_type argument.

    Args:
        file_path (str): The path to the .mod file.
        decision_variables_type (str): Either "binary decision variables" or "continuous decision variables".

    Raises:
        ValueError: If the decision_variables_type is not valid.
    """
    # Define the mappings for replacement based on decision_variables_type
    replacements = {
        "binary decision variables": (
            "dvar float+ x[1..num_locations]; // float decision variables (0 <= x[i] <= 1)",
            "dvar boolean x[1..num_locations]; // binary (boolean) decision variables"
        ),
        "continuous decision variables": (
            "dvar boolean x[1..num_locations]; // binary (boolean) decision variables",
            "dvar float+ x[1..num_locations]; // float decision variables (0 <= x[i] <= 1)"
        ),
    }

    if decision_variables_type not in replacements:
        raise ValueError("Invalid decision_variables_type. Use 'binary decision variables' or 'continuous decision variables'.")

    # Extract the original and replacement strings
    original_line, replacement_line = replacements[decision_variables_type]

    # Read the file content
    try:
        with open(file_path, 'r') as file:
            lines = file.readlines()
    except FileNotFoundError:
        raise FileNotFoundError(f"The file '{file_path}' does not exist.")

    # Update the file content if the original line exists
    modified = False
    for i, line in enumerate(lines):
        if line.strip() == original_line:
            lines[i] = replacement_line + "\n"
            modified = True
            break

    # Write back to the file if modifications were made
    if modified:
        with open(file_path, 'w') as file:
            file.writelines(lines)
    else:
        print("No matching line found. No changes were made.")

def insert_named_blocks_after_marker(file_path, block_names, block_mapping,  marker_text):
    """
    Inserts named content blocks (e.g., constraints or objective functions) after a marker line in a file.

    Args:
        file_path (str): Path to the .mod file.
        block_names (List[str]): A list of keys to insert from the block_mapping.
        block_mapping (dict): A dictionary mapping block names to their code strings.
        marker_text (str): The exact line of text in the file after which the blocks will be inserted.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the marker_text is not found or block_names contains invalid keys.
    """
    unknown_names = [name for name in block_names if name not in block_mapping]
    if unknown_names:
        raise ValueError(f"Unknown block name(s): {', '.join(unknown_names)}")

    try:
        with open(file_path, 'r') as file:
            lines = file.readlines()
    except FileNotFoundError:
        raise FileNotFoundError(f"The file '{file_path}' does not exist.")

    insertion_index = None
    for i, line in enumerate(lines):
        if marker_text in line:
            insertion_index = i + 1
            break

    if insertion_index is None:
        raise ValueError(f"The marker text '{marker_text}' was not found in the file.")

    # Prepare blocks (with blank lines between)
    inserted_blocks = []
    for name in block_names:
        inserted_blocks.append(block_mapping[name].strip())
        inserted_blocks.append("")

    # Insert blocks into original content
    new_lines = lines[:insertion_index] + [block + "\n" for block in inserted_blocks] + lines[insertion_index:]

    with open(file_path, 'w') as file:
        file.writelines(new_lines)

def set_objective_function(file_path, objective_function, objective_function_mapping):
    marker_text = "// Objective Function"
    insert_named_blocks_after_marker(file_path, objective_function, objective_function_mapping, marker_text)

def set_constraints(file_path, constraints_to_add, constraints_mapping):
    marker_text = "subject to {"
    insert_named_blocks_after_marker(file_path, constraints_to_add, constraints_mapping, marker_text)

def group_by_yeshuv_and_AnafSub(df_):
    key_columns = ['YeshuvName', 'AnafSub']
    columns_to_aggregate_by_sum = ["Dunam","Energy production (fix) mln kWh/year",
        "Potential revenue from crops before PV, mln NIS", "Potential revenue from crops after PV, mln NIS", "Installation cost"]
    columns_to_aggregate_by_first = ["Average influence of PV on crops", "Machoz", "eshkol"]
    relevant_columns_for_model = key_columns + columns_to_aggregate_by_sum + columns_to_aggregate_by_first
    agg_dict = {col: 'sum' for col in columns_to_aggregate_by_sum} # create dict with columns to aggregate by "sum"
    agg_dict.update({col: 'first' for col in columns_to_aggregate_by_first}) #update dict with columns to aggregate by "first"
    df_for_model = df_[relevant_columns_for_model]
    # Perform the groupby and aggregation
    df_for_model = df_for_model.groupby(key_columns).agg(agg_dict).reset_index()
    # df_for_model = df_for_model.groupby(key_columns)[columns_to_aggregate].sum().reset_index()
    print(df_for_model)
    df_for_model.to_excel('grouped_continuous_df.xlsx', index=False)
    return df_for_model

# Custom filter function with "include"/"exclude" option for each column
def filter_dataset(df: pd.DataFrame, filters: Dict[str, Tuple[List[str], str]]) -> pd.DataFrame:
    """
    Filters the dataframe based on multiple column conditions.

    Parameters:
    df (pd.DataFrame): The dataframe to filter.
    filters (Dict[str, Tuple[List[str], str]]): A dictionary where the keys are column names and the values are tuples.
        Each tuple contains a list of values to filter by and a string ("include" or "exclude") indicating the action.

    Returns:
    pd.DataFrame: The filtered dataframe.
    """
    # Initialize the condition to True for all rows
    condition = pd.Series([True] * len(df))
    # Iterate over each column and its filter values
    for column, (values, action) in filters.items():
        if action == "include":
            # Include rows where the column value is in the specified values
            condition &= df[column].isin(values)
        elif action == "exclude":
            # Exclude rows where the column value is in the specified values
            condition &= ~df[column].isin(values)
    # Return the filtered dataframe
    print("condition: ", condition)
    return df[condition]


@measure_time
def main(
    yeshuv_filter=None,
    machoz_filter=None,
    cluster_filter=None,
    crop_filter=None,
    objective_function_type="maximum energy",
    main_constraint="total_area_constraint",
    full_continuous_model=False,
    common_constraints=None,
    parameters=None,
    run_from_ui=False
):
    if not run_from_ui:
        # Set default test/debug values
        # yeshuv_filter = ['אשדוד', 'תרום']
        # machoz_filter = ['South']
        # crop_filter = ['peelables']
        yeshuv_filter = []
        machoz_filter = []
        crop_filter = []
        cluster_filter = []
        objective_function_type = "maximum energy"
        main_constraint = "total_area_constraint"
        full_continuous_model = False
        common_constraints = ["energy_production_per_yeshuv_constraint",
                          "energy_production_per_machoz_constraint",
                          "energy_production_per_eshkol_upper_bounding_constraint",
                          "energy_production_per_eshkol_lower_bounding_constraint"]
        parameters = {
            "total_energy_lower_bound": 80.00,
            "total_area_upper_bound": 20000.00,
            "Remaining_percentage_of_revenue_after_influence_on_crops_lower_bound": 0.92,
            "total_installation_cost_upper_bound": 120000.00
        }

    OPLRUN_PATH = r"C:\Program Files\IBM\ILOG\CPLEX_Studio1210\opl\bin\x64_win64\oplrun.exe"
    # OPLRUN_PATH = r"C:\Program Files\IBM\ILOG\CPLEX_Studio201\opl\bin\x64_win64\oplrun.exe"
    DEBUG = False # If true, take a slice out of the dataset for testing pueposes
    ROWS_FOR_DEBUG = 1000
    SANITY_CHECKS = False
    DECISION_VARIABLES_TYPE = "binary decision variables" # can either be "binary decision variables" or "continuous decision variables"
    OBJECTIVE_FUNCTION_TYPE = objective_function_type # can either be "maximum energy", "minimum area", "maximum remaining percentage of revenue" or "minimum installation cost"
    MAIN_CONSTRAINTS = [main_constraint]
    FULL_CONTINUOUS_MODEL = full_continuous_model
    
    
    GINI_IN_OBJECTIVE = False
    GINI_IN_CONSTRAINT = False
    
             
    COMMON_CONSTRAINTS = common_constraints + ["decision_variables_constraint"]
    model_constraints = MAIN_CONSTRAINTS + COMMON_CONSTRAINTS  

    # parameters of the model
    PARAMETERS = parameters
    
    # filters = {
    #     'YeshuvName': (['אשדוד', 'תרום'], "exclude"),  # Include 'אשדוד' and 'אשקלון'
    #     'Machoz': (['South'], "exclude"),   # Exclude 'North' and 'Center'
    #     "AnafSub": (['peelables'], "exclude")
    # }

    filters = {}
    if yeshuv_filter:
        filters["YeshuvName"] = (yeshuv_filter, "include")
    if machoz_filter:
        filters["Machoz"] = (machoz_filter, "include")
    if crop_filter:
        filters["AnafSub"] = (crop_filter, "include")
    # Add cluster filter if relevant to your dataset



    objective_function_mapping = {
        "maximum energy": "maximize TotalEnergy;",
        "minimum area": "minimize TotalArea;",
        "maximum remaining percentage of revenue": "maximize RemainingPercentageOfRevenue;",
        "minimum installation cost": "minimize TotalInstallationCost;",
        "maximum energy & maximum equity with gini": (
            "// Multi-Objective: Maximize energy & equity\n"
            "maximize TotalEnergy - G_numerator;"
        )
    }

    constraints_mapping = {
        "total_energy_constraint": (
            "    //Constraint for a lower bound of the total energy produced by installed PV's\n"
            "    TotalEnergy >= total_energy_lower_bound;"
        ),
        "total_area_constraint": (
            "    // Constraint for an upper bound of the total area used by installed PV's\n"
            "    TotalArea <= total_area_upper_bound;"
        ),
        "remaining_percentage_of_revenue_constraint": (
            "    // Constraint for the remaining percentage of original revenue, as a result of installing the PV's and influencing the crops, lower bounded by an inputed threshold \n"
            "    RemainingPercentageOfRevenue >= Remaining_percentage_of_revenue_after_influence_on_crops_lower_bound;"
        ),
        "total_installation_cost_constraint": (
            "    // Constraint for an upper bound of the total installation cost of PV's\n"
            "    TotalInstallationCost <= total_installation_cost_upper_bound;"
        ),
        "energy_production_per_yeshuv_constraint": (
            "    // Constraint for the total energy production of each yeshuv, upper bounded by the energy consumption of each yeshuv \n"
            "    forall (j in Yeshuvim) {\n"
            "        sum(i in S[j]) x[i] * fix_energy_production[i] <= energy_consumption_by_yeshuv[j];\n"
            "    };"
        ),
        "energy_production_per_machoz_constraint": (
            "    // Constraint for the total energy production of each machoz, upper bounded by the energy consumption of each machoz \n"
            "    forall (j in Machozot) {\n"
            "        sum(i in M[j]) x[i] * fix_energy_production[i] <= energy_consumption_by_machoz[j];\n"
            "    };"
        ),
        "energy_production_per_eshkol_upper_bounding_constraint": (
            "    // Constraint for the percentage of the total energy production of each eshkol, upper bounded by some fixed percentage \n"
            "    forall (k in Eshkolot) {\n"
            "        y[k] <= energy_upper_bounds_for_eshkolot[k] * sum(i in 1..num_locations) (fix_energy_production[i] * x[i]);\n"
            "    };"
        ),
        "energy_production_per_eshkol_lower_bounding_constraint": (
            "    // Constraint for the percentage of the total energy production of each eshkol, lower bounded by some fixed percentage \n"
            "    forall (k in Eshkolot) {\n"
            "        y[k] >= energy_lower_bounds_for_eshkolot[k] * sum(i in 1..num_locations) (fix_energy_production[i] * x[i]);\n"
            "    };"
        ),
        "decision_variables_constraint": (
            "    // Constraint that limits the value of x[i] to be less or equal than 1, relevant for the continuous model \n"
            "    forall(i in 1..num_locations)\n"
            "        x[i] <= 1;\n"
        ),
        "linearized_constraint_for_gini": (
            "    // Linearized Gini coefficient constraint (only for i < j)\n"
            "    forall(i in Eshkolot, j in Eshkolot: i < j) {\n"
            "        z[i][j] >=  energy_division_between_eshkolot[j]*y[j] - energy_division_between_eshkolot[i]*y[i];\n"
            "        z[i][j] >=  energy_division_between_eshkolot[i]*y[i] - energy_division_between_eshkolot[j]*y[j];\n"
            "    };"
        ),
        "gini_constraint": (
            "    // Gini constraint (now summing only over i < j)\n"
            "    G_numerator <= G_max * TotalEnergy;\n"
        ),

    }
    


    # File paths
    opl_model_file, dat_file, txt_output_path = 'Agriplots.mod', 'Agriplots.dat', 'output.txt'
    
    opl_base_model_file_path = "models/Agriplots_base_model.mod"
    create_copy_of_mod_file(opl_base_model_file_path, opl_model_file)

    dataset_path = 'Agriplots_final - Full data - including missing rows.xlsx'
    dataset_path = 'datasets_for_testing/Agriplots dataset - 1,000 rows.xlsx'
    # dataset_path = 'ssssdddd.xlsx'
    # dataset_path = "agrivoltaics_fix_4.7.25- main data.xlsx"
    anaf_sub_parameters_synthetic_values_path = 'Anaf sub parameters - synthetic values.xlsx'
    energy_consumption_by_yeshuv_path = 'energy_consumption_by_yeshuv.xlsx'
    energy_consumption_by_machoz_path = ['energy_consumption_by_machoz_aggregated_from_yeshuvim.xlsx', 'energy consumption by machoz']
    assignment_of_missing_yeshuv_names_path = 'assignment_of_missing_yeshuv_names.xlsx'
    yeshuvim_in_eshkolot_path = 'yeshuvim_in_eshkolot.xlsx'
    energy_division_between_eshkolot_path = 'energy_division_between_eshkolot-synthetic_values.xlsx'
    energy_division_between_eshkolot_path = 'energy_division_between_eshkolot-synthetic_values - try 2.xlsx'
    energy_lower_bounds_for_eshkolot_path = ['energy_lower_and_upper_bounds_for_eshkolot.xlsx', 'lower_bounds']
    energy_upper_bounds_for_eshkolot_path = ['energy_lower_and_upper_bounds_for_eshkolot.xlsx', 'upper_bounds']
    installation_decisions_output_path = 'installation_decisions_results.xlsx'
    final_results_output_path = 'final_results.xlsx'
    testing_data_and_parameters_path = 'datasets_for_testing/sanity_checks_datasets/sanity_check_1-choosing_based_on_area_constraint.xlsx'
    
    if SANITY_CHECKS:
        dataset_path, anaf_sub_parameters_synthetic_values_path, energy_consumption_by_yeshuv_path, energy_consumption_by_machoz_path, PARAMETERS = test_model(testing_data_and_parameters_path)
    load_df_dataset_start_time = time.time()
    if DEBUG:
        df_dataset = load_excel(dataset_path, ROWS_FOR_DEBUG) # Read a fraction of dataset from Excel
    else:
        df_dataset = load_excel(dataset_path) # Read full dataset from Excel
    elapsed_time = time.time() - load_df_dataset_start_time
    print(f"loading df_dataset took {elapsed_time:.2f} seconds")
    print("number of rows in full dataset :", len(df_dataset))
    print("number of yeshuvim before removing rows from dataset:",df_dataset["YeshuvName"].nunique())
    


    if dataset_path == "agrivoltaics_fix_4.7.25- main data.xlsx":
        col_names_replacements =  {
            "GeomachozName":"Machoz",
            "AnafSubENG":"AnafSub",
            "Feasability_to_install_PVs":"Feasability to install PVs?",
            "EPFix_MkWh":"Energy production (fix) mln kWh/year",
            "Average_influence_of_PV_on_crops": "Average influence of PV on crops",
            "Potential_revenue_from_crops_before_PV_MNIS":"Potential revenue from crops before PV, mln NIS",
            "Potential_revenue_from_crops_after_PV_MNIS":"Potential revenue from crops after PV, mln NIS",
        }
        df_dataset = df_dataset.drop(["AnafSub"], axis=1)
        df_dataset.rename(columns = col_names_replacements, inplace = True)

        import random
        machozot_list = ["Center", "Haifa", "Jerusalem", "North", "South", "Tel Aviv"]
        # Create random mahcozot column
        random_machozot = random.choices(machozot_list, k=df_dataset.shape[0])
        df_dataset["Machoz"] = random_machozot

    
    # filter dataset based on different columns
    df_dataset = filter_dataset(df_dataset, filters)
    # save potential revenue of full dataset before installations to be used in the model later on
    total_potential_revenue_before_PV_of_full_dataset = df_dataset["Potential revenue from crops before PV, mln NIS"].sum() 
    df_dataset = remove_rows_with_missing_values(df_dataset)
    df_dataset = remove_rows_with_non_feasible_locations(df_dataset)
    print("number of yeshuvim after removing some rows from dataset:",df_dataset["YeshuvName"].nunique())
    # modify influence on crops column based on synthetic values
    df_dataset = modify_influence_on_crops(df_dataset, anaf_sub_parameters_synthetic_values_path)
    # add installation costs of PV column based on costs of crops per dunam and area in dunam
    df_dataset = add_installation_costs(df_dataset, anaf_sub_parameters_synthetic_values_path)
    # import energy consumptions by yeshuv and by machoz 
    energy_consumption_by_yeshuv = load_excel(energy_consumption_by_yeshuv_path)
    energy_consumption_by_machoz = load_excel(energy_consumption_by_machoz_path)
    # assign different names for some yeshuvim in dataset to match energy_consumption_by_yeshuv and yeshuvim_in_eshkolot dataframes
    df_dataset = assign_different_yeshuv_names(df_dataset, assignment_of_missing_yeshuv_names_path)
    # import datasets relevant for using eshkolot in the model
    yeshuvim_in_eshkolot = load_excel(yeshuvim_in_eshkolot_path)
    yeshuvim_in_eshkolot.rename(columns = {'eshkol_2021':'eshkol'}, inplace = True) # rename column in the df
    energy_division_between_eshkolot = None # value will be given if Gini is used
    energy_lower_bounds_for_eshkolot = load_excel(energy_lower_bounds_for_eshkolot_path)
    energy_upper_bounds_for_eshkolot = load_excel(energy_upper_bounds_for_eshkolot_path)
    # add eshkolot to dataset based on yeshuvim_in_eshkolot, and also remove rows that their yeshuv doesn't have an eshkol
    df_dataset = add_eshkolot_to_dataset(df_dataset, yeshuvim_in_eshkolot)
    print("number of yeshuvim after adding eshkolot:",df_dataset["YeshuvName"].nunique())
    
    if FULL_CONTINUOUS_MODEL:
        DECISION_VARIABLES_TYPE = "continuous decision variables" #forces continuous decision variables for full continuous model
        continuous_model_df = group_by_yeshuv_and_AnafSub(df_dataset)
        df_dataset = continuous_model_df
    
    if GINI_IN_OBJECTIVE:
        PARAMETERS["G_max"] = 1.00 # meaning there is no constraint, since Gini can't be more than 1
        OBJECTIVE_FUNCTION_TYPE = "maximum energy & maximum equity with gini"
        energy_division_between_eshkolot = load_excel(energy_division_between_eshkolot_path)
    
    if GINI_IN_CONSTRAINT:
        PARAMETERS["G_max"] = 0.05 # constraint Gini coefficient to be no more than 0.05
        model_constraints.extend(["linearized_constraint_for_gini", "gini_constraint"])
        energy_division_between_eshkolot = load_excel(energy_division_between_eshkolot_path)

    # create location_id column in df_dataset that's based on index of the df
    df_dataset = df_dataset.reset_index() # reset index of the df before creating the new column, since rows were removed earlier
    df_dataset["location_id"] = df_dataset.index + 1
    df_dataset.to_excel('df_dataset before data preparation.xlsx', index=False)
    # get needed relevant data for running the model, in addition to the parameters (PARAMETERS)
    data = generate_model_inputs(df_dataset, energy_consumption_by_yeshuv, energy_lower_bounds_for_eshkolot, energy_upper_bounds_for_eshkolot, energy_consumption_by_machoz, total_potential_revenue_before_PV_of_full_dataset, energy_division_between_eshkolot)
    # write data and PARAMETERS to .dat file
    write_dat_file(dat_file, data, PARAMETERS)
    # set decision variables, objective function and constraints based chosen model
    set_decision_variable_type(opl_model_file, DECISION_VARIABLES_TYPE)
    set_objective_function(opl_model_file, [OBJECTIVE_FUNCTION_TYPE], objective_function_mapping)
    set_constraints(opl_model_file, model_constraints, constraints_mapping)
    # solve the OPL model and put the opl output in the opl_raw_output variable
    opl_raw_output = solve_opl_model(opl_model_file, dat_file, OPLRUN_PATH, txt_output_path)
    print("opl_raw_output:\n", opl_raw_output)
    # converting the raw output of the model to a dataframe with the needed results
    df_results = raw_output_to_df(opl_raw_output)
    # output the final results to excel file
    output_opl_results_to_excel(df_dataset, df_results, PARAMETERS, installation_decisions_output_path, final_results_output_path, DECISION_VARIABLES_TYPE, OBJECTIVE_FUNCTION_TYPE, MAIN_CONSTRAINTS[0])
    # resutls_for_GIS = get_results_for_GIS_tool(df_dataset, df_results, "results_for_GIS_temp.xlsx")
    # return resutls_for_GIS


def get_results_for_GIS_tool(df_dataset_, df_results_, export_temp_path_):
    main_results_df, installed_PVs_results, _ = df_results_
    relevant_columns_from_input = ["location_id", "OBJECTID", "YeshuvName", "Machoz", "AnafName", "CoverTypeE", "Energy production (tracking) mln kWh/year"]
    if "OBJECTID" not in list(df_dataset_.columns):
        relevant_columns_from_input.remove("OBJECTID")
    relevant_df_from_input = df_dataset_[relevant_columns_from_input]
    # convert "OBJECTID" and "Location" column to int, so the merge will be successful
    if "OBJECTID" in list(df_dataset_.columns):
        relevant_df_from_input['OBJECTID'] = relevant_df_from_input['OBJECTID'].astype('int')
    installed_PVs_results['location_id'] = installed_PVs_results['location_id'].astype('int')
    # convert "area in dunam used" column to numeric
    installed_PVs_results["area in dunam used"] = pd.to_numeric(installed_PVs_results["area in dunam used"], errors="coerce")
    # left join installed locations from result of opl model to columns from input dataset
    merged_data = pd.merge(relevant_df_from_input,installed_PVs_results, on="location_id", how="left")
    merged_data['x[i]'] = merged_data['x[i]'].apply(lambda x: 0 if pd.isna(x) else 1)
    merged_data['Energy units Produced in mln'] = merged_data['Energy units Produced in mln'].apply(lambda x: 0 if pd.isna(x) else float(x))
    merged_data['area in dunam used'] = merged_data['area in dunam used'].apply(lambda x: 0 if pd.isna(x) else float(x))
    merged_data = merged_data.rename(columns={
        'OBJECTID': 'plot_id',
        'YeshuvName': 'yeshuv',
        'Machoz': 'machoz',
        'AnafName': 'crop_type',
        'CoverTypeE': 'covertype',
        'x[i]': 'pv_installed',
        'Energy units Produced in mln': 'prodfix',
        'Energy production (tracking) mln kWh/year': 'prodtrack',
        'area in dunam used': 'dunam'
        })
    
    merged_data['color'] = merged_data['pv_installed'].apply(lambda x: '#008000' if x == 1 else '#FF0000')
    merged_data['economic_impact_nis'] = merged_data['pv_installed'].apply(lambda x: 50000 if x == 1 else 0)
    merged_data['selected'] = 1.00
    merged_data['longitude'] = 0.00
    merged_data['latitude'] = 0.00

    merged_data.loc[merged_data['pv_installed'] == 0, 'prodtrack'] = 0

    merged_data = merged_data.drop(columns=['location_id', 'influence on crops'])



    print(merged_data)
    # exporting results to excel
    print("main_results_df:\n", main_results_df)
    merged_data.to_excel(export_temp_path_)
    print(f"results for GIS saved to {export_temp_path_}")

    main_results_df = main_results_df[["Total energy produced in mln", "Total area (in dunam) used"]]
    main_results_df.columns = ["total_energy_mwh", "total_area_used_dunam"]

    return merged_data, main_results_df


# if __name__ == "__main__":
#     main()
    # pass
    # resutls_for_GIS = main()

if __name__ == "__main__":
    main(run_from_ui=False)