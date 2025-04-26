import pandas as pd
from typing import List, Dict, Optional, Callable, Union
from utils import measure_time

@measure_time
def prepare_data_for_model(
    df_: pd.DataFrame,
    energy_consumption_by_yeshuv: pd.DataFrame,
    energy_lower_bounds_for_eshkolot: pd.DataFrame,
    energy_upper_bounds_for_eshkolot: pd.DataFrame,
    energy_consumption_by_machoz: pd.DataFrame,
    total_potential_revenue_before_PV_of_full_dataset: float,
    energy_division_between_eshkolot: pd.DataFrame = None
) -> Dict[str, Union[List[float], int, float, Dict[str, set[int]]]]:
    """
    Prepare data for the optimization model.

    Args:
        df_ (pd.DataFrame): input data: df_dataset.
        energy_consumption_by_yeshuv (pd.DataFrame): Yeshuv energy consumption data.
        energy_division_between_eshkolot (pd.DataFrame): Eshkol energy division data.
        energy_consumption_by_machoz (pd.DataFrame): Machoz energy consumption data.
        total_potential_revenue_before_PV_of_full_dataset (float): Total potential revenue before PV installation.

    Returns:
        Dict[str, Union[List[float], int, float, Dict[str, Set[int]]]]: Prepared data for the model.
    """
    fix_energy_production = df_['Energy production (fix) mln kWh/year'].tolist()
    area_in_dunam = df_['Dunam'].tolist()
    influence_on_crops = df_['Average influence of PV on crops'].tolist()
    installation_costs = df_['Installation cost'].tolist()
    potential_revenue_before_PV = df_['Potential revenue from crops before PV, mln NIS'].tolist()
    num_locations = len(fix_energy_production)

    yeshuvim_with_locations = create_yeshuvim_with_locations(df_)
    print("number of yeshuvim in yeshuvim_with_locations:",len(yeshuvim_with_locations))
    # takes only yeshuvim that appear in the current dataset; values are unique since yeshuvim_with_locations is a dictionary
    relevant_yeshuvim = list(yeshuvim_with_locations.keys())
    num_yeshuvim = len(relevant_yeshuvim)
    # adjust energy consumptions so that it will only include yeshuvim from the dataset, and then convert it to a list
    energy_consumption_by_yeshuv = adjust_energy_consumption_by_yeshuv(energy_consumption_by_yeshuv, relevant_yeshuvim)
    print("energy_consumption_by_yeshuv positive values:", len(energy_consumption_by_yeshuv[energy_consumption_by_yeshuv["yearly energy consumption"] > 0]))
    energy_consumption_by_yeshuv = energy_consumption_by_yeshuv['yearly energy consumption'].tolist()

    machozot_with_locations = create_machozot_with_locations(df_)
    # takes only machozot that appear in the current dataset; values are unique since machozot_with_locations is a dictionary
    relevant_machozot = list(machozot_with_locations.keys())
    num_machozot = len(relevant_machozot)
    # adjust energy consumptions so that it will only include machozot from the dataset, and then convert it to a list
    energy_consumption_by_machoz = adjust_energy_consumption_by_machoz(energy_consumption_by_machoz, relevant_machozot)
    energy_consumption_by_machoz = energy_consumption_by_machoz['yearly energy consumption'].tolist()
    eshkolot_with_locations = create_eshkolot_with_locations(df_)
    
    # takes only eshkolot that appear in the current dataset; values are unique since eshkolot_with_locations is a dictionary
    relevant_eshkolot = list(eshkolot_with_locations.keys())
    num_eshkolot = len(relevant_eshkolot)
    # adjust upper and lower bounds for energy division between eshkolot so that it will only include eshkolot from the dataset, and then convert it to a list
    energy_lower_bounds_for_eshkolot = adjust_energy_division_between_eshkolot(energy_lower_bounds_for_eshkolot, relevant_eshkolot)
    energy_lower_bounds_for_eshkolot = energy_lower_bounds_for_eshkolot['percentage_of_energy_output'].tolist()
    energy_upper_bounds_for_eshkolot = adjust_energy_division_between_eshkolot(energy_upper_bounds_for_eshkolot, relevant_eshkolot)
    energy_upper_bounds_for_eshkolot = energy_upper_bounds_for_eshkolot['percentage_of_energy_output'].tolist()

    data_for_model = {
        "num_locations" : num_locations, #need to be first here, otherwise there will be bug in the mod file
        "fix_energy_production" : fix_energy_production,
        "influence_on_crops" : influence_on_crops,
        "installation_costs" : installation_costs,
        "potential_revenue_before_PV" : potential_revenue_before_PV,
        "total_potential_revenue_before_PV_of_full_dataset" : total_potential_revenue_before_PV_of_full_dataset,
        "area_in_dunam" : area_in_dunam,
        "yeshuvim_with_locations" : yeshuvim_with_locations,
        "num_yeshuvim" : num_yeshuvim,
        "energy_consumption_by_yeshuv" : energy_consumption_by_yeshuv,
        "machozot_with_locations" : machozot_with_locations,
        "num_machozot" : num_machozot,
        "energy_consumption_by_machoz" : energy_consumption_by_machoz,
        "eshkolot_with_locations" : eshkolot_with_locations,
        "num_eshkolot" : num_eshkolot,
        "energy_lower_bounds_for_eshkolot" : energy_lower_bounds_for_eshkolot,
        "energy_upper_bounds_for_eshkolot" : energy_upper_bounds_for_eshkolot,
    }
    
    # if provided, adjust energy_division_between_eshkolot so that it will only include eshkolot from the dataset, and then convert it to a list
    if energy_division_between_eshkolot is not None:
        energy_division_between_eshkolot = adjust_energy_division_between_eshkolot(energy_division_between_eshkolot, relevant_eshkolot)
        energy_division_between_eshkolot = energy_division_between_eshkolot['percentage_of_energy_output'].tolist()
        # add energy_division_between_eshkolot to the data that's gonna be used in the model
        data_for_model["energy_division_between_eshkolot"] = energy_division_between_eshkolot
    
    return data_for_model


def create_yeshuvim_with_locations(df_: pd.DataFrame) -> Dict[str, set]:
    """
    Create a mapping of Yeshuv names to their associated location IDs.
    
    Args:
        df_ (pd.DataFrame): DataFrame containing 'location_id' and 'YeshuvName' columns.
    
    Returns:
        Dict[str, set]: Mapping of Yeshuv names to sets of location IDs.
    """
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
  
def adjust_energy_consumption_by_yeshuv(
    energy_consumption_by_yeshuv_: pd.DataFrame, 
    relevant_yeshuvim_: List[str]
) -> pd.DataFrame:
    """
    Adjust energy consumption data to include only relevant Yeshuvim (that appears in df_dataset).
    if yeshuv not in original energy_consumption_by_yeshuv, their yearly consumption will be 0.
    
    Args:
        energy_consumption_by_yeshuv_ (pd.DataFrame): Original energy consumption DataFrame.
        relevant_yeshuvim_ (List[str]): List of relevant Yeshuvim names.
    
    Returns:
        pd.DataFrame: Adjusted energy consumption DataFrame.
    """
    if 'yeshuv_symbol' in energy_consumption_by_yeshuv_.columns:
        energy_consumption_by_yeshuv_ = energy_consumption_by_yeshuv_.drop(['yeshuv_symbol'], axis=1) # remove yeshuv_symbol column
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

def create_machozot_with_locations(df_: pd.DataFrame) -> Dict[str, set[int]]:
    """
    Create a mapping of Machoz names to their associated location IDs.

    Args:
        df_ (pd.DataFrame): DataFrame containing 'location_id' and 'Machoz' columns.

    Returns:
        Dict[str, Set[int]]: Mapping of Machoz names to sets of location IDs.
    """
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

def adjust_energy_consumption_by_machoz(
    energy_consumption_by_machoz_: pd.DataFrame, 
    relevant_machozot_: List[str]
) -> pd.DataFrame:
    """
    Adjust energy consumption data to include only relevant machozot (that appears in df_dataset).
    if machoz not in original energy_consumption_by_machoz, their yearly consumption will be 0.

    Args:
        energy_consumption_by_machoz_ (pd.DataFrame): Original energy consumption DataFrame.
        relevant_machozot_ (List[str]): List of relevant Machozot names.

    Returns:
        pd.DataFrame: Adjusted energy consumption DataFrame.
    """
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

def create_eshkolot_with_locations(df_: pd.DataFrame) -> Dict[str, set[int]]:
    """
    Create a mapping of Eshkol numbers to their associated location IDs.

    Args:
        df_ (pd.DataFrame): DataFrame containing 'location_id' and 'eshkol' columns.

    Returns:
        Dict[str, set[int]]: Mapping of Eshkol numbers to sets of location IDs.
    """
    eshkolot_locations_df = df_[['location_id', 'eshkol']]
    D = {}
    eshkolot_lst = eshkolot_locations_df["eshkol"].unique()
    eshkolot_lst = sorted(eshkolot_lst)
    #print("eshkolot_lst",eshkolot_lst)
    for eshkol in eshkolot_lst:
        # Get all location IDs associated with the current eshkol
        location_ids = eshkolot_locations_df.loc[eshkolot_locations_df['eshkol'] == eshkol]["location_id"].tolist()
        if eshkol not in D:
            D[eshkol] = set(location_ids)  # Create a set with all locations for the eshkol
        else:
            D[eshkol].update(location_ids)  # Update the set with additional location_ids if any   
    return D

def adjust_energy_division_between_eshkolot(
    energy_division_between_eshkolot_: pd.DataFrame, 
    relevant_eshkolot_: List[str]
) -> pd.DataFrame:
    """
    Adjust energy division data to include only relevant Eshkolot(that appears in df_dataset).
    if eshkol not in original energy_division_between_eshkolot_, their percentage_of_energy_output will be 0.

    Args:
        energy_division_between_eshkolot_ (pd.DataFrame): Original energy division DataFrame.
        relevant_eshkolot_ (List[str]): List of relevant Eshkol numbers.

    Returns:
        pd.DataFrame: Adjusted energy division DataFrame.
    """
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






