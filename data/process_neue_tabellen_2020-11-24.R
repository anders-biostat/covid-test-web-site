#!/usr/bin/env Rscript

# Process files that are in folder "Neue_Tabellen_2020-11-24". 
# They were provided by Robin on 2020-11-24 and contain samples scanned on that 
# day before the SCANSCRIPT was in operation

library(tidyverse)
library(readxl)
library(magrittr)
library(httr)
library(jsonlite)

indir <- "./Neue_Tabellen_2020-11-24"

mastertab_tidy <- readRDS("mastertab.rds")

files_to_proc <- list.files(path = indir, full.names = TRUE, pattern = "\\.csv")
l <- map(files_to_proc, process_file, save = TRUE)
names(l) <- files_to_proc

# this file contains all samples that have been registered (both access codes and 
# events up to and including 2020-11-23)
already_uploaded <- readRDS("uploaded_by_2020-11-23.rds")
to_upload_20201124 <- bind_rows(l) %>% anti_join(already_uploaded)
to_upload_20201124

# register access_code barcode pairs
to_upload_ac_bc_responses <-
  map2(to_upload_20201124$barcode, to_upload_20201124$access_code, function(bc, ac) {
    r <- POST(url = api_url, config = auth,
      body = list(barcode = bc, access_code = ac, bag = generic_bag_id))
    return(list(response = r, status_code = r$status_code))
  })

status_codes <- map_chr(to_upload_ac_bc_responses, "status_code")
sum(status_codes == "201")
sum(status_codes != "201")

# register event "kit_packed"
to_upload_event_responses <- 
  map(to_upload_20201124$access_code, function(ac) {
    POST(url = event_api, config = auth, body = list(access_code = ac))
  })

status_codes <- map_chr(to_upload_event_responses, "status_code")
sum(status_codes == "201")
sum(status_codes != "201")
