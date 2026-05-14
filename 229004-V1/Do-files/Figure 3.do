***Figure 3 calculates log ratios of reported imports to reported export by importer-product-year and takes medians

***First, the code calculates numbers for CCA3

clear
use "$CLEANDATA/Lost in transit annual.dta", clear
keep if importer_side == "Armenia"|importer_side == "Kazakhstan"|importer_side == "Kyrgyzstan"
collapse (sum) primaryvalue_exporter qty_exporter primaryvalue_importer qty_importer, by(importer_side refyear Code)


replace primaryvalue_exporter = 0 if primaryvalue_exporter ==.
replace qty_exporter = 0 if qty_exporter ==.
replace primaryvalue_importer = 0 if primaryvalue_importer ==.
replace qty_importer = 0 if qty_importer ==.

gen ratio = primaryvalue_importer/primaryvalue_exporter
gen log_ratio = log(ratio)

merge m:1 Code using "$RAWDATA/EU_sanctions_HS6.dta"
drop if _merge == 1 | _merge ==2
drop _merge

replace EU_sanction = 0 if EU_sanction ==.
gen sanction_type = 0
replace sanction_type = 1 if luxury ==1
replace sanction_type = 2 if aviation ==1 | industrial_cap ==1 | oil_exploration ==1 | oil_refining ==1
replace sanction_type = 3 if dual_use ==1 | firearms ==1 | military_tech ==1

collapse (p50) log_ratio, by( refyear sanction_type)
reshape wide log_ratio, i(refyear) j(sanction_type)

label variable log_ratio0 "CCA3, Not sanctioned"
label variable log_ratio1 "CCA3, Luxury"
label variable log_ratio2 "CCA3, Industrial"
label variable log_ratio3 "CCA3, Dual-use"

export excel using "$FIGURES/Figure 3.xlsx", sheet("Data") sheetmodify firstrow(varlabels) keepcellfmt

***Same for other land borders but without split by product type

clear
use "$CLEANDATA/Lost in transit annual.dta", clear
keep if importer_side == "Azerbaijan" | importer_side == "Belarus" | importer_side == "China" | importer_side == "Mongolia" | importer_side == "Georgia"  | importer_side == "Uzbekistan" | importer_side == "Tajikistan" | importer_side == "Turkmenistan"
collapse (sum) primaryvalue_exporter qty_exporter primaryvalue_importer qty_importer, by(importer_side refyear Code)


replace primaryvalue_exporter = 0 if primaryvalue_exporter ==.
replace qty_exporter = 0 if qty_exporter ==.
replace primaryvalue_importer = 0 if primaryvalue_importer ==.
replace qty_importer = 0 if qty_importer ==.

gen ratio = primaryvalue_importer/primaryvalue_exporter
gen log_ratio = log(ratio)

collapse (p50) log_ratio, by( refyear)

label variable log_ratio "Other land borders"

drop refyear

export excel using "$FIGURES/Figure 3.xlsx", sheet("Data") sheetmodify cell(F1) firstrow(varlabels) keepcellfmt

***Same for rest of the world

use "$CLEANDATA/Lost in transit annual.dta", clear
drop if importer_side == "Armenia"|importer_side == "Kazakhstan"|importer_side == "Kyrgyzstan"|importer_side == "Azerbaijan" | importer_side == "Belarus" | importer_side == "China" | importer_side == "Mongolia" | importer_side == "Georgia"  | importer_side == "Uzbekistan" | importer_side == "Tajikistan" | importer_side == "Turkmenistan"
collapse (sum) primaryvalue_exporter qty_exporter primaryvalue_importer qty_importer, by(importer_side refyear Code)


replace primaryvalue_exporter = 0 if primaryvalue_exporter ==.
replace qty_exporter = 0 if qty_exporter ==.
replace primaryvalue_importer = 0 if primaryvalue_importer ==.
replace qty_importer = 0 if qty_importer ==.

gen ratio = primaryvalue_importer/primaryvalue_exporter
gen log_ratio = log(ratio)

collapse (p50) log_ratio, by( refyear)

label variable log_ratio "Rest of the world"

drop refyear

export excel using "$FIGURES/Figure 3.xlsx", sheet("Data") sheetmodify cell(G1) firstrow(varlabels) keepcellfmt