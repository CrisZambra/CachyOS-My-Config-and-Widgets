#!/bin/bash
FILE="$HOME/.config/eww/canciones.txt"
if [ ! -f "$FILE" ] || [ ! -s "$FILE" ]; then
    echo "Sin canciones"
    exit
fi
TOTAL=$(wc -l < "$FILE")
SEED=$(date +%j%Y)
LINE=$(( (SEED % TOTAL) + 1 ))
sed -n "${LINE}p" "$FILE"