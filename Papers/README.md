#Guide to Running 

##Retrieve Data
* [__download_data__](./download_data.ipynb)  ([nbviewer](http://nbviewer.ipython.org/github/theandygross/TCGA/blob/master/Analysis_Notebooks/download_data.ipynb))
  Pulls all of the necessary data from the net and constructs the file tree and data objects used in the rest of the analysis. 

##Global Pre-Processing
(There are dependencies among these, run them in order.)
* [__HPV_Process_Data__](./HPV_Process_Data.ipynb)  ([nbviewer](http://nbviewer.ipython.org/github/theandygross/TCGA/blob/master/Analysis_Notebooks/HPV_Process_Data.ipynb)) 
  Compile HPV status for all patient tumors.  
  Calculate global variables and meta features in the HPV- background. 

##Analysis for Paper --

#Pre-Processing
* [__UPMC_cohort__](./UPMC_cohort.ipynb)  ([nbviewer](http://nbviewer.ipython.org/github/theandygross/TCGA/blob/master/Analysis_Notebooks/UPMC_cohort.ipynb)) 
  Validation of primary findings in independent patient cohort from University of Pittsburgh ([Stansky et al.](http://www.sciencemag.org/content/333/6046/1157.full)).
  

#Analysis
* [__Molecular_Validation__](./Molecular_Validation.ipynb)  ([nbviewer](http://nbviewer.ipython.org/github/theandygross/TCGA/blob/master/Analysis_Notebooks/Molecular_Validation.ipynb)) 
Validation of molecular associations in recent TCGA samples.
