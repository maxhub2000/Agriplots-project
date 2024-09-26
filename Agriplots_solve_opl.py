import subprocess
import shutil
import pandas as pd

def create_yeshuvim_with_locations(df, yeshuvim_in_eshkolot):
    yeshuvim_in_df = df['YeshuvName']
    yeshuvim_eshkolot_in_df = pd.merge(yeshuvim_in_df, yeshuvim_in_eshkolot, on='YeshuvName', how='inner')
    yeshuvim_with_locations = {}
    eshkolot_with_locations = {}
    location_to_object_id = {}
    for i in yeshuvim_eshkolot_in_df.index:
        location = i+1
        location_to_object_id[df["OBJECTID"][i]] = location

        yeshuv = yeshuvim_eshkolot_in_df['YeshuvName'][i]
        if yeshuv not in yeshuvim_with_locations:
            yeshuvim_with_locations[yeshuv] = {location}
        else:
            yeshuvim_with_locations[yeshuv].add(location)

        eshkol = yeshuvim_eshkolot_in_df['eshkol'][i]
        if eshkol not in eshkolot_with_locations:
            eshkolot_with_locations[eshkol] = {location}
        else:
            eshkolot_with_locations[eshkol].add(location)
    return yeshuvim_with_locations, eshkolot_with_locations, location_to_object_id


def prepare_data(df, energy_consumption_by_yeshuv, influence_on_crops_dict, yeshuvim_with_locations, eshkolot_with_locations, energy_division_between_eshkolot):

    
    fix_energy_production = df['Energy production (fix) mln kWh/year'].tolist()
    total_revenue = df['Total revenue, mln NIS'].tolist()
    area_in_dunam = df['Dunam'].tolist()
    # maps average influence on crops to each AnafSub according to the influence_on_crops_dict (like Vlookp)
    influence_on_crops = df['AnafSub'].map(influence_on_crops_dict).tolist()
    num_locations = len(fix_energy_production)
    
    num_yeshuvim = len(yeshuvim_with_locations)
    relevant_yeshuvim = yeshuvim_with_locations.keys()
    # takes only yeshuvim that appear in the current dataset
    energy_consumption_by_yeshuv = [row['yearly energy consumption'] for index, row in energy_consumption_by_yeshuv.iterrows() if row['yeshuv_name'] in relevant_yeshuvim]
    
    num_eshkolot = len(eshkolot_with_locations)
    relevant_eshkolot = eshkolot_with_locations.keys()
    # takes only eshkolot that appear in the current dataset
    energy_division_between_eshkolot = [row['percentage_of_energy_output'] for index, row in energy_division_between_eshkolot.iterrows() if row['eshkol'] in relevant_eshkolot]

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


def main():
    # File paths and parameters
    opl_model_file = 'Agriplots.mod'
    dat_file = 'Agriplots.dat'
    df_dataset = pd.read_excel('Agriplots dataset - 1000 rows.xlsx')
    output_file = 'output.txt'
    energy_consumption_by_yeshuv = pd.read_excel("energy_consumption_by_yeshuv-average_consumption_times_population_per_yeshuv.xlsx")
    yeshuvim_in_eshkolot = pd.read_excel('yeshuvim_in_eshkolot.xlsx')
    yeshuvim_in_eshkolot.rename(columns = {'eshkol_2021':'eshkol'}, inplace = True)
    energy_division_between_eshkolot = pd.read_excel('energy_division_between_eshkolot-synthetic_values.xlsx')
    # prepare dictionary that maps for each crop how much it's influenced by installing PV
    influence_on_crops_data = pd.read_excel('Average influence of PV on crops - synthetic values.xlsx')
    influence_on_crops_data["Average influence"] = (influence_on_crops_data["Average influence"]-1).round(2)
    influence_on_crops_dict = influence_on_crops_data.set_index("AnafSub")["Average influence"].to_dict()
    # parameters of the model
    params = {
        "influence_on_crops_lower_limit": 0.00,
        "minimal_total_revenue": 25.00,
        "total_area_upper_bound": 1500.00
    }

    # remove rows with nan values (Ideally should find a better way to handle those nan values later on)
    df_dataset = df_dataset.dropna(subset=['Energy production (fix) mln kWh/year',
                           'Average influence of PV on crops',
                           'Total revenue, mln NIS',
                           'Dunam'])


    yeshuvim_with_locations, eshkolot_with_locations, location_to_object_id = create_yeshuvim_with_locations(df_dataset, yeshuvim_in_eshkolot)
    ###plan regarding using the location_to_object_id dict:
    # If I have that dictionary, I could have a "connecting table" between the results of the opl model,
    # which is in term of location (a number) and the original data of each field, which is in term of OBJECTID.
    # that will allow me to output more meaningful result and check myself, since I could create a table with OBJECTID as it's key that includes data
    # about the relevant columns from the dataset for each field, for example yeshuv, energy consumption, dunam, influece on crops etc.
    # and also add to that interesting results/data from the opl run, for example the location, whether or not it was included in the model, in which city/eshkol it was
    # in the model (sanity check) etc.
    # I should probably implement that in a seperate python file that will import stuff from this file, and output the resluts as xlsx file.

    # Read data from Excel
    data = prepare_data(df_dataset, energy_consumption_by_yeshuv, influence_on_crops_dict, yeshuvim_with_locations, eshkolot_with_locations, energy_division_between_eshkolot)
    # Write data to .dat file
    write_dat_file(dat_file, data, params)
    # Solve the OPL model
    solve_opl_model(opl_model_file, dat_file, output_file)

if __name__ == "__main__":
    main()
