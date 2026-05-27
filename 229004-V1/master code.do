clear all
set more off

*Set directories
foreach path in "INPUT YOUR PATH HERE"  {
	capture cd "`path'"
		if _rc == 0 macro def PROJ "`path'"
	}
	
global CODE = "$PROJ/Do-files"
global FIGURES = "$PROJ/Figures"
global RAWDATA = "$PROJ/Raw-data"
global CLEANDATA = "$PROJ/Clean-data"
global WORKDATA = "$PROJ/Working-data"

**Run do files

*Create clean datasets
do "$CODE/Clean monthly data.do"
do "$CODE/Clean annual data.do"

*Do figures
do "$CODE/Figure 1.do"
do "$CODE/Figure 2.do"
do "$CODE/Figure 3.do"