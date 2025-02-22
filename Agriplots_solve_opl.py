import subprocess
import shutil
import pandas as pd
import time
from typing import List, Dict, Optional, Callable, Union

from choosing_parameters_interface import activate_interface
from remove_constraints_from_model import remove_constraints_from_model
from output_opl_results_to_excel import output_opl_results_to_excel
from prepare_data_for_model import prepare_data_for_model
from utils import measure_time, track_row_changes

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
def solve_opl_model(mod_file, dat_file, output_file=None):
    oplrun_path = "oplrun"
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

def modify_influence_on_crops(df_, influence_on_crops_synthetic_values_path):
    influence_on_crops_data = load_excel(influence_on_crops_synthetic_values_path)
    # prepare dictionary that maps for each crop how much it's influenced by installing PV
    influence_on_crops_dict = influence_on_crops_data.set_index("AnafSub")["Average influence"].to_dict()
    # maps average influence on crops to each AnafSub according to the influence_on_crops_dict (like Vlookp)
    modified_influence_on_crops = df_['AnafSub'].map(influence_on_crops_dict).tolist()
    df_["Average influence of PV on crops"] = modified_influence_on_crops
    return df_

@track_row_changes
def remove_rows_with_missing_values(df_):
    # remove rows with nan values (Ideally should find a better way to handle those nan values later on)
    df_ = df_.dropna(subset=['Energy production (fix) mln kWh/year',
                           'Dunam'])
    return df_

@track_row_changes
def remove_rows_with_non_feasible_locations(df_):
    # remove rows with non feasible locations for installing PV's
    df_ = df_[df_['Feasability to install PVs?'] != 0]
    return df_

@measure_time
@track_row_changes
def add_eshkolot_to_dataset(df_, yeshuvim_in_eshkolot_):
    # Perform a left join to add the 'eshkol' column from yeshuvim_in_eshkolot_ to df_
    df_ = pd.merge(df_, yeshuvim_in_eshkolot_, on='YeshuvName', how='left')
    # Fill missing values (if a YeshuvName is not found in yeshuvim_in_eshkolot_, set 'eshkol' to -1)
    df_['eshkol'].fillna(-1, inplace=True)
    # Optionally, convert 'eshkol' to integer if needed
    df_['eshkol'] = df_['eshkol'].astype(int)
    df_[df_['eshkol'] == -1].to_excel("removed rows from df_dataset after adding eshkolot.xlsx")
    #remove rows that has eshkol -1, meaning rows that their yeshuv doesn't have an eshkol
    df_ = df_[df_['eshkol'] != -1]
    return df_

def raw_output_to_df(opl_raw_output_):
    # parsing the result output to extract the required values
    main_results = pd.DataFrame()
    locations_with_installed_PVs = ""  # Variable to store multiple lines of output
    energy_produced_per_eshkol = ""  # Variable to store multiple lines of output
    capture_main_results = False
    capture_locations_with_installed_PVs_results = False  # Flag to start capturing excel output
    capture_energy_produced_per_eshkol_results = False  # Flag to start capturing excel output
    for line in opl_raw_output_.splitlines():
        # Detect the start of the excel output block
        if "Results for excel output file:" in line:
            capture_main_results = True  # Start capturing from the next line
            continue  # Skip the current line
        if "Locations with installed PV's:" in line:
            capture_main_results = False
            capture_locations_with_installed_PVs_results = True
            continue
        if capture_main_results:
            if line.strip() == "Locations with installed PV's:":  # Stop capturing when we hit an empty line (or define another end condition)
                capture_locations_with_installed_PVs_results = False
                capture_energy_produced_per_eshkol_results = True
                continue
            splitted_line = line.strip().split(": ")
            metric, value = splitted_line 
            main_results[metric] = [value]
        
        if capture_locations_with_installed_PVs_results:
            if line.strip() == "Energy produced per Eshkol:":  # Stop capturing when we hit an empty line (or define another end condition)
                capture_locations_with_installed_PVs_results = False
                capture_energy_produced_per_eshkol_results = True
                continue
            locations_with_installed_PVs += line + "\n"  # Append the line to the result string

        # Capture subsequent lines after the keyword is detected
        if capture_energy_produced_per_eshkol_results:
            # print("in fourth condition")
            if line.strip() == "End of Results for excel output file":  # Stop capturing when we hit an empty line (or define another end condition)
                break
            energy_produced_per_eshkol += line + "\n"  # Append the line to the result string

    locations_with_installed_PVs = locations_with_installed_PVs.strip()
    locations_with_installed_PVs = locations_with_installed_PVs.split("\n")  # Splitting at the \n delimiter

    energy_produced_per_eshkol = energy_produced_per_eshkol.strip()
    energy_produced_per_eshkol = energy_produced_per_eshkol.split("\n")  # Splitting at the \n delimiter

    locations_with_installed_PVs_results = model_results_to_df(locations_with_installed_PVs)
    energy_produced_per_eshkol_results = model_results_to_df(energy_produced_per_eshkol)
    df_results = [main_results, locations_with_installed_PVs_results, energy_produced_per_eshkol_results]
    # Return the captured results, including the excel output block
    return df_results

def model_results_to_df(excel_output_results):
    # Split the first element to get the column names
    column_names = excel_output_results[0].split(',')
    # Split each remaining element in the list to get the data rows
    rows = [row.split(',') for row in excel_output_results[1:]]
    # Create a pandas DataFrame using the rows and columns
    df_results = pd.DataFrame(rows, columns = column_names)
    return df_results

def assign_different_yeshuv_names(df_, new_yeshuv_names_path):
    new_yeshuv_names = load_excel(new_yeshuv_names_path)
    # Create a mapping from the assignment_of_missing_yeshuv_names DataFrame
    yeshuv_name_mapping = dict(zip(new_yeshuv_names['old_yeshuv_name'], new_yeshuv_names['new_yeshuv_name']))
    # Apply the mapping to the dataset
    df_['YeshuvName'] = df_['YeshuvName'].replace(yeshuv_name_mapping)
    df_['YeshuvName'].to_excel("yeshuvim in df_dataset after assigning different yeshuv names.xlsx")
    print("number of yeshuvim after assigning different names to yeshuvim:",df_["YeshuvName"].nunique())
    return df_

def load_excel(dataset_path_):
    # if dataset_path_ is a list that includes sheet_name, read excel using sheet name
    if isinstance(dataset_path_, list):
        loaded_dataset = pd.read_excel(dataset_path_[0], sheet_name = dataset_path_[1])
    # otherwise, just use the file path to read the excel
    else:
        loaded_dataset = pd.read_excel(dataset_path_)
    return loaded_dataset

def test_model(testing_data_and_parameters_path):
    dataset_path = [testing_data_and_parameters_path, "data"]
    influence_on_crops_synthetic_values_path = [testing_data_and_parameters_path, "Influence on crops"]
    energy_consumption_by_yeshuv_path = [testing_data_and_parameters_path, "energy consumption by yeshuv"]
    energy_consumption_by_machoz_path = [testing_data_and_parameters_path, "energy consumption by machoz"]
    params = load_excel([testing_data_and_parameters_path, "parameters"])
    params.columns = ['allowed_loss_from_influence_on_crops_percentage', 'total_area_upper_bound', 'G_max']
    # convert params to dict so it will be the same type as the params in the main() function
    params = params.to_dict(orient='records')[0]
    return dataset_path, influence_on_crops_synthetic_values_path, energy_consumption_by_yeshuv_path, energy_consumption_by_machoz_path, params

def set_decision_variable_type(file_path, model_type):
    """
    Modify a .mod file based on the model_type argument.

    Args:
        file_path (str): The path to the .mod file.
        model_type (str): Either "binary decision variables" or "continuous decision variables".

    Raises:
        ValueError: If the model_type is not valid.
    """
    # Define the mappings for replacement based on model_type
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

    if model_type not in replacements:
        raise ValueError("Invalid model_type. Use 'binary decision variables' or 'continuous decision variables'.")

    # Extract the original and replacement strings
    original_line, replacement_line = replacements[model_type]

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



@measure_time
def main():
    USER_INTERFACE = False
    TESTING_MODE = False
    MODEL_TYPE = "binary decision variables" # can either be "binary decision variables" or "continuous decision variables"
    GINI_IN_OBJECTIVE_FUNCTION = True
    # File paths
    opl_model_file, dat_file, txt_output_path = 'Agriplots.mod', 'Agriplots.dat', 'output.txt'
    if GINI_IN_OBJECTIVE_FUNCTION:
        opl_model_file = 'Agriplots_Gini_in_objective.mod'
    # opl_model_file = 'Agriplots_Gini_in_objective.mod' #Gini in Objective
    dataset_path = 'Agriplots_final - Full data.xlsx'
    dataset_path = 'Agriplots_final - Full data - including missing rows.xlsx'
    # dataset_path = 'Agriplots dataset - 1,000 rows.xlsx'
    influence_on_crops_synthetic_values_path = 'Average influence of PV on crops - synthetic values.xlsx'
    energy_consumption_by_yeshuv_path = 'energy_consumption_by_yeshuv.xlsx'
    energy_consumption_by_machoz_path = ["energy_consumption_by_machoz_aggregated_from_yeshuvim.xlsx", "energy consumption by machoz"]
    assignment_of_missing_yeshuv_names_path = 'assignment_of_missing_yeshuv_names.xlsx'
    assignment_of_missing_yeshuv_names_path = 'assignment_of_missing_yeshuv_names_mali.xlsx'
    yeshuvim_in_eshkolot_path = 'yeshuvim_in_eshkolot.xlsx'
    energy_division_between_eshkolot_path = 'energy_division_between_eshkolot-synthetic_values.xlsx'
    installation_decisions_output_path = 'installation_decisions_results.xlsx'
    final_results_output_path = 'final_results.xlsx'
    # testing_data_and_parameters_path = 'model_testing_data_and_parameters.xlsx'
    testing_data_and_parameters_path = 'sanity_check_8-infeasibility_due_to_machoz_constraint.xlsx'
    # parameters of the model
    params = {
        "allowed_loss_from_influence_on_crops_percentage": 0.9,
        "total_area_upper_bound": 30000.00,
        "G_max" : 0.05
        # "G_max" : 0.075100193
    }

    if TESTING_MODE:
        dataset_path, influence_on_crops_synthetic_values_path, energy_consumption_by_yeshuv_path, energy_consumption_by_machoz_path, params = test_model(testing_data_and_parameters_path)
    load_df_dataset_start_time = time.time()
    df_dataset = load_excel(dataset_path) # Read dataset from Excel
    elapsed_time = time.time() - load_df_dataset_start_time
    print(f"loading df_dataset took {elapsed_time:.2f} seconds")
    print("number of rows in full dataset :", len(df_dataset))
    print("number of yeshuvim before removing rows from dataset:",df_dataset["YeshuvName"].nunique())
    total_potential_revenue_before_PV_of_full_dataset = df_dataset["Potential revenue from crops before PV, mln NIS"].sum() #parameter to pass later on
    df_dataset = remove_rows_with_missing_values(df_dataset)
    df_dataset = remove_rows_with_non_feasible_locations(df_dataset)
    print("number of yeshuvim after removing some rows from dataset:",df_dataset["YeshuvName"].nunique())
    # modify influence on crops column based on synthetic values
    df_dataset = modify_influence_on_crops(df_dataset, influence_on_crops_synthetic_values_path)
    # import energy consumptions by yeshuv and by machoz 
    energy_consumption_by_yeshuv = load_excel(energy_consumption_by_yeshuv_path)
    energy_consumption_by_machoz = load_excel(energy_consumption_by_machoz_path)
    # assign different names for some yeshuvim in dataset to match energy_consumption_by_yeshuv and yeshuvim_in_eshkolot dataframes
    df_dataset = assign_different_yeshuv_names(df_dataset, assignment_of_missing_yeshuv_names_path)
    # import datasets relevant for using eshkolot in the model
    yeshuvim_in_eshkolot = load_excel(yeshuvim_in_eshkolot_path)
    yeshuvim_in_eshkolot.rename(columns = {'eshkol_2021':'eshkol'}, inplace = True) # rename column in the df
    energy_division_between_eshkolot = load_excel(energy_division_between_eshkolot_path)
    # add eshkolot to dataset based on yeshuvim_in_eshkolot, and also remove rows that their yeshuv doesn't have an eshkol
    df_dataset["YeshuvName"].to_excel("yeshuvim_before_adding_eshkolot.xlsx")
    df_dataset = add_eshkolot_to_dataset(df_dataset, yeshuvim_in_eshkolot)
    df_dataset["YeshuvName"].to_excel("yeshuvim_after_adding_eshkolot.xlsx")
    print("number of yeshuvim after adding eshkolot:",df_dataset["YeshuvName"].nunique())
    # create location_id column in df_dataset that's based on index of the df
    df_dataset = df_dataset.reset_index() # reset index of the df before creating the new column, since rows were removed earlier
    df_dataset["location_id"] = df_dataset.index + 1
    
    if USER_INTERFACE:
        user_input_params = activate_interface()
        trillion = 1e12 # float form of trillion that's also compatible with .mod and .dat files
        if user_input_params[0]:
            params["total_area_upper_bound"] = user_input_params[0]
        else:
            params["total_area_upper_bound"] = trillion # simulating infinity to show it won't be used in the model
        params["allowed_loss_from_influence_on_crops_percentage"] = user_input_params[1]/100
        
        removed_constraints = user_input_params[2]
        template_file_path = "edit_mod_file/template.mod"
        edited_file_path = "edit_mod_file/edited.mod"
        constraints_to_comment_texts = {
            "total_area_constraint" : "Constraint for an upper bound of the total area used by installed PV's",
            "revenue_change_constraint" : "Constraint for the revenue change in percentage as a result of installing the PV's and influencing the crops, lower bounded by an inputed threshold",
            "energy_production_per_yeshuv_constraint" : "Constraint for the total energy production of each yeshuv, upper bounded by the energy consumption of each yeshuv",
            "energy_production_per_machoz_constraint" : "Constraint for the total energy production of each machoz, upper bounded by the energy consumption of each machoz",
            "name_space_gini_constraint1": "Linearized Gini coefficient constraint (only for i < j)",
            "name_space_gini_constraint2": "Gini constraint (now summing only over i < j)",
        }
        remove_constraints_from_model(removed_constraints, template_file_path, edited_file_path, constraints_to_comment_texts)
        time.sleep(10)
        opl_model_file = edited_file_path

    # get needed relevant data for running the model, in addition to the parameters (params)
    data = prepare_data_for_model(df_dataset, energy_consumption_by_yeshuv, energy_division_between_eshkolot, energy_consumption_by_machoz, total_potential_revenue_before_PV_of_full_dataset)
    # write data and params to .dat file
    write_dat_file(dat_file, data, params)

    set_decision_variable_type(opl_model_file, MODEL_TYPE)
    # Solve the OPL model and put the opl output in the opl_raw_output variable
    opl_raw_output = solve_opl_model(opl_model_file, dat_file, txt_output_path)
    # converting the raw output of the model to a dataframe with the needed results
    df_results = raw_output_to_df(opl_raw_output)
    # output the final results to excel file
    output_opl_results_to_excel(df_dataset, df_results, params, installation_decisions_output_path, final_results_output_path, MODEL_TYPE, GINI_IN_OBJECTIVE_FUNCTION)

if __name__ == "__main__":
    main()
