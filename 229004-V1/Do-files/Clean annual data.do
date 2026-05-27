***********************************Dataset on annual exports from the EU/UK*****************************************
import delimited "$RAWDATA/full_annual_exports.csv", numericcols(5 6 7 8 13 16 22 33 45) clear
keep if partner2code == 0
keep refyear refmonth period reportercode partnercode cmdcode primaryvalue qty

**merges with country names 
merge m:1 reportercode using "$RAWDATA/COMTRADE reporters.dta"
drop if _merge ==2
drop _merge

merge m:1 partnercode using "$RAWDATA/COMTRADE partners.dta"
drop if _merge ==2
drop _merge

***cmdcode stands for HS6 code. HS6 codes that start with 0 do not import correctly and need to have 0 added in the beginning.
tostring cmdcode, replace
replace cmdcode = "0" + cmdcode if strlen(cmdcode) == 5
rename cmdcode Code
replace reporter = "Italy" if reportercode == 380

save "$WORKDATA/Lost in transit exports annual.dta", replace

***********************************Dataset on annual imports from the EU/UK*****************************************
clear
import delimited "$RAWDATA/full_annual_imports.csv", numericcols(5 6 7 8 13 16 22 33 45) clear
keep if partner2code == 0
keep refyear refmonth period reportercode partnercode cmdcode primaryvalue qty

**merges with country names
merge m:1 reportercode using "$RAWDATA/COMTRADE reporters.dta"
drop if _merge ==2
drop _merge

merge m:1 partnercode using "$RAWDATA/COMTRADE partners.dta"
drop if _merge ==2
drop _merge

***cmdcode stands for HS6 code. HS6 codes that statr with 0 do not import correctly and need to have 0 added in the beginning.
tostring cmdcode, replace
replace cmdcode = "0" + cmdcode if strlen(cmdcode) == 5
rename cmdcode Code
replace partner = "Italy" if partnercode == 380

save "$WORKDATA/Lost in transit imports annual.dta", replace



***This part of the code creates a lost in transit dataset from a combination of exports reported by the EU/UK and imports reported by importers. 

***These codes aggregate reported imports and exports by exporter-importer-product-year


clear
use "$WORKDATA/Lost in transit exports annual.dta"
rename reporter exporter_side
rename partner importer_side
rename primaryvalue primaryvalue_exporter
rename qty qty_exporter
keep exporter_side importer_side  Code primaryvalue_exporter qty_exporter refyear
collapse (sum) primaryvalue_exporter qty_exporter, by(refyear exporter_side importer_side Code)

save "$WORKDATA/Lost in transit exports temp.dta", replace

clear
use "$WORKDATA/Lost in transit imports annual.dta"
rename reporter importer_side
rename partner exporter_side
rename primaryvalue primaryvalue_importer
rename qty qty_importer
keep exporter_side importer_side  Code primaryvalue_importer qty_importer refyear
collapse (sum) primaryvalue_importer qty_importer, by(refyear exporter_side importer_side Code)

save "$WORKDATA/Lost in transit imports temp.dta", replace

***This code merges the two

clear 
use "$WORKDATA/Lost in transit exports temp.dta"
merge 1:1 exporter_side importer_side refyear Code using "$WORKDATA/Lost in transit imports temp.dta"
drop if importer_side == "World"
drop if exporter_side == "World"
drop _merge

***This part of the code drops those observations where there is no trade reported by one of the reporters in the country pair. it is needed as we need to drop observations where no trade has been reported completely, while keeping observations for products where one country repored trade and another reported 0.

preserve
collapse primaryvalue_importer primaryvalue_exporter, by( exporter_side importer_side refyear)
gen a = 1 if primaryvalue_importer ==. | primaryvalue_exporter ==.
collapse a, by(exporter_side importer_side refyear)
save "$WORKDATA/Lost in transit merge temp.dta", replace
restore

merge m:1  exporter_side importer_side refyear using "$WORKDATA/Lost in transit merge temp.dta"
drop if a ==1
drop a _merge

replace primaryvalue_exporter = 0 if primaryvalue_exporter ==.
replace qty_exporter = 0 if qty_exporter ==.
replace primaryvalue_importer = 0 if primaryvalue_importer ==.
replace qty_importer = 0 if qty_importer ==.

save "$CLEANDATA/Lost in transit annual.dta", replace