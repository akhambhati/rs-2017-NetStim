#Codebase

This folder contains main and supporting functions used by the analysis notebooks.

##Guidelines:
* Functions should be recyclable: arguments should be individual/groups of subjects; specific datasets, and every free parameter of the analyses
* Modular structure: several small functions >> one huge function
* Output a lot of information for the user on the screen
* Save all the relevant variables as output; remove any irrelevant variables (e.g. counters) from output
* Should perform error checking on each of the inputs
* If analyses are very long, can save partial data and/or include a progress bar (important if analyses are very long)
* Should save version info in an output file (for later reference, so we know what version of this script generated a given output)

##Generalization
* Collection of functions should be compiled into a toolbox
