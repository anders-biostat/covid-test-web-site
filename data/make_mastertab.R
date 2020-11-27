library(tidyverse)

# MASTERTABLE: links HH_ID and access codes:
masterfile <- "BFAST_master_DS_20201115__frozen.csv"
(mastertab <- read_delim(masterfile, delim = ";", 
  col_types = cols(
    .default = col_character(),
    PLZ = col_double(),
    ORTSTEIL = col_logical(),
    HH_ID = col_double(), 
    HNR = col_double(),
    age = col_double(),
    week = col_double(),
    day = col_double(),
    sex = col_double(),
    weight = col_logical()
  )))

my_cols <- c("ZugangsCode_A", "ZugangsCodeHH_B", "ZugangsCodeHH_C", "ZugangsCodeHH_D")
mastertab[, my_cols] <- map_dfc(mastertab[, my_cols], function(col) {
  col <- str_replace_all(col, pattern = " ", replacement = "")
  return(col)
})
mastertab$HH_ID %<>% as.character()
mastertab$nachname_vorname <- paste0(mastertab$NACHNAME, "_", mastertab$VORNAME)
# make tidy
(mastertab_tidy <- mastertab[, c("HH_ID", "nachname_vorname", "arm", my_cols)])
colnames(mastertab_tidy) <- c("hh_id", "nachname_vorname", "arm", "A", "B", "C", "D")
mastertab_tidy <- pivot_longer(mastertab_tidy, cols = A:D, 
  names_to = "letter", values_to = "access_code", 
  values_drop_na = TRUE)

saveRDS(object = mastertab_tidy, file = "mastertab.rds")


