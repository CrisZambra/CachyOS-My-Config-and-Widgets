#!/bin/bash
# ============================================================
# widget-selector.sh
# Elige al azar UNO de los widgets de "personaje" (capa BOTTOM,
# esquina superior derecha) para lanzar en esta sesión de Hyprland,
# en vez de tener siempre el mismo fijo. Agregar más opciones acá
# a futuro es tan simple como sumar una ruta más al array.
# ============================================================

WIDGETS=(
    "/home/cristopher/.config/eww/doom-widget.py"
    "/home/cristopher/.config/eww/hlm2-widget.py"
    "/home/cristopher/.config/eww/hades-widget.py"
)

CHOSEN="${WIDGETS[$RANDOM % ${#WIDGETS[@]}]}"

exec python3 "$CHOSEN"
