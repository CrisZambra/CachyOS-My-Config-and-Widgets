#!/bin/bash
SONG=$(shuf -n1 /home/cristopher/.config/eww/canciones.txt)
eww update song-of-day="$SONG"