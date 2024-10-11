import subprocess
import shutil
import pandas as pd


def create_locations_in_yeshuvim(yeshuvim_with_locations_):
    D = {}
    for YeshuvName in yeshuvim_with_locations_["YeshuvName"].unique():
        # Get all location IDs associated with the current YeshuvName
        location_ids = yeshuvim_with_locations_.loc[yeshuvim_with_locations_['YeshuvName'] == YeshuvName]["location_id"].tolist()
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

def create_locations_in_eshkolot(eshkolot_with_locations_):
    D = {}
    eshkolot_lst = eshkolot_with_locations_["eshkol"].unique()
    eshkolot_lst = sorted(eshkolot_lst)
    print("eshkolot_lst",eshkolot_lst)
    for eshkol in eshkolot_lst:
        # Get all location IDs associated with the current eshkol
        location_ids = eshkolot_with_locations_.loc[eshkolot_with_locations_['eshkol'] == eshkol]["location_id"].tolist()
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

def prepare_data(df_, energy_consumption_by_yeshuv, energy_division_between_eshkolot):
    fix_energy_production = df_['Energy production (fix) mln kWh/year'].tolist()
    total_revenue = df_['Total revenue, mln NIS'].tolist()
    area_in_dunam = df_['Dunam'].tolist()
    influence_on_crops = df_['Average influence of PV on crops'].tolist()
    num_locations = len(fix_energy_production)

    yeshuvim_with_locations = df_[['location_id', 'YeshuvName']]
    locations_in_yeshuvim = create_locations_in_yeshuvim(yeshuvim_with_locations)
    yeshuvim_with_locations = locations_in_yeshuvim
    # takes only yeshuvim that appear in the current dataset; values are unique since yeshuvim_with_locations is a dictionary
    relevant_yeshuvim = list(yeshuvim_with_locations.keys())
    num_yeshuvim = len(relevant_yeshuvim)
    # adjust energy consumptions so that it will only include yeshuvim from the dataset, and then convert it to a list
    energy_consumption_by_yeshuv = adjust_energy_consumption_by_yeshuv(energy_consumption_by_yeshuv, relevant_yeshuvim)
    energy_consumption_by_yeshuv = energy_consumption_by_yeshuv['yearly energy consumption'].tolist()


    #eshkolot_with_locations = df_[['location_id', 'eshkol']][df_['eshkol'] == -1]
    eshkolot_with_locations = df_[['location_id', 'eshkol']]
    print("eshkolot_with_locations:\n", eshkolot_with_locations)
    locations_in_eshkolot = create_locations_in_eshkolot(eshkolot_with_locations)
    #print("locations_in_eshkolot:\n",locations_in_eshkolot)
    eshkolot_with_locations = locations_in_eshkolot
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
        "total_revenue" : total_revenue,
        "area_in_dunam" : area_in_dunam,
        "yeshuvim_with_locations" : yeshuvim_with_locations,
        "num_yeshuvim" : num_yeshuvim,
        "energy_consumption_by_yeshuv" : energy_consumption_by_yeshuv,
        "eshkolot_with_locations" : eshkolot_with_locations,
        "num_eshkolot" : num_eshkolot,
        "energy_division_between_eshkolot" : energy_division_between_eshkolot
    }

def write_dat_file(dat_file, data, params):
    yeshuvim_with_locations = data.pop("yeshuvim_with_locations")
    eshkolot_with_locations = data.pop("eshkolot_with_locations")
    with open(dat_file, 'w') as f:
        for dict in [params, data]:
            for key, val in dict.items():
                f.write(f"{key} = {val};\n")

        f.write("S = [\n")
        for yeshuv, locations in yeshuvim_with_locations.items():
            f.write(f"{locations},\n")
        f.write("];\n")
        
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
    except Exception as e:
        print(f"Error running oplrun: {e}")


def modify_influence_on_crops(df_, synthetic_values_of_influence_on_crops_path):
    # prepare dictionary that maps for each crop how much it's influenced by installing PV
    influence_on_crops_data = pd.read_excel(synthetic_values_of_influence_on_crops_path)
    influence_on_crops_data["Average influence"] = (influence_on_crops_data["Average influence"]-1).round(2)
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
    return df_



def main():
    # File paths and parameters
    opl_model_file, dat_file, output_file = 'Agriplots.mod', 'Agriplots.dat', 'output.txt'
    df_dataset = pd.read_excel('Agriplots dataset - 1000 rows.xlsx') # Read dataset from Excel
    df_dataset["location_id"] = df_dataset.index + 1
    print("df_dataset[location_id]\n", df_dataset["location_id"])
    df_dataset = remove_rows_with_missing_values(df_dataset)
    # modify influence on crops column based on synthetic values
    df_dataset = modify_influence_on_crops(df_dataset, 'Average influence of PV on crops - synthetic values.xlsx')

    energy_consumption_by_yeshuv = pd.read_excel("energy_consumption_by_yeshuv-average_consumption_times_population_per_yeshuv.xlsx")
    
    #yeshuvim_in_eshkolot = pd.read_excel('yeshuvim_in_eshkolot.xlsx')
    yeshuvim_in_eshkolot = pd.read_excel('yeshuvim_in_eshkolot_modified_to_match_dataset.xlsx')
    yeshuvim_in_eshkolot.rename(columns = {'eshkol_2021':'eshkol'}, inplace = True)
    energy_division_between_eshkolot = pd.read_excel('energy_division_between_eshkolot-synthetic_values.xlsx')
    # add eshkolot to dataset based on yeshuvim_in_eshkolot
    df_dataset = add_eshkolot_to_dataset(df_dataset, yeshuvim_in_eshkolot)
    print("df_dataset after adding eshkolot:\n", df_dataset)
    
    # parameters of the model
    params = {
        "influence_on_crops_lower_limit": 0.00,
        "minimal_total_revenue": 25.00,
        "total_area_upper_bound": 1500.00
    }

    ### plan regarding outputting the results in a meanningful manner:
    # I will create a location_to_object_id dict (again, maybe in differently from what I tried before):
    # If I have that dictionary, I could have a "connecting table" between the results of the opl model,
    # which is in term of location (a number) and the original data of each field, which is in term of OBJECTID.
    # that will allow me to output more meaningful result and check myself, since I could create a table with OBJECTID as it's key that includes data
    # about the relevant columns from the dataset for each field, for example yeshuv, energy consumption, dunam, influece on crops etc.
    # and also add to that interesting results/data from the opl run, for example the location, whether or not it was included in the model, in which city/eshkol it was
    # in the model (sanity check) etc.
    # I should probably implement that in a seperate python file that will import stuff from this file, and output the resluts as xlsx file.
    
    data = prepare_data(df_dataset, energy_consumption_by_yeshuv, energy_division_between_eshkolot)
    # Write data to .dat file
    write_dat_file(dat_file, data, params)
    # Solve the OPL model
    solve_opl_model(opl_model_file, dat_file, output_file)

if __name__ == "__main__":
    main()
