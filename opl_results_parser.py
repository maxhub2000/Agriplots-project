import pandas as pd


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



