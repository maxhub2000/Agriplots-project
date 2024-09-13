import subprocess
import shutil
import pandas as pd

def create_cities_with_locations(df, yeshuvim_in_eshkolot):
    yeshuvim_in_df = df['YeshuvName']
    yeshuvim_eshkolot_in_df = pd.merge(yeshuvim_in_df, yeshuvim_in_eshkolot, on='YeshuvName', how='inner')
    cities_with_locations = {}
    eshkolot_with_locations = {}
    for i in yeshuvim_eshkolot_in_df.index:
        location = i+1
        city = yeshuvim_eshkolot_in_df['YeshuvName'][i]
        if city not in cities_with_locations:
            cities_with_locations[city] = {location}
        else:
            cities_with_locations[city].add(location)

        eshkol = yeshuvim_eshkolot_in_df['eshkol'][i]
        if eshkol not in eshkolot_with_locations:
            eshkolot_with_locations[eshkol] = {location}
        else:
            eshkolot_with_locations[eshkol].add(location)
    return cities_with_locations, eshkolot_with_locations


def prepare_data(df, energy_consumption_by_yeshuv, influence_on_crops_dict, yeshuvim_in_eshkolot, energy_division_between_eshkolot):
    # remove rows with nan values (Ideally should find a better way to handle those nan values later on)
    df = df.dropna(subset=['Energy production (fix) mln kWh/year',
                           'Average influence of PV on crops',
                           'Total revenue, mln NIS',
                           'Dunam'])
    
    fix_energy_production = df['Energy production (fix) mln kWh/year'].tolist()
    total_revenue = df['Total revenue, mln NIS'].tolist()
    area_in_dunam = df['Dunam'].tolist()
    # maps average influence on crops to each AnafSub according to the influence_on_crops_dict (like Vlookp)
    influence_on_crops = df['AnafSub'].map(influence_on_crops_dict).tolist()
    num_locations = len(fix_energy_production)
    cities_with_locations, eshkolot_with_locations = create_cities_with_locations(df, yeshuvim_in_eshkolot)
    
    num_cities = len(cities_with_locations)
    relevant_cities = cities_with_locations.keys()
    # takes only cities that appear in the current dataset
    energy_consumption_by_yeshuv = [row['yearly energy consumption'] for index, row in energy_consumption_by_yeshuv.iterrows() if row['yeshuv_name'] in relevant_cities]
    
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
        "cities_with_locations" : cities_with_locations,
        "num_cities" : num_cities,
        "energy_consumption_by_yeshuv" : energy_consumption_by_yeshuv,
        "eshkolot_with_locations" : eshkolot_with_locations,
        "num_eshkolot" : num_eshkolot,
        "energy_division_between_eshkolot" : energy_division_between_eshkolot
    }

def write_dat_file(dat_file, data, params):
    cities_with_locations = data.pop("cities_with_locations")
    eshkolot_with_locations = data.pop("eshkolot_with_locations")
    with open(dat_file, 'w') as f:
        for dict in [params, data]:
            for key, val in dict.items():
                f.write(f"{key} = {val};\n")

        f.write("S = [\n")
        for city, locations in cities_with_locations.items():
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

    # Read data from Excel
    data = prepare_data(df_dataset, energy_consumption_by_yeshuv, influence_on_crops_dict, yeshuvim_in_eshkolot, energy_division_between_eshkolot)
    # Write data to .dat file
    write_dat_file(dat_file, data, params)
    # Solve the OPL model
    solve_opl_model(opl_model_file, dat_file, output_file)

if __name__ == "__main__":
    main()
