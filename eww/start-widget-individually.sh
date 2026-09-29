#!/bin/bash
# ============================================================
# start-widget-individually.sh
#
# Referencia de los comandos para iniciar cada widget de escritorio
# POR SEPARADO, uno a la vez, útil para depurar/ajustar uno en
# particular sin tener que recargar toda la sesión de Hyprland.
#
# Este archivo NO se ejecuta solo de punta a punta (mataría e
# iniciaría los widgets uno detrás de otro). Copia y pega la sección
# del widget que te interesa, o descomenta solo esa parte.
# ============================================================

# --- Matar cualquier instancia previa de un widget en particular ---
# (cámbialo por el nombre del script que quieras reiniciar)
#   pkill -f "doom-widget.py"
#   pkill -f "hlm2-widget.py"
#   pkill -f "hades-widget.py"
#   pkill -f "matrix-window.py"

# --- Canción del día + Matrix Rain + lanzador de widgets EWW ---
# bash /home/cristopher/.config/eww/launch_widgets.sh

# --- Matrix Rain (lluvia de caracteres, capa BOTTOM) ---
# python3 /home/cristopher/.config/eww/matrix-window.py

# --- DOOM widget (sprites de enemigos rotando 360°) ---
# python3 /home/cristopher/.config/eww/doom-widget.py

# --- Hotline Miami 2 widget (cabezas parlantes con diálogo) ---
# python3 /home/cristopher/.config/eww/hlm2-widget.py

# --- Hades widget (retrato de diálogo por personaje, con marco) ---
# python3 /home/cristopher/.config/eww/hades-widget.py

# --- Selector aleatorio (el que realmente arranca hyprland.conf) ---
# elige al azar UNO de los tres widgets de personaje de arriba
# bash /home/cristopher/.config/eww/widget-selector.sh
