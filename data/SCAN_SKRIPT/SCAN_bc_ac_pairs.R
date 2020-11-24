#!/usr/bin/env Rscript

ipak <- function(pkg){
  suppressMessages(suppressWarnings({
    pkg = as.character(substitute(pkg))
    new.pkg <- pkg[!(pkg %in% installed.packages()[, "Package"])]
    if (length(new.pkg))
      install.packages(new.pkg, dependencies = TRUE)
    invisible(sapply(pkg, require, character.only = TRUE))
  }))
}

readline_shell <- function(display_text) {
  cat(display_text)
  var <- readLines(con = "stdin", n = 1)
  return(var)
}

generic_bag_id <- 246

ipak(tidyverse)
ipak(httr)
ipak(jsonlite)

mastertab <- readRDS("mastertab.rds")
api_url <- "https://covidtest-hd.de/api/samples/"
event_api <- "https://virusfinder.de/en/add_kit_packed_event"
# api_url <- "localhost:8000"
auth = authenticate("packstation", "p3c75z2x8")

while (TRUE) {
  hh_id <- readline_shell("Please scan household ID: ")
  hh_id <- str_replace(hh_id, pattern = "^0{1,4}", replacement = "")
  subtab <- mastertab[mastertab$hh_id == hh_id, ]
  cat("Household ID: ", hh_id, " with ", unique(subtab$nachname_vorname), "\n")

  subtab$barcode <- NA
  
  if (nrow(subtab) == 1) {
    bc <- readline_shell("Please scan tube barcode: ")
    subtab$barcode <- bc
  } else if (nrow(subtab) == 4) {
    for (l in subtab$letter) {
      bc <- readline_shell(paste("Please scan tube barcode for tube", l, ": "))
      subtab$barcode[subtab$letter == l] <- bc
    }
  } else {
    stop("Something went wrong: there are ", nrow(subtab), " access codes associated with this household")
  }
  
  for (r in seq_len(nrow(subtab))) {
    ac <- subtab$access_code[r]
    bc <- subtab$barcode[r]
    
    # register barcode-access_code pair with covidtest server
    r <- POST(url = api_url, config = auth, 
      body = list(barcode = bc, access_code = ac, bag = generic_bag_id))
    if (r$status_code != 201) {
	  cat("Error registering barcode:\n")
      print(content(r))
      stop()
    }

    # change status on bfast-web-server
    r2 <- POST(url = event_api, config = auth, 
    	body = list(access_code = ac))
    if (r2$status_code != 201) {
	    cat("Error registering event\n")
	    print(content(r2))
	    stop()
    }
  }
  rm(subtab)
  cat("\n")
  yn <- readline_shell("Do you want to continue (y/n)? \n")
  if (yn == "n") stop("Thank you and goodbye :)")
  cat("\n\n")
}





