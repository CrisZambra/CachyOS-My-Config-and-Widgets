#!/bin/bash
CACHE="$HOME/.config/eww/scroll-cache.txt"

# Obtener la canción directamente del script, no de eww
TEXT=$(eww get song-of-day)

# Si eww aún no cargó, obtener directamente
if [ "$TEXT" = "Cargando..." ] || [ -z "$TEXT" ]; then
    TEXT=$(bash /home/cristopher/.config/eww/song.sh)
    eww update song-of-day="$TEXT"
fi

MAX=35
if [ ${#TEXT} -le $MAX ]; then
    echo "$TEXT"
    exit
fi

POS=0
if [ -f "$CACHE" ]; then
    POS=$(cat "$CACHE")
fi

DISPLAY="${TEXT:$POS}  ${TEXT:0:$POS}"
DISPLAY="${DISPLAY:0:$MAX}"
POS=$(( (POS + 1) % ${#TEXT} ))
echo $POS > "$CACHE"
echo "$DISPLAY"