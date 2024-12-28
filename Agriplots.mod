// Parameters
int num_locations = ...;
int num_yeshuvim = ...;
int num_machozot = ...;
int num_eshkolot = ...;
float allowed_loss_from_influence_on_crops_percentage = ...;
float total_area_upper_bound = ...;
float G_max = ...;
float total_potential_revenue_before_PV_of_full_dataset = ...;
float fix_energy_production[1..num_locations] = ...;
float influence_on_crops[1..num_locations] = ...;
float potential_revenue_before_PV[1..num_locations] = ...;
float area_in_dunam[1..num_locations] = ...;

range Yeshuvim = 1..num_yeshuvim;
float energy_consumption_by_yeshuv[Yeshuvim] = ...;
range Machozot = 1..num_machozot;
float energy_consumption_by_machoz[Machozot] = ...;
range Eshkolot = 1..num_eshkolot;
float energy_division_between_eshkolot[Eshkolot] = ...;


// Define sets S_j for each yeshuv j
{int} S[j in Yeshuvim] = ...; // Load sets from .dat file

// Define sets M_j for each machoz j
{int} M[j in Machozot] = ...; // Load sets from .dat file

// Define sets E_k for each eshkol k
{int} E[k in Eshkolot] = ...; // Load sets from .dat file

// Decision Variables
dvar float+ x[1..num_locations]; // float decision variables (0 <= x[i] <= 1)
dexpr float y[k in Eshkolot] = sum(i in E[k]) x[i] * fix_energy_production[i];
dvar float z[1..num_eshkolot][1..num_eshkolot];


// Solver settings (added at the end of the file)
execute {
    cplex.tilim = 3600;  // Time limit in seconds
    cplex.epgap = 0.01;
    //cplex.tolerances.mipgap = 0.01;  // Optimality gap
}


// Objective Function
maximize sum(i in 1..num_locations) (fix_energy_production[i] * x[i]);

// Constraints
subject to {

    // Constraint for an upper bound of the total area used by installed PV's
    sum(i in 1..num_locations) (x[i] * area_in_dunam[i]) <= total_area_upper_bound;
	    
    // Constraint for the revenue change in percentage as a result of installing the PV’s and influencing the crops, lower bounded by an inputed threshold
    total_potential_revenue_before_PV_of_full_dataset + sum(i in 1..num_locations) (x[i] * potential_revenue_before_PV[i] * influence_on_crops[i] - x[i] * potential_revenue_before_PV[i]) >= allowed_loss_from_influence_on_crops_percentage * total_potential_revenue_before_PV_of_full_dataset;

    // Constraint for the total energy production of each yeshuv, upper bounded by the energy consumption of each yeshuv
    forall (j in Yeshuvim) {
        sum(i in S[j]) x[i] * fix_energy_production[i] <= energy_consumption_by_yeshuv[j];
    }
    
    // Constraint for the total energy production of each machoz, upper bounded by the energy consumption of each machoz
    forall (j in Machozot) {
        sum(i in M[j]) x[i] * fix_energy_production[i] <= energy_consumption_by_machoz[j];
    }



    // Linearized Gini coefficient constraint (only for i < j)
    forall(i in Eshkolot, j in Eshkolot: i < j) {
        z[i][j] >=  energy_division_between_eshkolot[j]*y[j] - energy_division_between_eshkolot[i]*y[i] ;
        z[i][j] >=  energy_division_between_eshkolot[i]*y[i] - energy_division_between_eshkolot[j]*y[j] ;
    }


    // Gini constraint (now summing only over i < j)
    sum(i in Eshkolot, j in Eshkolot: i < j) z[i][j] <= G_max * sum(i in 1..num_eshkolot) (y[i]);

    
    // Constraint for the percentage of the total energy production of each eshkol, upper bounded by some fixed percentage
    /*
    forall (k in Eshkolot) {
        sum(i in E[k]) x[i] * fix_energy_production[i] <= energy_division_between_eshkolot[k] * sum(j in 1..num_locations) (fix_energy_production[j] * x[j]);
    }
    */


    // Constraint that limits the value of x[i] to be less or equal than 1
    forall(i in 1..num_locations) 
        x[i] <= 1;                  

}

// Execute block to set the CPLEX time limit
//execute {
  //  writeln("Setting time limit to 60 seconds");
    //cplex.tilim = 60; // Set the time limit to 60 seconds
//}





execute {
  /*
  writeln("Decision variable values:")
  for (var i in fix_energy_production) {
    var dec_variable_str = "x[" + i +"] = " + x[i]
    if (!(x[i] != 1 && x[i] != 0)){
      dec_variable_str += "Non-Binary value";
    }
    writeln(dec_variable_str);
  }
  */

  var total_energy_produced = 0;
  for (var i in fix_energy_production) {
    total_energy_produced += fix_energy_production[i] * x[i];
  }
  writeln("Total energy produced: ", total_energy_produced);
}


// Output results
execute {
  var total_energy_produced = 0;
  var number_of_installed_PV = 0;
  var Overall_total_revenue = 0;
  var total_area = 0;
  var total_potential_revenue_before_PV_for_included_locations = 0
  var total_potential_revenue_after_PV_for_included_locations = 0
  var num_of_non_binary_dec_variables = 0;
  writeln("Installation decisions:");
  for (var i in fix_energy_production) {
    if (x[i] > 0) {
      writeln("Location ", i, ": ", fix_energy_production[i] * x[i], " mln Energy units Produced, area_in_dunam used: ", area_in_dunam[i], ", potential revenue before PV: ", potential_revenue_before_PV[i], ", potential revenue after PV: ", potential_revenue_before_PV[i] * influence_on_crops[i], " x[",i,"] = ", x[i]);
      total_energy_produced += fix_energy_production[i] * x[i]
      number_of_installed_PV += 1
      total_area += area_in_dunam[i]
      total_potential_revenue_before_PV_for_included_locations += potential_revenue_before_PV[i]
      total_potential_revenue_after_PV_for_included_locations += potential_revenue_before_PV[i] * influence_on_crops[i]
      if (x[i] != 1){
        num_of_non_binary_dec_variables +=1
      }


	 }
  }

  writeln("Total energy produced: ", total_energy_produced);
  writeln("Number of installed PV's: ", number_of_installed_PV);
  writeln("total area (in dunam) used: ", total_area);
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


  writeln("\n")
  var total_energy_produced_from_y = 0;
  for (var i in Eshkolot) {
    total_energy_produced_from_y += y[i];
    }
  writeln("Sum of y[i]: ", total_energy_produced_from_y);


  writeln("\nresults of Gini coefficient: ")
  var sum_of_z = 0
  for (var i in Eshkolot){
    for (var j in Eshkolot){
      if (i>=j){
        continue
      }
      else{
        writeln("i: ",i,", j: ",j,", e[i]: ",energy_division_between_eshkolot[i],", e[j]: ",energy_division_between_eshkolot[j], ", e[j]*y[j] - e[i]*y[i]: ",energy_division_between_eshkolot[j]*y[j] - energy_division_between_eshkolot[i]*y[i], ", e[i]*y[i] - e[j]*y[j]: ",energy_division_between_eshkolot[i]*y[i] - energy_division_between_eshkolot[j]*y[j], ", z[i][j]: ",z[i][j])
        sum_of_z += z[i][j]
      }

    }
  }

  Gini_coefficient_value_from_model = sum_of_z/total_energy_produced_from_y

  writeln("\nSum of z[i][j]: ",sum_of_z)
  writeln("inequality of wealth: Sum of z[i][j] / Sum of y[i] = ",Gini_coefficient_value_from_model)


  writeln("\nResults for excel output file:")
  writeln("Total energy produced in mln: ", total_energy_produced);
  writeln("Total area (in dunam) used: ", total_area);
  writeln("Gini Coefficient value: ", Gini_coefficient_value_from_model);
  writeln("Poetntial revenue before installing PV'S: ", total_potential_revenue_before_PV);
  writeln("Poetntial revenue after installing PV'S: ", total_potential_revenue_after_PV);
  writeln("Percentage change in revenue: ", total_potential_revenue_after_PV/total_potential_revenue_before_PV);


  writeln("Locations with installed PV's:")
  writeln("location_id,", "Energy units Produced in mln,", "influence on crops,", "area in dunam used");
  for (var i in fix_energy_production) {
    if (x[i] == 1) {
      writeln(i, ",", fix_energy_production[i] * x[i], ",", influence_on_crops[i] * x[i], ",", area_in_dunam[i] * x[i]);

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
