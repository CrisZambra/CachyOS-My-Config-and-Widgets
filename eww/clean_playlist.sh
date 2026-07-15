#!/bin/bash
# ============================================================
# clean_playlist.sh
# Extrae y limpia nombres de canciones desde archivos .m3u8
# Uso: ./clean_playlist.sh /ruta/a/playlists/*.m3u8
# o:   ./clean_playlist.sh /ruta/a/playlists/
# ============================================================

OUTPUT_FILE="$HOME/.config/eww/canciones.txt"
TEMP_FILE=$(mktemp)

if [ -d "$1" ]; then
    FILES=$(find "$1" -name "*.m3u8")
else
    FILES="$@"
fi

if [ -z "$FILES" ]; then
    echo "Uso: $0 /ruta/a/playlists/*.m3u8"
    echo "  o: $0 /ruta/a/playlists/"
    exit 1
fi

echo "Procesando playlists..."

for file in $FILES; do
    [ -f "$file" ] || continue
    grep -v '^#' "$file" | grep -v '^$' | while read -r line; do
        filename=$(basename "$line")
        name="${filename%.*}"
        # Eliminar formato disco.pista: "4.05 "
        name=$(echo "$name" | sed 's/^[0-9]\{1,2\}\.[0-9]\{1,3\}[[:space:]]*//')
        # Eliminar número de pista: "01 - ", "01. ", "1. ", "01 "
        name=$(echo "$name" | sed 's/^[0-9]\{1,3\}[[:space:]]*[-\.]\?[[:space:]]*//')
        # Limpiar espacios al inicio y final
        name=$(echo "$name" | sed 's/^[[:space:]]*//' | sed 's/[[:space:]]*$//')
        [ -n "$name" ] && echo "$name"
    done
done >> "$TEMP_FILE"

sort -u "$TEMP_FILE" > "$OUTPUT_FILE"
rm "$TEMP_FILE"

TOTAL=$(wc -l < "$OUTPUT_FILE")
echo "✓ Listo: $TOTAL canciones únicas guardadas en $OUTPUT_FILE ver0.1"