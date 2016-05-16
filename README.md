#Software Overview 

This section should give an overview of the research project as a whole. Relevant papers from which this research led to should be cited here with a brief description of each paper. 

What does this repository do? 
How is the repository organized?

##How to Use

This code uses a number of features in the scientific python stack. This repository has been tested and run on the Mac OS X - El Capitan platform.

###Initial Steps
####Grab Conda Package Manager for Python 2.7 (NOT 3.5)
To run code within repository, it is recommended that the user download and install either:
* [Anaconda](https://www.continuum.io/downloads) -- a completely free Python distribution (including for commercial use and redistribution) including more than 300 of the most popular Python packages for science, math, engineering, and data analysis.
* [Miniconda](http://conda.pydata.org/miniconda.html) -- a small “bootstrap” version of Anaconda that includes only conda and conda-build, and installs Python

####Clone Conda Environment
The user should clone the included environment to install all the packages required to replicate code functionality in this repository. Navigate to the base directory for the repository, ensure that the `environment.yml` file is in the directory and run: 
```
conda env create -f environment.yml
```

####Activate the Environment
After cloning the Conda environment, named `codebase`, you must instruct conda to switch to the newly installed environment. To do this, run:
```
source activate cb-nmfsubnet
```
