#!/bin/bash
# ============================================================
# widgets-ctl.sh
# Control manual, desde HyprPanel, de los widgets de fondo (Matrix
# Rain + el widget de personaje que haya elegido widget-selector.sh).
#
# Uso:
#   widgets-ctl.sh close   # mata los que estén corriendo
#   widgets-ctl.sh open    # lanza los que falten (nunca duplica: antes
#                          # de lanzar cada uno comprueba con pgrep)
# ============================================================
set -u

ALL_PATTERN="matrix-window.py|doom-widget.py|hlm2-widget.py|hades-widget.py"
CHAR_PATTERN="doom-widget.py|hlm2-widget.py|hades-widget.py"
EWW_DIR="/home/cristopher/.config/eww"

case "${1:-}" in
    close)
        pkill -f "$ALL_PATTERN"
        ;;
    open)
        # stdout/stderr van a /dev/null a propósito: si heredan la salida
        # de quien llama a este script (HyprPanel via execAsync, o una
        # shell con el output capturado), ese proceso se queda esperando
        # a que la pipe se cierre - y nunca se cierra porque el widget
        # GTK sigue corriendo para siempre.
        pgrep -f "matrix-window.py" >/dev/null || (nohup python3 "$EWW_DIR/matrix-window.py" >/dev/null 2>&1 & disown)
        pgrep -f "$CHAR_PATTERN" >/dev/null || (nohup bash "$EWW_DIR/widget-selector.sh" >/dev/null 2>&1 & disown)
        ;;
    *)
        echo "Uso: $0 close|open" >&2
        exit 1
        ;;
esac
