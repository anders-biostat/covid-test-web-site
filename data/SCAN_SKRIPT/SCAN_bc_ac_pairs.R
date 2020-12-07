#!/usr/bin/env Rscript

# add option to run script in repair mode:
args <- commandArgs(trailingOnly = TRUE)
repair_mode <- FALSE
if (length(args) == 1 & (args[1] == "--repair")) {
  cat("--Script launching in repair mode, which allows to skip tubes when scanning--\n")
  repair_mode <- TRUE
}

ipak <- function(pkg){
  suppressMessages(suppressWarnings({
    pkg = as.character(substitute(pkg))
    new.pkg <- pkg[!(pkg %in% installed.packages()[, "Package"])]
    if (length(new.pkg))
      install.packages(new.pkg, dependencies = TRUE)
    invisible(sapply(pkg, require, character.only = TRUE))
  }))
}

# This function is necessary because otherwise the interactive prompt will not work 
# when run from bash
# Note: does not work from within RStudio
readline_shell <- function(display_text) {
  cat(display_text)
  var <- readLines(con = "stdin", n = 1)
  return(var)
}

check_response_status <- function(response, expected_status, error_message) {
  if (response$status_code == 504) {
    cat("\nERROR: the server seems to be down. Script will exit. Please try again in a few minutes.\nCall Simon Anders if problem persists.")
  }
  if (response$status_code != expected_status) {
    cat("\n", error_message)
    print(content(response))
    stop()
  }
}


ipak(tidyverse)
ipak(httr)
ipak(jsonlite)

mastertab <- readRDS("mastertab.rds")
api_url_samples <- "https://covidtest-hd.de/api/samples/"
api_url_events_covidtest <- "https://covidtest-hd.de/api/events/"
api_url_events_packed <- "https://virusfinder.de/en/add_kit_packed_event"
auth = authenticate("packstation", "p3c75z2x8")
generic_bag_id <- 246

# for testing purposes
# source("./config_for_testing.R)

get_fmtd_tstmp <- function() {
  tstmp <- str_replace_all(Sys.time(), pattern = "\\s", replacement = "_")
  tstmp <- str_replace_all(tstmp, pattern = ":", replacement = ".")
  return(tstmp)
}

# in script below close connection to file before exiting
run_script <- function() {
  has_started <- FALSE
  while (TRUE) {
    # When script is started, ask for a batch number and open a file
    if (!has_started) {
      batch_num <- readline_shell("Please enter a batch number: ")
      tstmp_file <- get_fmtd_tstmp()
      con <- file(description = paste0("Log_", tstmp_file, ".csv"), open = "w")
      # Beginning of a csv file with the right column names
      writeLines(c("hh_id,", "access_code,", "barcode,", "batch,", "timestamp\n"), con = con, sep = "")
      has_started <- TRUE
    }
    on.exit(close(con))

    # extract subtable from master table based on household ID
    hh_id <- readline_shell("Please scan household ID: ")
    hh_id <- str_replace(hh_id, pattern = "^0{1,4}", replacement = "")
    subtab <- mastertab[mastertab$hh_id == hh_id, ]
    
    # Check if there are 1 or 4 access codes - if so, register them, else abort
    if (!(nrow(subtab) %in% c(1, 4))) {
      stop("Something went wrong: there are ", nrow(subtab), " access codes associated with this household.")
    }
    
    cat("Household ID:", hh_id, " with", unique(subtab$nachname_vorname), "\n")
    
    subtab$barcode <- NA
    for (r in seq_len(nrow(subtab))) {
      if (nrow(subtab) == 1) {
        bc <- readline_shell("Please scan tube barcode: ")
      } else {
        l <- subtab$letter[r]
        if (repair_mode) {
          yn <- ""
          while (!(yn %in% c("yes", "no"))) {
            if (yn != "") cat("Please type either yes or no.\n")
            yn <- readline_shell(paste("Do you want to skip tube ", l, "for this household? ('yes'/'no')\n"))
          }
          if (yn == "yes") next
        }
        bc <- readline_shell(paste("Please scan tube barcode for tube", l, ": "))
      }
      ac <- subtab$access_code[r]
      
      # register barcode-access_code pair with covidtest server
      r <- POST(url = api_url_samples, config = auth,
        body = list(barcode = bc, access_code = ac, bag = generic_bag_id))
      check_response_status(r, 201, "ERROR REGISTERING BARCODE. Response returned:\n")
      sample_id <- content(r)$id
      
      # sample should be id of the sample: parse the response with content and get it
      # e.g. https://covidtest-hd.de/admin/app/sample/150574/
      # change status on covid server so that it's not marked as "imported from read_registrations_file"
      printed <- POST(url = api_url_events_covidtest, config = auth,
        body = list(sample = sample_id, status = "PRINTED", comment = "Scanned with script by Packstation"))
      check_response_status(printed, 201, "ERROR REGISTERING EVENT 'PRINTED' WITH COVID-TEST:\n")
      
      # change status on bfast-web-server
      r2 <- POST(url = api_url_events_packed, config = auth, body = list(access_code = ac))
      check_response_status(r, 201, "Error registering event 'kit_packed':\n")
      
      # if everything worked, append to csv file:
      writeLines(c(hh_id, ",", ac, ",", bc, ",", batch_num, ",", paste0(get_fmtd_tstmp(), "\n")), con = con, sep = "")
    }
    
    rm(subtab, hh_id, ac, bc)
    flush(con)

    yn <- readline_shell("\nPress enter to continue or type 'q' to quit.\n")
    if (yn == "q") {
      message("Thank you and goodbye :)\n")
      quit('no')
    }
    cat("\n")
  }
}

run_script()

