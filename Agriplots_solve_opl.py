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
    print("column_names: ", column_names)
    # Split each remaining element in the list to get the data rows
    rows = [row.split(',') for row in excel_output_results[1:]]
    # Create a pandas DataFrame using the rows and columns
    df_results = pd.DataFrame(rows, columns = column_names)
    return df_results

def assign_different_yeshuv_names(df_, new_yeshuv_names_path):
    new_yeshuv_names = load_excel(new_yeshuv_names_path)
    print(len(new_yeshuv_names))
    # Create a mapping from the assignment_of_missing_yeshuv_names DataFrame
    yeshuv_name_mapping = dict(zip(new_yeshuv_names['old_yeshuv_name'], new_yeshuv_names['new_yeshuv_name']))
    # Apply the mapping to the dataset
    df_['YeshuvName'] = df_['YeshuvName'].replace(yeshuv_name_mapping)
    # df_['YeshuvName'].to_excel("yeshuvim in df_dataset after assigning different yeshuv names.xlsx")
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

def set_objective_function_type(file_path, objective_function_type):
    """
    Modify the objective function in the .mod file based on the value of objective_function_type.

    Args:
        file_path (str): Path to the .mod file.
        objective_function_type (str): Either "single objective" or "multi objective".

    Raises:
        FileNotFoundError: If the file does not exist.
    """

    # Define the mappings for replacement based on objective_function_type
    replacements = {
        "single objective": (
            "// Multi-Objective Function - Maximizing both total energy produced and equity between eshkolot, using the formula:\n"
            "// TotalEnergy*(1-G) = TotalEnergy*[1-(G_numerator/TotalEnergy)] = TotalEnergy - G_numerator\n"
            "maximize TotalEnergy - G_numerator;",
            "// Objective Function\nmaximize TotalEnergy;"
        ),
        "multi objective": (
            "// Objective Function\nmaximize TotalEnergy;",
            "// Multi-Objective Function - Maximizing both total energy produced and equity between eshkolot, using the formula:\n"
            "// TotalEnergy*(1-G) = TotalEnergy*[1-(G_numerator/TotalEnergy)] = TotalEnergy - G_numerator\n"
            "maximize TotalEnergy - G_numerator;"
        )
    }

    # Extract the original and replacement strings
    original_text, replacement_text = replacements[objective_function_type]

    # Read the file content
    try:
        with open(file_path, 'r') as file:
            content = file.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"The file '{file_path}' does not exist.")

    # Update the file content if the original text exists
    if original_text in content:
        content = content.replace(original_text, replacement_text)
        with open(file_path, 'w') as file:
            file.write(content)
    else:
        print("No matching objective function found. No changes were made.")




def group_by_yeshuv_and_AnafSub(df_):
    key_columns = ['YeshuvName', 'AnafSub']
    columns_to_aggregate_by_sum = ["Dunam","Energy production (fix) mln kWh/year",
        "Potential revenue from crops before PV, mln NIS", "Potential revenue from crops after PV, mln NIS"]
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

def create_copy_of_mod_file(original_file_path, new_file_path):
    # Creates a copy of file that's in original_file_path,
    # that will be located in new_file_path
    shutil.copy(original_file_path, new_file_path)


@measure_time
def main():
    USER_INTERFACE = False
    TESTING_MODE = False
    OBJECTIVE_FUNCTION_TYPE = "multi objective" # can either be "single objective" or "multi objective"
    DECISION_VARIABLES_TYPE = "continuous decision variables" # can either be "binary decision variables" or "continuous decision variables"
    FULL_CONTINUOUS_MODEL = False

    constraints_to_comment_texts = {
            "total_area_constraint" : "Constraint for an upper bound of the total area used by installed PV's",
            "revenue_change_constraint" : "Constraint for the revenue change in percentage as a result of installing the PV's and influencing the crops, lower bounded by an inputed threshold",
            "energy_production_per_yeshuv_constraint" : "Constraint for the total energy production of each yeshuv, upper bounded by the energy consumption of each yeshuv",
            "energy_production_per_machoz_constraint" : "Constraint for the total energy production of each machoz, upper bounded by the energy consumption of each machoz",
            "name_space_gini_constraint1": "Linearized Gini coefficient constraint (only for i < j)",
            "name_space_gini_constraint2": "Gini constraint (now summing only over i < j)",
        }
    
    # File paths
    opl_model_file, dat_file, txt_output_path = 'Agriplots.mod', 'Agriplots.dat', 'output.txt'
    
    opl_base_model_file_path = "edit_mod_file/Agriplots_base_model.mod"
    create_copy_of_mod_file(opl_base_model_file_path, opl_model_file)

    removed_constraints = []
    if OBJECTIVE_FUNCTION_TYPE == "multi objective":
        removed_constraints.append("name_space_gini_constraint2")


    dataset_path = 'Agriplots_final - Full data.xlsx'
    dataset_path = 'Agriplots_final - Full data - including missing rows.xlsx'
    dataset_path = 'datasets_for_testing/Agriplots dataset - 1,000 rows.xlsx'
    influence_on_crops_synthetic_values_path = 'Average influence of PV on crops - synthetic values.xlsx'
    energy_consumption_by_yeshuv_path = 'energy_consumption_by_yeshuv.xlsx'
    energy_consumption_by_machoz_path = ["energy_consumption_by_machoz_aggregated_from_yeshuvim.xlsx", "energy consumption by machoz"]
    assignment_of_missing_yeshuv_names_path = 'assignment_of_missing_yeshuv_names.xlsx'
    assignment_of_missing_yeshuv_names_path = 'assignment_of_missing_yeshuv_names_mali.xlsx'
    yeshuvim_in_eshkolot_path = 'yeshuvim_in_eshkolot.xlsx'
    energy_division_between_eshkolot_path = 'energy_division_between_eshkolot-synthetic_values.xlsx'
    energy_division_between_eshkolot_path = 'energy_division_between_eshkolot-synthetic_values - try 2.xlsx'
    installation_decisions_output_path = 'installation_decisions_results.xlsx'
    final_results_output_path = 'final_results.xlsx'
    testing_data_and_parameters_path = 'sanity_check_1-choosing_based_on_area_constraint.xlsx'
    # parameters of the model
    params = {
        "allowed_loss_from_influence_on_crops_percentage": 0.92,
        "total_area_upper_bound": 20000.00,
        "G_max" : 0.05
        # "G_max" : 0.075100193
        # "G_max" : 1.0
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
    
    if FULL_CONTINUOUS_MODEL:
        DECISION_VARIABLES_TYPE = "continuous decision variables" #forces continuous decision variables for full continuous model
        continuous_model_df = group_by_yeshuv_and_AnafSub(df_dataset)
        df_dataset = continuous_model_df
    
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
        
        removed_constraints.extend(user_input_params[2])
        time.sleep(5)

    # get needed relevant data for running the model, in addition to the parameters (params)
    data = prepare_data_for_model(df_dataset, energy_consumption_by_yeshuv, energy_division_between_eshkolot, energy_consumption_by_machoz, total_potential_revenue_before_PV_of_full_dataset)
    # write data and params to .dat file
    write_dat_file(dat_file, data, params)

    set_decision_variable_type(opl_model_file, DECISION_VARIABLES_TYPE)
    set_objective_function_type(opl_model_file, OBJECTIVE_FUNCTION_TYPE)
    # remove constraints from model if needed
    if removed_constraints:
        remove_constraints_from_model(removed_constraints, opl_model_file, constraints_to_comment_texts)

    # Solve the OPL model and put the opl output in the opl_raw_output variable
    opl_raw_output = solve_opl_model(opl_model_file, dat_file, txt_output_path)
    # converting the raw output of the model to a dataframe with the needed results
    df_results = raw_output_to_df(opl_raw_output)
    # output the final results to excel file
    output_opl_results_to_excel(df_dataset, df_results, params, installation_decisions_output_path, final_results_output_path, DECISION_VARIABLES_TYPE, OBJECTIVE_FUNCTION_TYPE)
    
    resutls_for_GIS = get_results_for_GIS_tool(df_dataset, df_results, "results_for_GIS_temp.xlsx")

    return resutls_for_GIS


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




if __name__ == "__main__":
    # pass
    resutls_for_GIS = main()
