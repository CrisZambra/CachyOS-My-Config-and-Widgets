#!/bin/bash
WALLPAPER_DIR="$HOME/Pictures/4k"

while true; do
    find "$WALLPAPER_DIR" -type f \( -iname "*.jpg" -o -iname "*.png" -o -iname "*.jpeg" -o -iname "*.webp" \) | shuf | while read -r img; do
        awww img "$img" --transition-type wipe --transition-duration 1.5
        sleep 1800s
    done
done