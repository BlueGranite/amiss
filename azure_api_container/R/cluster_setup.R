cores <- 10
it_cl <- makeCluster(cores)

clusterExport(it_cl, c("purrr",
                    "magrittr",
                    "futile.logger",
                    "caret",
                    "ModelMetrics",
                    "foreach",
                    "doParallel",
                    "doRNG",
                    "here"))

registerDoParallel(it_cl, cores)

stopCluster(it_cl)
