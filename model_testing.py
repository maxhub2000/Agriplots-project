import pandas as pd

# Allowed values for specific columns
machoz_names = ["Center", "Haifa", "Jerusalem", "North", "South", "Tel Aviv", "Other"]
yeshuv_names = ["vineyard מהר\"ל", "vineyard שלום", "אבו ג'ווייעד )שבט(", "אבו גוש", "אבו סנאן", "אביאל", "אביבים"]
anafsub_names = ["nuts", "grapefruits", "field crops general", "greenhouse crops", "open area crops", "grass"]

# Helper function to calculate "Potential revenue from crops after PV"
def calculate_revenue_after_pv(before_pv, anafsub, influence_dict):
    influence = influence_dict.get(anafsub, 1.0)
    return round(before_pv * influence, 2)

# Test case templates
test_cases = {
    "test_case_1.xlsx": {
        "data": [
            {"OBJECTID": 101, "YeshuvName": "vineyard מהר\"ל", "Dunam": 5, 
             "AnafSub": "nuts", "Machoz": "Center",
             "Energy production (fix) mln kWh/year": 15, "Feasability to install PVs?": 1,
             "Potential revenue from crops before PV, mln NIS": 100},
            {"OBJECTID": 102, "YeshuvName": "vineyard שלום", "Dunam": 7, 
             "AnafSub": "grapefruits", "Machoz": "North",
             "Energy production (fix) mln kWh/year": 10, "Feasability to install PVs?": 1,
             "Potential revenue from crops before PV, mln NIS": 80},
        ],
        "parameters": {
            "allowed_loss_from_influence_on_crops_percentage": 0.05,  # Tight, but feasible
            "total_area_upper_bound": 6,  # Only one location can fit
            "G_max": 0.3
        }
    },
    "test_case_2.xlsx": {
        "data": [
            {"OBJECTID": 103, "YeshuvName": "אבו גוש", "Dunam": 3, 
             "AnafSub": "field crops general", "Machoz": "South",
             "Energy production (fix) mln kWh/year": 10, "Feasability to install PVs?": 1,
             "Potential revenue from crops before PV, mln NIS": 50},
            {"OBJECTID": 104, "YeshuvName": "אבו סנאן", "Dunam": 4, 
             "AnafSub": "greenhouse crops", "Machoz": "Tel Aviv",
             "Energy production (fix) mln kWh/year": 12, "Feasability to install PVs?": 1,
             "Potential revenue from crops before PV, mln NIS": 60},
            {"OBJECTID": 105, "YeshuvName": "אביאל", "Dunam": 2, 
             "AnafSub": "open area crops", "Machoz": "Haifa",
             "Energy production (fix) mln kWh/year": 8, "Feasability to install PVs?": 1,
             "Potential revenue from crops before PV, mln NIS": 40},
        ],
        "parameters": {
            "allowed_loss_from_influence_on_crops_percentage": 0.2,  # Generous, allowing flexibility
            "total_area_upper_bound": 10,  # All locations fit
            "G_max": 0.3
        }
    },
    "test_case_3.xlsx": {
        "data": [
            {"OBJECTID": 106, "YeshuvName": "אבו גוש", "Dunam": 5, 
             "AnafSub": "grass", "Machoz": "South",
             "Energy production (fix) mln kWh/year": 10, "Feasability to install PVs?": 1,
             "Potential revenue from crops before PV, mln NIS": 100},
            {"OBJECTID": 107, "YeshuvName": "אביבים", "Dunam": 6, 
             "AnafSub": "field crops general", "Machoz": "Center",
             "Energy production (fix) mln kWh/year": 20, "Feasability to install PVs?": 1,
             "Potential revenue from crops before PV, mln NIS": 200},
        ],
        "parameters": {
            "allowed_loss_from_influence_on_crops_percentage": 0.1,  # Feasible on revenue
            "total_area_upper_bound": 5,  # No location fits
            "G_max": 0.3
        }
    },
    "test_case_4.xlsx": {
        "data": [
            {"OBJECTID": 108, "YeshuvName": "אבו סנאן", "Dunam": 4, 
             "AnafSub": "nuts", "Machoz": "Tel Aviv",
             "Energy production (fix) mln kWh/year": 20, "Feasability to install PVs?": 1,
             "Potential revenue from crops before PV, mln NIS": 150},
        ],
        "parameters": {
            "allowed_loss_from_influence_on_crops_percentage": 0.1,
            "total_area_upper_bound": 4,  # Exactly fits one location
            "G_max": 0.1
        }
    },
    "test_case_5.xlsx": {
        "data": [
            {"OBJECTID": 109, "YeshuvName": "אבו גוש", "Dunam": 4, 
             "AnafSub": "grapefruits", "Machoz": "North",
             "Energy production (fix) mln kWh/year": 18, "Feasability to install PVs?": 1,
             "Potential revenue from crops before PV, mln NIS": 120},
        ],
        "parameters": {
            "allowed_loss_from_influence_on_crops_percentage": 0.3,
            "total_area_upper_bound": 5,
            "G_max": 0.3
        }
    }
}

# Create and save Excel files
for file_name, case in test_cases.items():
    # Prepare the "Influence on crops" sheet
    influence_df = pd.DataFrame([
        {"AnafSub": name, "Average influence": round(1.0 - 0.01 * i, 2)} for i, name in enumerate(anafsub_names)
    ])
    influence_dict = dict(zip(influence_df["AnafSub"], influence_df["Average influence"]))

    # Prepare the "data" sheet
    data = case["data"]
    for row in data:
        anafsub = row["AnafSub"]
        before_pv = row["Potential revenue from crops before PV, mln NIS"]
        row["Potential revenue from crops after PV, mln NIS"] = calculate_revenue_after_pv(before_pv, anafsub, influence_dict)

    # Reorder columns
    data_df = pd.DataFrame(data)[[
        "OBJECTID", "YeshuvName", "Dunam", "AnafSub", "Machoz", 
        "Energy production (fix) mln kWh/year", "Feasability to install PVs?", 
        "Potential revenue from crops before PV, mln NIS", "Potential revenue from crops after PV, mln NIS"
    ]]

    # Prepare the "parameters" sheet
    parameters_df = pd.DataFrame([case["parameters"]])

    # Save to Excel
    with pd.ExcelWriter(file_name, engine='openpyxl') as writer:
        data_df.to_excel(writer, index=False, sheet_name="data")
        influence_df.to_excel(writer, index=False, sheet_name="Influence on crops")
        parameters_df.to_excel(writer, index=False, sheet_name="parameters")

print("Excel files created successfully!")
