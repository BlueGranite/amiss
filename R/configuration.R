library(rjson)

get_config <- function (filename) {
  config <- readLines(filename)
  return(fromJSON(config))
}

generate_parameter_combination <- function(parameter_grid) {
  params = list()
  for (name in names(parameter_grid)) {
    params[[name]] <- sample(parameter_grid[[name]], size = 1)
  }
  return(params)
}

write_config <- function(config_list, filename) {
  json_config <- toJSON(config_list)
  writeLines(json_config, con = filename)
}