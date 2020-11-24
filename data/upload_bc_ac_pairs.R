#!/usr/bin/env Rscript

library(tidyverse)
library(httr)
library(jsonlite)

### RUN ON 2020-11-23
to_upload <- "new_res_A1.rds"
(to_upload <- readRDS(file = to_upload))

api_url <- 'https://covidtest-hd.de/api/samples/'
auth <- authenticate("fhuber", "pYZf9ty2U8ATaR8")
generic_bag_id <- 246

# to_upload_get_responses <- 
#   map(to_upload$barcode, function(bc) {
#     r <- GET(url = api_url, config = auth, query = list(barcode = bc))
#     return(list(response = r, content = content(r), status_code = r$status_code))
#   })
# 
# map(to_upload_get_responses, "content")

bc <- to_upload$barcode
ac <- to_upload$access_code
POST(url = api_url, config = auth,
  body = list(barcode = bc, access_code = ac, bag = generic_bag_id))

to_upload_post_responses <-
  map2(to_upload$barcode, to_upload$access_code, function(bc, ac) {
    r <- POST(url = api_url, config = auth,
      body = list(barcode = bc, access_code = ac, bag = generic_bag_id))
    return(list(response = r, status_code = r$status_code))
})
saveRDS(file = "new_res_A1_post_responses.rds", object = to_upload_post_responses)

to_upload_post_responses

map_chr(to_upload_post_responses, "status_code")

# foo <- GET(url = api_url, config = auth, query = list(barcode = to_upload$barcode[1]))
# content(foo)

# bc <- to_upload$barcode[2]
# ac <- to_upload$access_code[2]

to_upload2 <- "new_res_A2.rds"
(to_upload2 <- readRDS(file = to_upload2))

to_upload2_post_responses <-
  map2(to_upload2$barcode, to_upload2$access_code, function(bc, ac) {
    r <- POST(url = api_url, config = auth,
      body = list(barcode = bc, access_code = ac, bag = generic_bag_id))
    return(list(response = r, status_code = r$status_code))
  })
saveRDS(file = "new_res_A2_post_responses.rds", object = to_upload2_post_responses)

to_upload2_post_responses

stopifnot(all(map_chr(to_upload2_post_responses, "status_code") == "201"))

