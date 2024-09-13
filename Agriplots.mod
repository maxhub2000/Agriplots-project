// Parameters
int num_locations = ...;
int num_cities = ...;
int num_eshkolot = ...;
float influence_on_crops_lower_limit = ...;
float minimal_total_revenue = ...;
float total_area_upper_bound = ...;
float fix_energy_production[1..num_locations] = ...;
float influence_on_crops[1..num_locations] = ...;
float total_revenue[1..num_locations] = ...;
float area_in_dunam[1..num_locations] = ...;
//float energy_consumption_by_yeshuv = ...;

range Cities = 1..num_cities;
float energy_consumption_by_yeshuv[Cities] = ...;
range Eshkolot = 1..num_eshkolot;
float energy_division_between_eshkolot[Eshkolot] = ...;


// Define sets S_j for each city j
{int} S[j in Cities] = ...; // Load sets from .dat file

// Define sets E_j for each eshkol j
{int} E[j in Eshkolot] = ...; // Load sets from .dat file

// Decision Variables
dvar boolean X[1..num_locations]; // binary (boolean) decision variables


// Objective Function
maximize sum(j in 1..num_locations) (fix_energy_production[j] * X[j]);

// Constraints
subject to {


    forall (j in Cities) {
        sum(i in S[j]) X[i] * fix_energy_production[i] <= energy_consumption_by_yeshuv[j];
    }


    forall (j in Eshkolot) {
        sum(i in E[j]) X[i] * fix_energy_production[i] <= energy_division_between_eshkolot[j] * sum(j in 1..num_locations) (fix_energy_production[j] * X[j]);
    }


    // Constraint for an upper bound of the total area used by installed PV's
    sum(j in 1..num_locations) (X[j] * area_in_dunam[j]) <= total_area_upper_bound;
	    
    // Constraint for minimal influence on crops after installment of PV's that can be tolerated 
    sum(j in 1..num_locations) (X[j] * influence_on_crops[j]) >= influence_on_crops_lower_limit;
	
    // Constraint for minimal total revenue from installment of PV's
    sum(j in 1..num_locations) (X[j] * total_revenue[j]) >= minimal_total_revenue;

}

// Execute block to set the CPLEX time limit
execute {
    writeln("Setting time limit to 60 seconds");
    cplex.tilim = 60; // Set the time limit to 60 seconds
}



execute {
  var total_energy_produced = 0;
  for (var j in fix_energy_production) {
    total_energy_produced += fix_energy_production[j] * X[j];
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
  for (var j in fix_energy_production) {
    if (X[j] == 1) {
      writeln("Location ", j, ": ", fix_energy_production[j] * X[j], " mln Energy units Produced, influence of ", influence_on_crops[j] * X[j], " on crops, area_in_dunam used: ", area_in_dunam[j] * X[j]);
      total_energy_produced += fix_energy_production[j] * X[j]
      total_influence += influence_on_crops[j]
      number_of_installed_PV += 1
      Overall_total_revenue += total_revenue[j]
      total_area += area_in_dunam[j]

	 }
  }

  writeln("Total energy produced: ", total_energy_produced);
  writeln("Number of installed PV's: ", number_of_installed_PV);
  writeln("Total influence on crops: ", total_influence);
  writeln("Overall total revenue (in mln): ", Overall_total_revenue);
  writeln("total area (in dunam) used: ", total_area);





  writeln("\nEnergy produced by city: ")
  for (var city in Cities) {
    var total_energy_produced_by_city = 0
    var city_str = "city " + city.toString() + ": " + "allowed energy production: " + energy_consumption_by_yeshuv[city].toString();
    city_str += " ,chosen locations: ["
    for (var loc in S[city])
      if (X[loc] == 1){
        city_str += loc.toString() + ", "
        total_energy_produced_by_city += X[loc]*fix_energy_production[loc]
      }

    if (total_energy_produced_by_city == 0){
      continue
    }

    city_str += "] total energy produced: " + total_energy_produced_by_city.toString();
    writeln(city_str);  
  }







  writeln("\nEnergy produced by eshkol: ")
  for (var eshkol in Eshkolot) {
    var total_energy_produced_by_eshkol = 0
    var eshkol_allowed_energy_production = energy_division_between_eshkolot[eshkol] * total_energy_produced 
    var eshkol_str = "eshkol " + eshkol.toString() + ": " + "allowed energy production: " + eshkol_allowed_energy_production.toString();
    eshkol_str += " ,chosen locations: ["
    for (var loc in E[eshkol])
      if (X[loc] == 1){
        eshkol_str += loc.toString() + ", "
        total_energy_produced_by_eshkol += X[loc]*fix_energy_production[loc]
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
