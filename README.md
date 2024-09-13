# Agriplots-project

This repository contains the files and scripts for optimizing photovoltaic (PV) installations on agricultural plots (Agriplots). The aim is to maximize energy production while considering the influence on crops and other constraints.

## Files Overview

### 1. **Agriplots.mod**
   - This is the core OPL model file that defines the linear programming model.
   - **Objective**: Maximize energy production from tracking and fixed PV installations across multiple locations.
   - **Constraints**:
     - At most one PV can be installed at each location.
     - The total number of PV installations is capped by a predefined limit.
     - Ensure that the influence of PVs on crops does not fall below a minimum threshold.
     - Meet or exceed the required total revenue.
   - Decision variables and constraints are described in more detail in the PDF file "Agriplots Basic Linear Programming Model.pdf".

### 2. **Agriplots_solve_opl.py**
   - A Python script for preparing data, writing it into a `.dat` file, and solving the OPL model using the `oplrun` command.
   - It processes data from several Excel files (listed below) to extract relevant parameters like energy production, influence on crops, and revenue.
   - The script writes these parameters into the `.dat` file, which is then used by the OPL model for solving.
   - It also includes functionality to handle errors during the execution of the OPL model and writes the results into an output file.

### 3. **Agriplots.dat**
   - This `.dat` file contains the input data used by the OPL model. It is generated dynamically by the Python script based on the dataset provided in Excel files.
   - Parameters like the number of locations, energy production values, crop influence, and revenue are stored here.

### 4. **Agriplots Basic Linear Programming Model.pdf**
   - A PDF that describes the structure of the linear programming model, including the decision variables, objective function, and constraints.
   - This document serves as a reference for understanding how the OPL model is constructed and the logic behind it.

### 5. **Excel Files**:
   These files contain datasets that are used in the model. They provide input data such as energy consumption, revenue, and influence of PV on crops for different locations.
   
   - **Agriplots dataset - 1000 rows.xlsx**: The main dataset with energy production, crop influence, revenue, and area data for multiple locations.
   - **energy_consumption_by_yeshuv-average_consumption_times_population_per_yeshuv.xlsx**: Contains data on the energy consumption by each yeshuv (settlement), used to define energy demands for various locations.
   - **energy_division_between_eshkolot-synthetic_values.xlsx**: Data on how energy production is divided among different eshkolot (regions).
   - **Average influence of PV on crops - synthetic values.xlsx**: Provides information on the average influence of PV installations on crops, critical for ensuring crop health in the optimization model.
   - **yeshuvim_in_eshkolot.xlsx**: A dataset mapping yeshuvim to eshkolot, used to group locations and manage energy distribution.

## How to Run the Model

1. Ensure you have IBM ILOG CPLEX Optimization Studio installed, and `oplrun` is available in your PATH.
2. Use the Python script `Agriplots_solve_opl.py` to generate the `.dat` file and solve the model:
   ```bash
   python Agriplots_solve_opl.py
3. The solution will be printed to the console and saved in the `output.txt` file.


### 5. **Requirements**:   
   - Python 3.x
   - IBM ILOG CPLEX Optimization Studio
   - **energy_division_between_eshkolot-synthetic_values.xlsx**: Data on how energy production is divided among different eshkolot (regions).
   - Pandas library (for data manipulation)
