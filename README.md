# CachyOS - My Config and Widgets

Configuración de escritorio de [CachyOS](https://cachyos.org/) + [Hyprland](https://hyprland.org/) que uso día a día en un laptop 4K (HiDPI, escala 2.00), junto con los widgets de escritorio que fui armando (canción del día, lluvia Matrix, sprites de DOOM rotando).

No es un instalador "un click": son mis dotfiles reales, documentados para que los adaptes a tu propio setup.

## Contenido

| Carpeta | Qué es |
|---|---|
| `hypr/hyprland.conf` | Config principal de Hyprland (monitor, atajos, cursor, blur/sombras, autostart de todo lo demás) |
| `hypr/wallpaper-cycle.sh` | Rotación de wallpapers aleatoria con `awww` |
| `hypr/setup-cursor.sh` | Convierte un pack de cursores de Windows (.cur/.ani) a tema Xcursor con `win2xcur` |
| `hyprpanel/config.json` | Config de [HyprPanel](https://github.com/Jas-SinghFSU/HyprPanel) (barra, dashboard con shortcuts a Steam/Brave) |
| `eww/` | Widgets hechos con [EWW](https://github.com/elkowar/eww) y Python + GTK3 + `gtk-layer-shell` |
| `gtk/` | `settings.ini` de GTK3/GTK4 (tema de cursor) |
| `Xresources` | `Xcursor.theme` / `Xcursor.size` para que XWayland (apps como Godot, Krita) use el mismo cursor |

### Widgets en `eww/`

- **Canción del día** (`eww.yuck`, `eww.scss`, `song.sh`, `next-song.sh`, `scroll-text.sh`, `search-song.sh`, `clean_playlist.sh`): elige una canción "del día" desde una lista generada con `clean_playlist.sh` a partir de playlists `.m3u8`, con botones para buscarla en YouTube/Spotify/Deezer.
- **Matrix Rain** (`matrix-window.py`): ventana GTK3 + `gtk-layer-shell` en capa `BOTTOM` (detrás de todas las ventanas), lluvia de caracteres estilo Matrix, corre a ~15fps por consumo de CPU.
- **DOOM widget** (`doom-widget.py`, `doom-assets/`): sprites de enemigos de DOOM rotando en 360°, cambian de enemigo cada 6s.

## Importante: qué NO incluye este repo (y por qué)

- **Sprites de DOOM extraídos ni `doom-logo.png`**: son assets con copyright de id Software. En vez de eso incluyo `eww/doom-assets/extract-sprites.sh`, que los extrae de **tu propia copia legal** de `DOOM.WAD`/`DOOM2.WAD` con `deutex`. Sin sprites, el widget muestra el texto "-- DOOM --" en vez del logo (no rompe nada).
- **El pack de cursores de Windows** (origen de `MyCursor`): tampoco se redistribuye por licencia. `setup-cursor.sh` espera un pack `.cur`/`.ani` propio en la carpeta que definas en `SOURCE_DIR`.

## Dependencias

Repos oficiales (`pacman -S`):
```
hyprland hyprpaper grim grimblast wf-recorder brightnessctl wireplumber
imv mpv ffmpeg thunar nwg-look xorg-xrdb ufw
gtk-layer-shell gtk4-layer-shell python-gobject python-cairo
```

AUR (`paru -S`):
```
ags-hyprpanel-git   # HyprPanel
eww                 # widgets EWW
awww                # wallpaper con transiciones (fork de swww)
win2xcur            # convierte cursores .cur/.ani -> Xcursor
deutex              # extrae sprites de WADs de DOOM
```

## Instalación

1. Clona el repo y copia (o symlinkea) cada carpeta a su lugar en `~/.config`:
   ```bash
   git clone <url-de-este-repo> ~/CachyOS-My-Config-and-Widgets
   cd ~/CachyOS-My-Config-and-Widgets

   cp hypr/*.conf hypr/*.sh ~/.config/hypr/
   cp -r hyprpanel ~/.config/
   cp -r eww ~/.config/
   cp gtk/gtk-3.0-settings.ini ~/.config/gtk-3.0/settings.ini
   cp gtk/gtk-4.0-settings.ini ~/.config/gtk-4.0/settings.ini
   cp Xresources ~/.Xresources
   ```

2. **Reemplaza las rutas absolutas.** Estos archivos tienen `/home/cristopher` hardcodeado (mis dotfiles no son genéricos) — cámbialo por tu propio `$HOME`:
   ```bash
   grep -rl "/home/cristopher" ~/.config/hypr/hyprland.conf ~/.config/eww ~/.config/hypr/setup-cursor.sh \
     | xargs sed -i "s|/home/cristopher|$HOME|g"
   ```

3. **Cursor**: edita `SOURCE_DIR` en `hypr/setup-cursor.sh` para que apunte a tu propio pack de cursores `.cur`/`.ani`, luego:
   ```bash
   bash ~/.config/hypr/setup-cursor.sh 2   # el número es la escala (2 = HiDPI 4K)
   ```
   Nota: el tema resultante solo tendrá los tamaños de bitmap que traiga tu pack de origen — pedir un tamaño intermedio que no exista fuerza un reescalado con artefactos (cursor oscurecido/con halo en XWayland). Usa siempre un tamaño exacto disponible en `Xcursor.size` / `XCURSOR_SIZE` / `HYPRCURSOR_SIZE`.

4. **DOOM widget**: extrae los sprites desde tu propia copia de los WAD:
   ```bash
   cd ~/.config/eww/doom-assets
   ./extract-sprites.sh /ruta/a/DOOM.WAD doom1
   ./extract-sprites.sh /ruta/a/DOOM2.WAD doom2
   ```
   Opcional: coloca tu propio `doom-logo.png` en `~/.config/eww/` si quieres el logo en vez del texto "-- DOOM --".

5. **Canción del día**: genera la lista desde tus playlists `.m3u8`:
   ```bash
   bash ~/.config/eww/clean_playlist.sh /ruta/a/tus/playlists/
   ```

6. **Wallpapers**: coloca tus fondos en `~/Pictures/4k/` (o cambia `WALLPAPER_DIR` en `wallpaper-cycle.sh`).

7. Recarga Hyprland:
   ```bash
   hyprctl reload
   ```

## Notas / gotchas documentados

- El monitor está pineado explícitamente en `hyprland.conf` (`monitor = eDP-1,3840x2400@60,0x0,2`) — ajusta el nombre de salida (`eDP-1`), resolución y escala a tu propio monitor (`hyprctl monitors` para ver el tuyo).
- Blur y sombras están desactivados en `decoration {}` — es una decisión de rendimiento para GPUs Intel integradas modestas en paneles 4K, no una limitación de Hyprland. Actívalos si tu GPU aguanta.
- HyprPanel: las opciones del dashboard van bajo el prefijo `menus.dashboard...` en `config.json`, no `dashboard...` — con el prefijo equivocado, HyprPanel ignora la clave en silencio (sin error en el log).
- Los iconos de los shortcuts del dashboard de HyprPanel son solo glyphs de texto de una Nerd Font (no soporta imágenes/logos reales).
- XWayland (apps como Godot, Krita) lee el cursor desde `~/.Xresources` (`Xcursor.theme`/`Xcursor.size`), **no** desde las env vars `XCURSOR_SIZE`/`HYPRCURSOR_SIZE` de Hyprland — son dos rutas de configuración independientes.

## Licencia

MIT para los scripts y configuraciones de este repo (ver `LICENSE`). No cubre software de terceros que uses junto con esto (Hyprland, EWW, HyprPanel, DOOM, fuentes, etc.), cada uno con su propia licencia.
