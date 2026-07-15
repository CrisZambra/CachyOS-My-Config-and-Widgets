#!/bin/bash
PLATFORM=$1
SONG=$(cat /home/cristopher/.config/eww/canciones.txt | grep -F "$(eww get song-of-day)" | head -1)
QUERY=$(echo "$SONG" | sed 's/ /+/g')

case $PLATFORM in
    youtube)
        xdg-open "https://www.youtube.com/results?search_query=$QUERY" ;;
    spotify)
        xdg-open "https://open.spotify.com/search/$QUERY" ;;
    deezer)
        xdg-open "https://www.deezer.com/search/$QUERY" ;;
esac