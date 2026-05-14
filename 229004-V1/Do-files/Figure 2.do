***Figure 2 uses monthly trade data to plot exports of CCA3 to Russia split by sanctions category

clear
use "C:\Users\chupilkm\EBRD\OCE - Russia trade\trade data\CCA3 exports.dta"

gen month = monthly(string( refyear) + "-" + string( refmonth) , "YM")
format month %tm


drop if reporter == "Georgia"
keep if partner == "Russian Federation"
collapse (sum) primaryvalue qty, by( Code month)

merge m:1 Code using "C:\Users\chupilkm\EBRD\OCE - Russia trade\EU_sanctions_HS6.dta"
drop if _merge == 1 | _merge ==2
drop _merge

replace EU_sanction = 0 if EU_sanction ==.
gen sanction_type = 0
replace sanction_type = 1 if luxury ==1
replace sanction_type = 2 if aviation ==1 | industrial_cap ==1 | oil_exploration ==1 | oil_refining ==1
replace sanction_type = 3 if dual_use ==1 | firearms ==1 | military_tech ==1


collapse (sum) primaryvalue, by( sanction_type month)
replace primaryvalue = primaryvalue/1000000000
reshape wide primaryvalue, i(month) j(sanction_type)

label variable primaryvalue0 "Not sanctioned"
label variable primaryvalue1 "Luxury"
label variable primaryvalue2 "Industrial"
label variable primaryvalue3 "Dual-use"

export excel using "$FIGURES/Figure 2.xlsx", sheet("CCA3 Russia") sheetmodify firstrow(varlabels) keepcellfmt