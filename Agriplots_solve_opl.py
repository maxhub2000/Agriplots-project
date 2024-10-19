import subprocess
import shutil
import pandas as pd
import time



def create_yeshuvim_with_locations(df_):
    yeshuvim_locations_df = df_[['location_id', 'YeshuvName']]
    D = {}
    for YeshuvName in yeshuvim_locations_df["YeshuvName"].unique():
        # Get all location IDs associated with the current YeshuvName
        location_ids = yeshuvim_locations_df.loc[yeshuvim_locations_df['YeshuvName'] == YeshuvName]["location_id"].tolist()
        if YeshuvName not in D:
            D[YeshuvName] = set(location_ids)  # Create a set with all locations for the YeshuvName
        else:
            D[YeshuvName].update(location_ids)  # Update the set with additional location_ids if any   
    return D
  
def adjust_energy_consumption_by_yeshuv(energy_consumption_by_yeshuv_, relevant_yeshuvim_):
    energy_consumption_by_yeshuv_ = energy_consumption_by_yeshuv_.drop(['yeshuv_symbol'], axis=1) # remove yeshuv_symbol column
    # creating energy consumption by yeshuv for only yeshuvim in inputed df (relevant_yeshuvim_),
    # if yeshuv not in original energy_consumption_by_yeshuv, their yearly consumption will be 0
    adjusted_df = pd.DataFrame(columns=['yeshuv_name', 'yearly energy consumption'])
    for yeshuv in relevant_yeshuvim_:
        if yeshuv in energy_consumption_by_yeshuv_["yeshuv_name"].tolist():
            # if yeshuv in input df, get it's yeshuv name and yearly energy consumption in the "row" var, then append the row to the adjusted_df
            row = energy_consumption_by_yeshuv_.loc[energy_consumption_by_yeshuv_['yeshuv_name'] == yeshuv]
            adjusted_df = adjusted_df.append(row, ignore_index = True)
        else:
            # otherwise, add the yeshuv name with yearly energy consumption of 0, so that the model wouldn't choose locations from that yeshuv
            row = {'yeshuv_name': yeshuv, 'yearly energy consumption': 0.00}
            adjusted_df = adjusted_df.append(row, ignore_index = True)
    return adjusted_df

def create_machozot_with_locations(df_):
    machozot_locations_df = df_[['location_id', 'Machoz']]
    D = {}
    for Machoz in machozot_locations_df["Machoz"].unique():
        # Get all location IDs associated with the current Machoz
        location_ids = machozot_locations_df.loc[machozot_locations_df['Machoz'] == Machoz]["location_id"].tolist()
        if Machoz not in D:
            D[Machoz] = set(location_ids)  # Create a set with all locations for the Machoz
        else:
            D[Machoz].update(location_ids)  # Update the set with additional location_ids if any   
    return D

def adjust_energy_consumption_by_machoz(energy_consumption_by_machoz_, relevant_machozot_):
    # creating energy consumption by machoz for only machozot in inputed df (relevant_machozot_),
    # if machoz not in original energy_consumption_by_machoz, their yearly consumption will be 0
    adjusted_df = pd.DataFrame(columns=['machoz', 'yearly energy consumption'])
    for machoz in relevant_machozot_:
        if machoz in energy_consumption_by_machoz_["machoz"].tolist():
            # if machoz in input df, get it's machoz name and yearly energy consumption in the "row" var, then append the row to the adjusted_df
            row = energy_consumption_by_machoz_.loc[energy_consumption_by_machoz_['machoz'] == machoz]
            adjusted_df = adjusted_df.append(row, ignore_index = True)
        else:
            # otherwise, add the machoz name with yearly energy consumption of 0, so that the model wouldn't choose locations from that machoz
            row = {'machoz': machoz, 'yearly energy consumption': 0.00}
            adjusted_df = adjusted_df.append(row, ignore_index = True)
    return adjusted_df

def sort_df_by_list_order(df_, list_order, column_name):
    """
    Sort a DataFrame by the order of values in a list.

    Parameters:
    df (pd.DataFrame): The DataFrame to sort.
    list_order (list): A list of values specifying the desired order.
    column_name (str): The column in df to be sorted based on the list_order.

    Returns:
    pd.DataFrame: A new DataFrame sorted according to the list_order.
    """
    # Convert the specified column to a categorical type with the provided order
    df_[column_name] = pd.Categorical(df_[column_name], categories=list_order, ordered=True)
    # Sort the DataFrame by the specified column
    df_sorted = df_.sort_values(column_name).reset_index(drop=True)
    return df_sorted

def create_eshkolot_with_locations(df_):
    eshkolot_locations_df = df_[['location_id', 'eshkol']]
    D = {}
    eshkolot_lst = eshkolot_locations_df["eshkol"].unique()
    eshkolot_lst = sorted(eshkolot_lst)
    print("eshkolot_lst",eshkolot_lst)
    for eshkol in eshkolot_lst:
        # Get all location IDs associated with the current eshkol
        location_ids = eshkolot_locations_df.loc[eshkolot_locations_df['eshkol'] == eshkol]["location_id"].tolist()
        if eshkol not in D:
            D[eshkol] = set(location_ids)  # Create a set with all locations for the eshkol
        else:
            D[eshkol].update(location_ids)  # Update the set with additional location_ids if any   
    return D

def adjust_energy_division_between_eshkolot(energy_division_between_eshkolot_, relevant_eshkolot_):
    # creating energy division between eshkolot for only eshkolot in inputed df (relevant_eshkolot_),
    # if eshkol not in original energy_division_between_eshkolot_, their percentage_of_energy_output will be 0
    adjusted_df = pd.DataFrame(columns=['eshkol', 'percentage_of_energy_output'])
    for eshkol in relevant_eshkolot_:
        if eshkol in energy_division_between_eshkolot_["eshkol"].tolist():
            # if eshkol in input df, get it's eshkol number and percentage of energy output in the "row" var, then append the row to the adjusted_df
            row = energy_division_between_eshkolot_.loc[energy_division_between_eshkolot_['eshkol'] == eshkol]
            adjusted_df = adjusted_df.append(row, ignore_index = True)
        else:
            # otherwise, add the eshkol num with percentage of energy output of 0, so that the model wouldn't choose locations from that eshkol
            row = {'eshkol': eshkol, 'percentage_of_energy_output': 0.00}
            adjusted_df = adjusted_df.append(row, ignore_index = True)
    return adjusted_df

def prepare_data(df_, energy_consumption_by_yeshuv, energy_division_between_eshkolot, energy_consumption_by_machoz):
    fix_energy_production = df_['Energy production (fix) mln kWh/year'].tolist()
    area_in_dunam = df_['Dunam'].tolist()
    influence_on_crops = df_['Average influence of PV on crops'].tolist()
    potential_revenue_before_PV = df_['Potential revenue from crops before PV, mln NIS'].tolist()
    num_locations = len(fix_energy_production)


    yeshuvim_with_locations = create_yeshuvim_with_locations(df_)
    # takes only yeshuvim that appear in the current dataset; values are unique since yeshuvim_with_locations is a dictionary
    relevant_yeshuvim = list(yeshuvim_with_locations.keys())
    num_yeshuvim = len(relevant_yeshuvim)
    # adjust energy consumptions so that it will only include yeshuvim from the dataset, and then convert it to a list
    energy_consumption_by_yeshuv = adjust_energy_consumption_by_yeshuv(energy_consumption_by_yeshuv, relevant_yeshuvim)
    energy_consumption_by_yeshuv = energy_consumption_by_yeshuv['yearly energy consumption'].tolist()


    machozot_with_locations = create_machozot_with_locations(df_)
    # takes only machozot that appear in the current dataset; values are unique since machozot_with_locations is a dictionary
    relevant_machozot = list(machozot_with_locations.keys())
    num_machozot = len(relevant_machozot)
    # adjust energy consumptions so that it will only include machozot from the dataset, and then convert it to a list
    energy_consumption_by_machoz = adjust_energy_consumption_by_machoz(energy_consumption_by_machoz, relevant_machozot)
    energy_consumption_by_machoz = energy_consumption_by_machoz['yearly energy consumption'].tolist()


    #eshkolot_with_locations = df_[['location_id', 'eshkol']][df_['eshkol'] == -1]
    eshkolot_with_locations = create_eshkolot_with_locations(df_)
    #print("eshkolot_with_locations:\n", eshkolot_with_locations)
    # takes only eshkolot that appear in the current dataset; values are unique since eshkolot_with_locations is a dictionary
    relevant_eshkolot = list(eshkolot_with_locations.keys())
    #print("relevant_eshkolot:\n",relevant_eshkolot)
    num_eshkolot = len(relevant_eshkolot)
    # adjust energy_division_between_eshkolot so that it will only include eshkolot from the dataset, and then convert it to a list
    energy_division_between_eshkolot = adjust_energy_division_between_eshkolot(energy_division_between_eshkolot, relevant_eshkolot)
    energy_division_between_eshkolot = energy_division_between_eshkolot['percentage_of_energy_output'].tolist()


    return {
        "num_locations" : num_locations, #need to be first here, otherwise there will be bug in the mod file
        "fix_energy_production" : fix_energy_production,
        "influence_on_crops" : influence_on_crops,
        "potential_revenue_before_PV" : potential_revenue_before_PV,
        "area_in_dunam" : area_in_dunam,
        "yeshuvim_with_locations" : yeshuvim_with_locations,
        "num_yeshuvim" : num_yeshuvim,
        "energy_consumption_by_yeshuv" : energy_consumption_by_yeshuv,
        "machozot_with_locations" : machozot_with_locations,
        "num_machozot" : num_machozot,
        "energy_consumption_by_machoz" : energy_consumption_by_machoz,
        "eshkolot_with_locations" : eshkolot_with_locations,
        "num_eshkolot" : num_eshkolot,
        "energy_division_between_eshkolot" : energy_division_between_eshkolot
    }

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

def modify_influence_on_crops(df_, synthetic_values_of_influence_on_crops_path):
    # prepare dictionary that maps for each crop how much it's influenced by installing PV
    influence_on_crops_data = pd.read_excel(synthetic_values_of_influence_on_crops_path)
    influence_on_crops_dict = influence_on_crops_data.set_index("AnafSub")["Average influence"].to_dict()
    # maps average influence on crops to each AnafSub according to the influence_on_crops_dict (like Vlookp)
    modified_influence_on_crops = df_['AnafSub'].map(influence_on_crops_dict).tolist()
    df_["Average influence of PV on crops"] = modified_influence_on_crops
    return df_

def remove_rows_with_missing_values(df_):
    # remove rows with nan values (Ideally should find a better way to handle those nan values later on)
    df_ = df_.dropna(subset=['Energy production (fix) mln kWh/year',
                           'Average influence of PV on crops',
                           'Total revenue, mln NIS',
                           'Dunam'])
    return df_

def add_eshkolot_to_dataset(df_, yeshuvim_in_eshkolot_):
    # Perform a left join to add the 'eshkol' column from yeshuvim_in_eshkolot_ to df_
    df_ = pd.merge(df_, yeshuvim_in_eshkolot_, on='YeshuvName', how='left')
    # Fill missing values (if a YeshuvName is not found in yeshuvim_in_eshkolot_, set 'eshkol' to -1)
    df_['eshkol'].fillna(-1, inplace=True)
    # Optionally, convert 'eshkol' to integer if needed
    df_['eshkol'] = df_['eshkol'].astype(int)
    #remove rows that has eshkol -1
    df_ = df_[df_['eshkol'] != -1]
    #df_ = df_[df_['location_id'] != 990]
    return df_

def raw_output_to_df(opl_raw_output_):
    # Parse the result output here to extract the required values
    # For simplicity, I'll assume we parse the output and extract needed results manually
    output_results_for_excel = ""  # Variable to store multiple lines of output
    capture_excel_output = False  # Flag to start capturing excel output
    for line in opl_raw_output_.splitlines():
        # Detect the start of the excel output block
        if "Results for excel output file:" in line:
            capture_excel_output = True  # Start capturing from the next line
            continue  # Skip the current line
        
        # Capture subsequent lines after the keyword is detected
        if capture_excel_output:
            if line.strip() == "":  # Stop capturing when we hit an empty line (or define another end condition)
                break
            output_results_for_excel += line + "\n"  # Append the line to the result string

    output_results_for_excel = output_results_for_excel.strip()
    output_results_for_excel = output_results_for_excel.split("\n")  # Splitting at the \n delimiter
    df_results = model_results_to_df(output_results_for_excel)
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

def output_opl_results_to_excel(df_input, df_opl_results, output_path):
    relevant_columns_from_input = ["location_id", "OBJECTID", "YeshuvName", "Machoz", "eshkol", "Potential revenue from crops before PV, mln NIS", "Potential revenue from crops after PV, mln NIS"]
    relevant_df_from_input = df_input[relevant_columns_from_input]
    # convert "OBJECTID" and "Location" column to int, so the merge will be successful
    relevant_df_from_input['OBJECTID'] = relevant_df_from_input['OBJECTID'].astype('int')
    df_opl_results['location_id'] = df_opl_results['location_id'].astype('int')
    # left join installed locations from result of opl model to columns from input dataset
    results_left_joined_input_columns = pd.merge(df_opl_results, relevant_df_from_input, on="location_id", how="left")    
    # exporting results to excel
    print(f"Excel output saved to {output_path}")
    results_left_joined_input_columns.to_excel(output_path)


def main():
    # Save timestamp
    start_time_code = time.time()
    # File paths and parameters
    opl_model_file, dat_file, output_file = 'Agriplots.mod', 'Agriplots.dat', 'output.txt'
    df_dataset = pd.read_excel('Agriplots dataset - 1000 rows.xlsx') # Read dataset from Excel
    # df_dataset["location_id"] = df_dataset.index + 1
    # print("df_dataset[location_id]\n", df_dataset["location_id"])
    df_dataset = remove_rows_with_missing_values(df_dataset)
    # modify influence on crops column based on synthetic values
    df_dataset = modify_influence_on_crops(df_dataset, 'Average influence of PV on crops - synthetic values.xlsx')

    energy_consumption_by_yeshuv = pd.read_excel("energy_consumption_by_yeshuv-average_consumption_times_population_per_yeshuv.xlsx")
    energy_consumption_by_machoz = pd.read_excel("energy_consumption_by_machoz_aggregated_from_yeshuvim.xlsx", sheet_name = "energy consumption by machoz")

    #yeshuvim_in_eshkolot = pd.read_excel('yeshuvim_in_eshkolot.xlsx')
    yeshuvim_in_eshkolot = pd.read_excel('yeshuvim_in_eshkolot_modified_to_match_dataset.xlsx')
    yeshuvim_in_eshkolot.rename(columns = {'eshkol_2021':'eshkol'}, inplace = True)
    energy_division_between_eshkolot = pd.read_excel('energy_division_between_eshkolot-synthetic_values.xlsx')
    # add eshkolot to dataset based on yeshuvim_in_eshkolot
    df_dataset = add_eshkolot_to_dataset(df_dataset, yeshuvim_in_eshkolot)
    #print("df_dataset after adding eshkolot:\n", df_dataset)
    df_dataset.to_excel("df_dataset_after_adding_eshkolot.xlsx")


    # parameters of the model
    params = {
        "allowed_loss_from_influence_on_crops_percentage": 0.9,
        "total_area_upper_bound": 1500.00,
        "G_max" : 0.05
    }


    df_dataset = df_dataset.reset_index()
    df_dataset["location_id"] = df_dataset.index + 1
    print("df_dataset[location_id]\n", df_dataset["location_id"])


    data = prepare_data(df_dataset, energy_consumption_by_yeshuv, energy_division_between_eshkolot, energy_consumption_by_machoz)
    # Write data to .dat file
    write_dat_file(dat_file, data, params)

    # Save timestamp
    end_time_code = time.time()
    run_time_code_before_opl_model = end_time_code - start_time_code
    print("\nrun_time_code_before_opl_model:",run_time_code_before_opl_model, "\n")
    
    # Save timestamp
    start_time_opl_model = time.time()

    # Solve the OPL model and put the opl output in the opl_raw_output variable
    opl_raw_output = solve_opl_model(opl_model_file, dat_file, output_file)

    # Save timestamp
    end_time_opl_model = time.time()

    run_time_opl_model = end_time_opl_model - start_time_opl_model
    print("\nrun_time_opl_model:",run_time_opl_model,"\n")


    df_results = raw_output_to_df(opl_raw_output)
    print("model_results:\n", df_results)
    final_results_excel_output_path = 'final_opl_results.xlsx'
    output_opl_results_to_excel(df_dataset, df_results, final_results_excel_output_path)




if __name__ == "__main__":
    main()
