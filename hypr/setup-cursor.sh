#!/bin/bash
# ============================================================
# setup-cursor.sh
# Instala cursores de Windows (.cur/.ani) para Linux/Hyprland
# ============================================================

SOURCE_DIR="/home/cristopher/Downloads/dark/default"
THEME_NAME="MyCursor"
THEME_DIR="$HOME/.local/share/icons/$THEME_NAME"
CURSORS_DIR="$THEME_DIR/cursors"
SCALE=${1:-2}  # Escala por defecto: 2 (para 4K)

echo "Limpiando instalación anterior..."
rm -rf "$THEME_DIR"
sudo rm -rf "/usr/share/icons/$THEME_NAME"
mkdir -p "$CURSORS_DIR"

echo "Convirtiendo cursores con escala $SCALE..."
cd "$SOURCE_DIR"
win2xcur *.cur *.ani -o "$CURSORS_DIR" --scale $SCALE

echo "Creando symlinks..."
cd "$CURSORS_DIR"

# Cursor principal (el más importante)
cp pointer default
ln -sf default left_ptr
ln -sf default arrow
ln -sf default top_left_arrow
ln -sf default x-cursor

# Texto
cp beam text
ln -sf text xterm
ln -sf text ibeam
ln -sf text cursor

# Links/mano
cp link pointer_hand
ln -sf pointer_hand hand
ln -sf pointer_hand hand1
ln -sf pointer_hand hand2
ln -sf pointer_hand pointing_hand
ln -sf pointer_hand openhand

# No disponible
cp unavailable crossed_circle
ln -sf crossed_circle forbidden
ln -sf crossed_circle no-drop
ln -sf crossed_circle not-allowed

# Carga completa
cp busy watch
ln -sf watch wait

# Carga parcial
cp working left_ptr_watch
ln -sf left_ptr_watch half-busy
ln -sf left_ptr_watch progress

# Mover
cp move fleur
ln -sf fleur all-scroll
ln -sf fleur size_all

# Redimensionar vertical
cp vert size_ver
ln -sf size_ver n-resize
ln -sf size_ver s-resize
ln -sf size_ver ns-resize
ln -sf size_ver v_double_arrow
ln -sf size_ver row-resize

# Redimensionar horizontal
cp horz size_hor
ln -sf size_hor e-resize
ln -sf size_hor w-resize
ln -sf size_hor ew-resize
ln -sf size_hor h_double_arrow
ln -sf size_hor col-resize

# Diagonal 1 (↘)
cp dgn1 size_fdiag
ln -sf size_fdiag nwse-resize
ln -sf size_fdiag nw-resize
ln -sf size_fdiag se-resize
ln -sf size_fdiag bd_double_arrow

# Diagonal 2 (↙)
cp dgn2 size_bdiag
ln -sf size_bdiag nesw-resize
ln -sf size_bdiag ne-resize
ln -sf size_bdiag sw-resize
ln -sf size_bdiag fd_double_arrow

# Precisión
cp precision crosshair
ln -sf crosshair cross
ln -sf crosshair tcross
ln -sf crosshair diamond_cross

# Ayuda
cp help question_arrow
ln -sf question_arrow dnd-ask

# Alternativo
cp alternate context-menu
ln -sf context-menu dnd-copy
ln -sf context-menu dnd-link
ln -sf context-menu dnd-move
ln -sf context-menu dnd-none

# Escritura a mano
cp handwriting pencil

# Pin y persona (sin equivalente estándar, usar default)
ln -sf default cell
ln -sf default alias

echo "Creando index.theme..."
cat > "$THEME_DIR/index.theme" << EOF
[Icon Theme]
Name=$THEME_NAME
Comment=Custom cursor theme from Windows
EOF

echo "Copiando al sistema..."
sudo cp -r "$THEME_DIR" "/usr/share/icons/"

echo "Configurando GTK..."
mkdir -p ~/.config/gtk-3.0
cat > ~/.config/gtk-3.0/settings.ini << EOF
[Settings]
gtk-cursor-theme-name=$THEME_NAME
gtk-cursor-theme-size=0
EOF

mkdir -p ~/.config/gtk-4.0
cat > ~/.config/gtk-4.0/settings.ini << EOF
[Settings]
gtk-cursor-theme-name=$THEME_NAME
gtk-cursor-theme-size=0
EOF

echo "Configurando X11..."
cat > ~/.Xresources << EOF
Xcursor.theme: $THEME_NAME
Xcursor.size: 0
EOF

echo ""
echo "✓ Instalación completa con escala $SCALE"
echo ""
echo "Ahora agrega esto a hyprland.conf:"
echo "  env = XCURSOR_THEME,$THEME_NAME"
echo "  env = XCURSOR_SIZE,0"
echo "  env = HYPRCURSOR_SIZE,0"
echo ""
echo "Cierra sesión y vuelve a entrar para aplicar."