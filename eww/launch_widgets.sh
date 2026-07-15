#!/bin/bash
eww kill 2>/dev/null
sleep 0.5
eww daemon
sleep 2
eww open song-window
sleep 1
SONG=$(bash /home/cristopher/.config/eww/song.sh)
eww update song-of-day="$SONG"