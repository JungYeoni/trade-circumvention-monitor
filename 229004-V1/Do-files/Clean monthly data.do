***********************************Dataset on monthly exports from EU/UK*****************************************

clear
import delimited "$RAWDATA/monthly_trade_data.csv"
keep if partner2code == 0
drop if refyear == 2024
keep refyear refmonth period reportercode partnercode cmdcode primaryvalue qty

**merges with country names 
merge m:1 reportercode using "$RAWDATA/COMTRADE reporters.dta"
drop if _merge ==2
drop _merge

merge m:1 partnercode using "$RAWDATA/COMTRADE partners.dta"
drop if _merge ==2
drop _merge

replace reporter = "Italy" if reportercode == 380

gen month = monthly(string( refyear) + "-" + string( refmonth) , "YM")
format month %tm

***cmdcode stands for HS6 code. HS6 codes that statr with 0 do not import correctly and need to have 0 added in the beginning.

tostring cmdcode, replace
replace cmdcode = "0" + cmdcode if strlen(cmdcode) == 5
rename cmdcode Code

save "$CLEANDATA/monthly_trade_data.dta", replace

***********************************Same for the dataset on CCA3 exports to Russia*****************************************

clear
import delimited "$RAWDATA/CCA3 exports.csv"
keep if partner2code == 0
drop if refyear == 2024
keep refyear refmonth period reportercode partnercode cmdcode primaryvalue qty

**merges with country names 
merge m:1 reportercode using "$RAWDATA/COMTRADE reporters.dta"
drop if _merge ==2
drop _merge

merge m:1 partnercode using "$RAWDATA/COMTRADE partners.dta"
drop if _merge ==2
drop _merge

replace reporter = "Italy" if reportercode == 380

gen month = monthly(string( refyear) + "-" + string( refmonth) , "YM")
format month %tm

***cmdcode stands for HS6 code. HS6 codes that start with 0 do not import correctly and need to have 0 added in the beginning.

tostring cmdcode, replace
replace cmdcode = "0" + cmdcode if strlen(cmdcode) == 5
rename cmdcode Code

save "$CLEANDATA/CCA3 exports.dta", replace
