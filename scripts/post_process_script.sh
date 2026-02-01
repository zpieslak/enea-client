#!/bin/bash

inputs=("$@")
output_dir="$ENEA_CLIENT_POST_PROCESS_HOME_ASSISTANT_CONFIG_DIR"
output_file="$ENEA_CLIENT_POST_PROCESS_OUTPUT_PATH"

# Clear the output file and write header once
echo "statistic_id,unit,start,delta" > "$output_dir/$output_file"

# Prepare the CSV file for Home Assistant import
for input in "${inputs[@]}"; do
  awk -F';' '
  BEGIN {
    OFS=","
  }

  NR==1 { next }

  {
    gsub(/"/, "")
    split($1, a, /[- :]/)
    start = a[1] "-" a[2] "-" a[3] " " a[4] ":00"

    print "sensor.grid_import_energy","kWh",start,$4
    print "sensor.grid_export_energy","kWh",start,$5
  }
  ' "$input" >> "$output_dir/$output_file"
done

# Run the curl command to import the processed CSV file into Home Assistant
curl -X POST \
   -H "Authorization: Bearer $ENEA_CLIENT_POST_PROCESS_HOME_ASSISTANT_TOKEN" \
   -H "Content-Type: application/json" \
   http://localhost:8123/api/services/import_statistics/import_from_file \
   -d '{
    "filename": "'"$output_file"'",
    "timezone_identifier": "Europe/Warsaw",
    "delimiter": ",",
    "decimal": false,
    "datetime_format": "%Y-%m-%d %H:%M",
    "unit_from_entity": false
  }'
