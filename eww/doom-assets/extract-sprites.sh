#!/bin/bash
# ============================================================
# extract-sprites.sh
# Extrae los sprites de DOOM.WAD / DOOM2.WAD como PNG con
# transparencia, usando deutex. NO redistribuye WADs ni sprites:
# necesitas tu propia copia legal de DOOM.WAD y/o DOOM2.WAD.
#
# Uso:
#   ./extract-sprites.sh /ruta/a/DOOM.WAD doom1
#   ./extract-sprites.sh /ruta/a/DOOM2.WAD doom2
# ============================================================
set -e

WAD="$1"
OUTNAME="$2"

if [ -z "$WAD" ] || [ -z "$OUTNAME" ]; then
    echo "Uso: $0 /ruta/a/DOOM.WAD <doom1|doom2>"
    exit 1
fi

if ! command -v deutex >/dev/null; then
    echo "Falta deutex. Instala con: paru -S deutex"
    exit 1
fi

OUTDIR="$(dirname "$0")/$OUTNAME"
mkdir -p "$OUTDIR"

deutex -doom "$WAD" -dir "$OUTDIR" -png -rgb 0 47 47 -sprites -extract

echo "✓ Sprites extraídos en $OUTDIR/sprites"
echo "  El widget (doom-widget.py) espera esta estructura:"
echo "  eww/doom-assets/doom1/sprites/*.png"
echo "  eww/doom-assets/doom2/sprites/*.png"
