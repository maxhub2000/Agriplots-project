// Parameters
int num_locations = ...;
int num_yeshuvim = ...;
int num_machozot = ...;
int num_eshkolot = ...;
float Remaining_percentage_of_revenue_after_influence_on_crops_lower_bound = ...;
float total_area_upper_bound = ...;
float total_installation_cost_upper_bound = ...;
float total_energy_lower_bound = ...;
// float G_max = ...; ## uncomment if Gini coefficient is used in the model as a constraint
float total_potential_revenue_before_PV_of_full_dataset = ...;
float fix_energy_production[1..num_locations] = ...;
float influence_on_crops[1..num_locations] = ...;
float installation_costs[1..num_locations] = ...;
float potential_revenue_before_PV[1..num_locations] = ...;
float area_in_dunam[1..num_locations] = ...;

range Yeshuvim = 1..num_yeshuvim;
float energy_consumption_by_yeshuv[Yeshuvim] = ...;
range Machozot = 1..num_machozot;
float energy_consumption_by_machoz[Machozot] = ...;
range Eshkolot = 1..num_eshkolot;
//float energy_division_between_eshkolot[Eshkolot] = ...; ## uncomment if Gini coefficient is used in the model
float energy_lower_bounds_for_eshkolot[Eshkolot] = ...;
float energy_upper_bounds_for_eshkolot[Eshkolot] = ...;

// Define sets S_j for each yeshuv j
{int} S[j in Yeshuvim] = ...; // Load sets from .dat file

// Define sets M_j for each machoz j
{int} M[j in Machozot] = ...; // Load sets from .dat file

// Define sets E_k for each eshkol k
{int} E[k in Eshkolot] = ...; // Load sets from .dat file

// Decision Variables and expressions
dvar boolean x[1..num_locations]; // binary (boolean) decision variables
dexpr float y[k in Eshkolot] = sum(i in E[k]) x[i] * fix_energy_production[i];
dexpr float TotalEnergy = sum(i in 1..num_locations) fix_energy_production[i] * x[i]; // Total energy produced
dexpr float TotalArea = sum(i in 1..num_locations) (x[i] * area_in_dunam[i]); // Total area used
dexpr float RemainingPercentageOfRevenue = (total_potential_revenue_before_PV_of_full_dataset + sum(i in 1..num_locations) (x[i] * potential_revenue_before_PV[i] * influence_on_crops[i] - x[i] * potential_revenue_before_PV[i])) / total_potential_revenue_before_PV_of_full_dataset; // Remaining percentage of original revenue after installing PV's
dexpr float TotalInstallationCost = sum(i in 1..num_locations) (x[i] * installation_costs[i]); // Total installation cost
/* ## uncomment if Gini coefficient is used in the model
dvar float z[1..num_eshkolot][1..num_eshkolot]; 
dexpr float G_numerator = sum(i in Eshkolot, j in Eshkolot: i < j) z[i][j]; // numerator of Gini Coefficient value (denominator equals to TotalEnergy)
*/

// Solver settings
execute {
    cplex.tilim = 3600;  // Time limit in seconds
    cplex.epgap = 0.01;  // Optimality gap
    //cplex.tolerances.mipgap = 0.01;  // Optimality gap
}


// Objective Function

// Constraints
subject to {
}


execute {
  writeln("Total energy produced: ", TotalEnergy);
  writeln("Total area (in dunam) used: ", TotalArea);
  writeln("Remaining percentage of revenue after installing PV'S: ", RemainingPercentageOfRevenue);
  writeln("Total installation cost: ", TotalInstallationCost);
}


// Output results
execute {
  //var total_energy_produced = 0;
  var number_of_installed_PV = 0;
  var Overall_total_revenue = 0;
  //var total_area = 0;
  var total_potential_revenue_before_PV_for_included_locations = 0
  var total_potential_revenue_after_PV_for_included_locations = 0
  var num_of_non_binary_dec_variables = 0;
  writeln("Installation decisions:");
  for (var i in fix_energy_production) {
    if (x[i] > 0) {
      writeln("Location ", i, ": ", fix_energy_production[i] * x[i], " mln Energy units Produced, area_in_dunam used: ", area_in_dunam[i], ", potential revenue before PV: ", potential_revenue_before_PV[i], ", potential revenue after PV: ", potential_revenue_before_PV[i] * influence_on_crops[i], " x[",i,"] = ", x[i]);
      //total_energy_produced += fix_energy_production[i] * x[i]
      number_of_installed_PV += 1
      //total_area += area_in_dunam[i]
      total_potential_revenue_before_PV_for_included_locations += potential_revenue_before_PV[i]
      total_potential_revenue_after_PV_for_included_locations += potential_revenue_before_PV[i] * influence_on_crops[i]
      if (x[i] != 1){
        num_of_non_binary_dec_variables +=1
      }

   }
  }


  writeln("Number of installed PV's: ", number_of_installed_PV);
  writeln("total poetntial revenue before installing PV'S for locations included: ", total_potential_revenue_before_PV_for_included_locations);
  writeln("total poetntial revenue after installing PV's for locations included, as a result of influence on crops: ", total_potential_revenue_after_PV_for_included_locations);
  writeln("Number of Non-Binary decision variables: ", num_of_non_binary_dec_variables);



  var total_potential_revenue_before_PV = total_potential_revenue_before_PV_of_full_dataset
  var xi_ci_ri = total_potential_revenue_after_PV_for_included_locations
  var xi_ri = total_potential_revenue_before_PV_for_included_locations
  var r_i = total_potential_revenue_before_PV_of_full_dataset
  writeln("xi_ci_ri: ", xi_ci_ri, "xi_ri: ", xi_ri, "r_i: ", r_i);
  var total_potential_revenue_after_PV = xi_ci_ri + r_i - xi_ri



  writeln("\nEnergy produced by yeshuv: ")
  for (var yeshuv in Yeshuvim) {
    var total_energy_produced_by_yeshuv = 0
    var yeshuv_str = "yeshuv " + yeshuv.toString() + ": " + "allowed energy production: " + energy_consumption_by_yeshuv[yeshuv].toString();
    yeshuv_str += " ,chosen locations: ["
    for (var loc in S[yeshuv])
      if (x[loc] == 1){
        yeshuv_str += loc.toString() + ", "
        total_energy_produced_by_yeshuv += x[loc]*fix_energy_production[loc]
      }
    if (total_energy_produced_by_yeshuv == 0){
      continue
    }
    yeshuv_str += "] total energy produced: " + total_energy_produced_by_yeshuv.toString();
    writeln(yeshuv_str);  
  }


  writeln("\nEnergy produced by machoz: ")
  for (var machoz in Machozot) {
    var total_energy_produced_by_machoz = 0
    var machoz_str = "machoz " + machoz.toString() + ": " + "allowed energy production: " + energy_consumption_by_machoz[machoz].toString();
    machoz_str += " ,chosen locations: ["
    for (var loc in M[machoz])
      if (x[loc] == 1){
        machoz_str += loc.toString() + ", "
        total_energy_produced_by_machoz += x[loc]*fix_energy_production[loc]
      }
    if (total_energy_produced_by_machoz == 0){
      continue
    }
    machoz_str += "] total energy produced: " + total_energy_produced_by_machoz.toString();
    writeln(machoz_str);  
  }


  writeln("\nEnergy produced by eshkol: ")
  for (var eshkol in Eshkolot) {
    var eshkol_str = "eshkol " + eshkol.toString() + ":"
    eshkol_str += " chosen locations: ["
    for (var loc in E[eshkol])
      if (x[loc] == 1){
        eshkol_str += loc.toString() + ", "
      }
    eshkol_str += "] total energy produced: " + y[eshkol];
    writeln(eshkol_str);
  }



  writeln("\nResults for excel output file:")
  writeln("Total energy produced in mln: ", TotalEnergy);
  writeln("Total area (in dunam) used: ", TotalArea);
  writeln("Remaining percentage of revenue: ", RemainingPercentageOfRevenue);
  writeln("Total installation cost: ", TotalInstallationCost);
  writeln("Poetntial revenue before installing PV'S: ", total_potential_revenue_before_PV);
  writeln("Poetntial revenue after installing PV'S: ", total_potential_revenue_after_PV);
  /* ## uncomment if Gini coefficient is used in the model
  if (TotalEnergy > 0){
    var Gini_coefficient_value = G_numerator / TotalEnergy; // calculation of Gini Coefficient value if needed for results 
  } else {
    var Gini_coefficient_value = 1.00; // if TotalEnergy = 0, make Gini_coefficient_value to be 1
  }
  writeln("Gini Coefficient value: ", Gini_coefficient_value);
  */

  writeln("Locations with installed PV's:")
  writeln("location_id,", "x[i],", "Energy units Produced in mln,", "influence on crops,", "area in dunam used");
  for (var i in fix_energy_production) {
    if (x[i] > 0) {
      writeln(i, ",", x[i], ",",  fix_energy_production[i] * x[i], ",", influence_on_crops[i] * x[i], ",", area_in_dunam[i] * x[i]);

   }
  }
  writeln("Energy produced per Eshkol:")
  writeln("Eshkol_num,", "Energy Produced");
  for (var eshkol in Eshkolot) {
    writeln(eshkol, ",", y[eshkol])
  }
 
writeln("End of Results for excel output file")
}


execute {
    for (var eshkol in Eshkolot) {
      writeln(eshkol); 

    }
}
