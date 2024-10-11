// Parameters
int num_locations = ...;
int num_yeshuvim = ...;
int num_eshkolot = ...;
float influence_on_crops_lower_limit = ...;
float minimal_total_revenue = ...;
float total_area_upper_bound = ...;
float fix_energy_production[1..num_locations] = ...;
float influence_on_crops[1..num_locations] = ...;
float total_revenue[1..num_locations] = ...;
float area_in_dunam[1..num_locations] = ...;
//float energy_consumption_by_yeshuv = ...;

range Yeshuvim = 1..num_yeshuvim;
float energy_consumption_by_yeshuv[Yeshuvim] = ...;
range Eshkolot = 1..num_eshkolot;
float energy_division_between_eshkolot[Eshkolot] = ...;


// Define sets S_j for each yeshuv j
{int} S[j in Yeshuvim] = ...; // Load sets from .dat file

// Define sets E_k for each eshkol k
{int} E[k in Eshkolot] = ...; // Load sets from .dat file

// Decision Variables
dvar boolean x[1..num_locations]; // binary (boolean) decision variables


// Objective Function
maximize sum(i in 1..num_locations) (fix_energy_production[i] * x[i]);

// Constraints
subject to {



    // Constraint for an upper bound of the total area used by installed PV's
    sum(i in 1..num_locations) (x[i] * area_in_dunam[i]) <= total_area_upper_bound;
	    
    // Constraint for minimal influence on crops after installment of PV's that can be tolerated 
    sum(i in 1..num_locations) (x[i] * influence_on_crops[i]) >= influence_on_crops_lower_limit;
	
    // Constraint for minimal total revenue from installment of PV's
    sum(i in 1..num_locations) (x[i] * total_revenue[i]) >= minimal_total_revenue;



    // Constraint for the total energy production of each yeshuv, upper bounded by the energy consumption of each yeshuv
    
    forall (j in Yeshuvim) {
        sum(i in S[j]) x[i] * fix_energy_production[i] <= energy_consumption_by_yeshuv[j];
    }
    

    // Constraint for the percentage of the total energy production of each eshkol, upper bounded by some fixed percentage
    /*
    forall (k in Eshkolot) {
        sum(i in E[k]) x[i] * fix_energy_production[i] <= energy_division_between_eshkolot[k] * sum(j in 1..num_locations) (fix_energy_production[j] * x[j]);
    }
    */


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
  var total_influence = 0;
  var number_of_installed_PV = 0;
  var Overall_total_revenue = 0;
  var total_area = 0;
  writeln("Installation decisions:");
  for (var i in fix_energy_production) {
    if (x[i] == 1) {
      writeln("Location ", i, ": ", fix_energy_production[i] * x[i], " mln Energy units Produced, influence of ", influence_on_crops[i] * x[i], " on crops, area_in_dunam used: ", area_in_dunam[i] * x[i]);
      total_energy_produced += fix_energy_production[i] * x[i]
      total_influence += influence_on_crops[i]
      number_of_installed_PV += 1
      Overall_total_revenue += total_revenue[i]
      total_area += area_in_dunam[i]

	 }
  }

  writeln("Total energy produced: ", total_energy_produced);
  writeln("Number of installed PV's: ", number_of_installed_PV);
  writeln("Total influence on crops: ", total_influence);
  writeln("Overall total revenue (in mln): ", Overall_total_revenue);
  writeln("total area (in dunam) used: ", total_area);


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

  writeln("\nEnergy produced by eshkol: ")
  for (var eshkol in Eshkolot) {
    var total_energy_produced_by_eshkol = 0
    var eshkol_allowed_energy_production = energy_division_between_eshkolot[eshkol] * total_energy_produced 
    var eshkol_str = "eshkol " + eshkol.toString() + ": " + "allowed energy production: " + eshkol_allowed_energy_production.toString();
    eshkol_str += " ,chosen locations: ["
    for (var loc in E[eshkol])
      if (x[loc] == 1){
        eshkol_str += loc.toString() + ", "
        total_energy_produced_by_eshkol += x[loc]*fix_energy_production[loc]
      }

    if (total_energy_produced_by_eshkol == 0){
      continue
    }

    eshkol_str += "] total energy produced: " + total_energy_produced_by_eshkol.toString();
    writeln(eshkol_str);  
  }
}


execute {
    for (var eshkol in Eshkolot) {
      writeln(eshkol); 

    }
}
