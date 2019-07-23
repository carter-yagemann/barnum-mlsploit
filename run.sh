#!/bin/bash
set -e

INPUT="/mnt/input"
OUTPUT="/mnt/output"

CONFIG="$INPUT/input.json"
RESULT="$OUTPUT/output.json"


# General input validation and setup
rm -f "$OUTPUT/*.pdf"
if [ ! -f $CONFIG ]; then
    echo "input.json not found in $INPUT, did you mean to copy one of the example input JSON?"
    exit 1
fi


# General input variables
NAME=$( jq -r ".name" "$CONFIG" )

# Name specific input variables
if [[ $NAME == "Mimicus" ]]; then
    NUM_FILES=$( jq ".num_files" "$CONFIG" )
fi


echo "Running $NAME"

if [[ $NAME == "Mimicus" ]]; then
    rm -f /app/mimicus/data/attack.list
    if [ ! -d /app/mimicus/results ]; then
        mkdir /app/mimicus/results
    else
        rm -f /app/mimicus/results/*
    fi

    for PDF in `jq -r ".files[]" "$CONFIG"`; do
        FILEPATH="${INPUT}/${PDF}"
        if [ ! -f "$FILEPATH" ]; then
            echo "Cannot find $FILEPATH, cannot continue"

            # Write output.json
            echo -n '{"name": "Mimicus", "tags": [], "files": [' > "$RESULT"
            for PDF in `jq -r ".files[]" "$CONFIG"`; do echo -n "\"${PDF}\"," >> "$RESULT"; done
            sed -i 's/,$//' "$RESULT"
            echo -n '], "files_extra": [], "files_modified": []}' >> "$RESULT"

            exit 1
        else
            echo "$FILEPATH" >> /app/mimicus/data/attack.list
        fi
    done

    echo "Calling Mimicus"
    python2 /app/mimicus/reproduction/FTC.py

    cp /app/mimicus/results/FTC_mimicry/*.pdf "$OUTPUT"

    # Write output.json
    echo -n '{"name": "Mimicus", "tags": [' > "$RESULT"
    for PDF in `jq -r ".files[]" "$CONFIG"`; do echo -n '{},' >> "$RESULT"; done
    sed -i 's/,$//' "$RESULT"
    echo -n '], "files": [' >> "$RESULT"
    for PDF in `jq -r ".files[]" "$CONFIG"`; do echo -n "\"${PDF}\"," >> "$RESULT"; done
    sed -i 's/,$//' "$RESULT"
    echo -n '], "files_extra": [], "files_modified": [' >> "$RESULT"
    for PDF in `jq -r ".files[]" "$CONFIG"`; do echo -n "\"${PDF}\"," >> "$RESULT"; done
    sed -i 's/,$//' "$RESULT"
    echo -n ']}' >> "$RESULT"

    exit 0
fi

if [[ $NAME == "Barnum-Train" || $NAME == "Barnum-Eval" ]]; then
    res=$( python3 /app/barnum-wrapper.py )
    exit $res
fi
