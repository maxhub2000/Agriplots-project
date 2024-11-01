// Parameters
int num_locations = ...;
int num_yeshuvim = ...;
int num_machozot = ...;
int num_eshkolot = ...;
float allowed_loss_from_influence_on_crops_percentage = ...;
float total_area_upper_bound = ...;
float G_max = ...;
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
dvar boolean x[1..num_locations]; // binary (boolean) decision variables
dexpr float y[k in Eshkolot] = sum(i in E[k]) x[i] * fix_energy_production[i];
dvar float z[1..num_eshkolot][1..num_eshkolot];


// Objective Function
maximize sum(i in 1..num_locations) (fix_energy_production[i] * x[i]);

// Constraints
subject to {

    // Constraint for an upper bound of the total area used by installed PV's
    sum(i in 1..num_locations) (x[i] * area_in_dunam[i]) <= total_area_upper_bound;
	    
    // Constraint for the revenue change in percentage as a result of installing the PV’s and influencing the crops, lower bounded by an inputed threshold
    sum(i in 1..num_locations) (x[i] * potential_revenue_before_PV[i] * influence_on_crops[i]) >= allowed_loss_from_influence_on_crops_percentage * sum(i in 1..num_locations) (x[i] * potential_revenue_before_PV[i]);

    // Linearized Gini coefficient constraint (only for i < j)
    forall(i in Eshkolot, j in Eshkolot: i < j) {
        z[i][j] >=  energy_division_between_eshkolot[j]*y[j] - energy_division_between_eshkolot[i]*y[i] ;
        z[i][j] >=  energy_division_between_eshkolot[i]*y[i] - energy_division_between_eshkolot[j]*y[j] ;
    }


    // Gini constraint (now summing only over i < j)
    sum(i in Eshkolot, j in Eshkolot: i < j) z[i][j] <= G_max * sum(i in 1..num_eshkolot) (y[i]);


}

// Execute block to set the CPLEX time limit
execute {
    writeln("Setting time limit to 60 seconds");
    cplex.tilim = 60; // Set the time limit to 60 seconds
}



execute {
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
  var total_potential_revenue_before_PV = 0
  var total_potential_revenue_after_PV = 0
  writeln("Installation decisions:");
  for (var i in fix_energy_production) {
    if (x[i] == 1) {
      writeln("Location ", i, ": ", fix_energy_production[i] * x[i], " mln Energy units Produced, area_in_dunam used: ", area_in_dunam[i], ", potential revenue before PV: ", potential_revenue_before_PV[i], ", potential revenue after PV: ", potential_revenue_before_PV[i] * influence_on_crops[i]);
      total_energy_produced += fix_energy_production[i] * x[i]
      number_of_installed_PV += 1
      total_area += area_in_dunam[i]
      total_potential_revenue_before_PV += potential_revenue_before_PV[i]
      total_potential_revenue_after_PV += potential_revenue_before_PV[i] * influence_on_crops[i]


	 }
  }

  writeln("Total energy produced: ", total_energy_produced);
  writeln("Number of installed PV's: ", number_of_installed_PV);
  writeln("total area (in dunam) used: ", total_area);
  writeln("total poetntial revenue before installing PV'S for locations included: ", total_potential_revenue_before_PV);
  writeln("total poetntial revenue after installing PV's for locations included, as a result of influence on crops: ", total_potential_revenue_after_PV);



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

  writeln("\nSum of z[i][j]: ",sum_of_z)
  writeln("inequality of wealth: Sum of z[i][j] / Sum of y[i] = ",sum_of_z/total_energy_produced_from_y)


  writeln("\nResults for excel output file:")
  writeln("location_id,", "Energy units Produced in mln,", "influence on crops,", "area in dunam used");
  for (var i in fix_energy_production) {
    if (x[i] == 1) {
      writeln(i, ",", fix_energy_production[i] * x[i], ",", influence_on_crops[i] * x[i], ",", area_in_dunam[i] * x[i]);

   }
  }
  writeln("")

}


execute {
    for (var eshkol in Eshkolot) {
      writeln(eshkol); 

    }
}
