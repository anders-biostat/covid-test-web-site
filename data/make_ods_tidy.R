#!/usr/bin/env Rscript
library(tidyverse)
library(readxl)
library(magrittr)
library(httr)
library(jsonlite)

api_url <- 'https://covidtest-hd.de/api/samples/'
auth <- authenticate("fhuber", "pYZf9ty2U8ATaR8")
generic_bag_id <- 246

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

process_file <- function(filename, study_arm = NULL, save = FALSE) {
  if (is.null(study_arm)) {
    study_arm <- str_extract(filename, pattern = "A1|A2|B1|B2")
  }
  tab <- read.table(filename, header = FALSE, sep = ",", na.strings = "")
  tab <- tab[, 1:2]
  tab <- tab[complete.cases(tab), ]
  # study_arm musst be one of A1/A2/B1/B2
  if (study_arm %in% c("A1", "B1")) {
    tab_tidy <- process_arm1(tab)
  } else if (study_arm %in% c("A2", "B2")) {
    tab_tidy <- process_arm2(tab)
  } else {
    stop("Unknown study arm")
  }

  tab_joined <- left_join(tab_tidy, mastertab_tidy)
  stopifnot(nrow(tab_joined) == nrow(tab_tidy) | (!all(complete.cases(tab_joined))))
  
  newname <- str_replace(filename, pattern = "\\.csv", replacement = "_tidy.rds")
  if (save) saveRDS(tab_joined, file = newname)
  
  return(tab_joined)
}

process_arm1 <- function(tab) {
  tab_tidy <- 
    pivot_wider(tab, names_from = V1, values_from = V2) %>% 
    janitor::clean_names() %>% 
    unnest(cols = colnames(.)) %>% 
    dplyr::rename("hh_id" = "haushalts_id", "barcode" = "kit")
  
  return(tab_tidy)
}

process_arm2 <- function(tab) {
  tab_tidy <- 
    pivot_wider(tab, names_from = V1, values_from = V2) %>% 
    janitor::clean_names() %>% 
    unnest(cols = colnames(.)) %>% 
    pivot_longer(cols = a:d, names_to = "letter", values_to = "barcode") %>% 
    mutate(letter = toupper(letter)) %>% 
    rename("hh_id" = "haushalts_id")
  
  return(tab_tidy)
}

files_to_proc <- list.files(path = "./Codes_Stand_20201123", full.names = TRUE, 
  pattern = "\\.csv")

l <- map(files_to_proc, process_file, save = TRUE)
names(l) <- files_to_proc

already_uploaded <- bind_rows(foo, bar)

to_upload <- bind_rows(l) %>% anti_join(already_uploaded)

to_upload_post_responses <-
  map2(to_upload$barcode, to_upload$access_code, function(bc, ac) {
    r <- POST(url = api_url, config = auth,
      body = list(barcode = bc, access_code = ac, bag = generic_bag_id))
    return(list(response = r, status_code = r$status_code))
  })

status_codes <- map_chr(to_upload_post_responses, "status_code")
nrow(to_upload)
length(to_upload_post_responses)
sum(status_codes == "201")

View(to_upload_post_responses[status_codes != "201"])
to_upload[status_codes != "201", ]

to_upload[to_upload$hh_id %in% c("2920", "4594"), ]

saveRDS(file = "to_upload_post_responses.rds", object = to_upload_post_responses)


# saveRDS(file = "new_res_A2_post_responses.rds", object = to_upload2_post_responses)






