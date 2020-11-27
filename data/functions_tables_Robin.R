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
