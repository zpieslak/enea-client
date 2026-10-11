#!/bin/bash

set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
inputs=("$@")
output_dir="$ENEA_CLIENT_POST_PROCESS_HOME_ASSISTANT_CONFIG_DIR"
output_file="$ENEA_CLIENT_POST_PROCESS_OUTPUT_PATH"

# Clear the output file and write header once
echo "statistic_id,unit,start,delta" > "$output_dir/$output_file"

# Sanitize raw CSV data without modifying the downloaded files, then convert it.
for input in "${inputs[@]}"; do
  tr -d '\000' < "$input" \
    | awk -f "$script_dir/enea_to_home_assistant.awk" >> "$output_dir/$output_file"
done

# Adjust the DST-overlap timestamp in the generated CSV before import.
sed -i 's/2026-03-29 02:00/2026-03-29 01:00/g' "$output_dir/$output_file"

# Run the curl command to import the processed CSV file into Home Assistant
curl -X POST \
   -H "Authorization: Bearer $ENEA_CLIENT_POST_PROCESS_HOME_ASSISTANT_TOKEN" \
   -H "Content-Type: application/json" \
   http://localhost:8123/api/services/import_statistics/import_from_file \
   -d '{
    "filename": "'"$output_file"'",
    "timezone_identifier": "Europe/Warsaw",
    "delimiter": ",",
    "decimal": ".",
    "datetime_format": "%Y-%m-%d %H:%M",
    "unit_from_entity": false
  }'
