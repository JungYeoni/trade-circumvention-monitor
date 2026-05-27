***Figure 1 uses monthly trade data to plot exports of EU/UK to Russia and Central Asia split by sanctions category


use "$CLEANDATA/monthly_trade_data.dta", clear
drop if yofd(dofm(month)) == 2024
keep if partner == "Russian Federation"
keep if reporter == "EU-28" | reporter == "United Kingdom"
collapse (sum) primaryvalue qty, by( Code month)

merge m:1 Code using "$RAWDATA/EU_sanctions_HS6.dta"
keep if _merge ==3
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

export excel using "$FIGURES/Figure 1.xlsx", sheet("EU Russia") sheetmodify firstrow(varlabels) keepcellfmt

clear
use "$CLEANDATA/monthly_trade_data.dta", clear
drop if yofd(dofm(month)) == 2024
keep if partner == "Armenia" | partner == "Kazakhstan" | partner == "Kyrgyzstan" 
keep if reporter == "EU-28" | reporter == "United Kingdom"
collapse (sum) primaryvalue qty, by( Code month)

merge m:1 Code using "C:\Users\chupilkm\EBRD\OCE - Russia trade\EU_sanctions_HS6.dta"
keep if _merge ==3
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

export excel using "$FIGURES/Figure 1.xlsx", sheet("EU CCA3") sheetmodify firstrow(varlabels) keepcellfmt