# Convert NUL-free Enea CSV records into Home Assistant statistics.
BEGIN {
    FS = ";"
    OFS = ","
}

# Each invocation handles one monthly file with its own header.
NR == 1 { next }

# Placeholder rows have no usable energy readings.
/"---"/ { next }

{
    $0 = sanitize_record($0)

    start = hour_start($1)
    import_energy = $4
    export_energy = $5

    emit_statistic("sensor.grid_import_energy", start, import_energy)
    emit_statistic("sensor.grid_export_energy", start, export_energy)
}

function sanitize_record(record) {
    gsub(/"="/, "", record)
    record = normalize_decimals(record)
    gsub(/"/, "", record)
    return record
}

function normalize_decimals(value) {
    # Replace only commas between digits, leaving other commas intact.
    while (match(value, /[0-9],[0-9]/)) {
        value = substr(value, 1, RSTART) "." substr(value, RSTART + 2)
    }
    return value
}

function hour_start(timestamp,    parts) {
    split(timestamp, parts, /[- :]/)
    return parts[1] "-" parts[2] "-" parts[3] " " parts[4] ":00"
}

function emit_statistic(statistic_id, start, energy) {
    print statistic_id, "kWh", start, energy
}
