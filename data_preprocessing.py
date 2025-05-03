import pandas as pd
from utils import measure_time, track_row_changes, load_excel



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



def modify_influence_on_crops(df_, anaf_sub_parameters_synthetic_values_path):
    anaf_sub_parameters_data = load_excel(anaf_sub_parameters_synthetic_values_path)
    # prepare dictionary that maps for each crop how much it's influenced by installing PV
    influence_on_crops_dict = anaf_sub_parameters_data.set_index("AnafSub")["Average influence"].to_dict()
    # maps average influence on crops to each AnafSub according to the influence_on_crops_dict (like Vlookp)
    modified_influence_on_crops = df_['AnafSub'].map(influence_on_crops_dict).tolist()
    df_["Average influence of PV on crops"] = modified_influence_on_crops
    return df_

def add_installation_costs(df_, anaf_sub_parameters_synthetic_values_path):
    anaf_sub_parameters_data = load_excel(anaf_sub_parameters_synthetic_values_path)
    # prepare dictionary that maps for each crop how much what's it's cost per dunam
    costs_of_crops_dict = anaf_sub_parameters_data.set_index("AnafSub")["Cost per Dunam"].to_dict()
    costs_of_crops = df_['AnafSub'].map(costs_of_crops_dict).tolist()
    df_["Cost of AnafSub per dunam"] = costs_of_crops
    df_["Installation cost"] = df_["Cost of AnafSub per dunam"] * df_["Dunam"]
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

