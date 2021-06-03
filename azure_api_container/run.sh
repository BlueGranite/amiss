#!/bin/bash

# set -e

echo AMISS_SESSION_ID
echo AMISS_SESSION_DIR
echo AMISS_VCF_FILENAME
echo AMISS_CADD_SNV_FILENAME
echo AMISS_CADD_INDEL_FILENAME

Rscript /app/amiss/R/01_parse_vcf.R 2>&1 | tee ${AMISS_SESSION_DIR}/step_01.log