#!/usr/bin/env python3
import gi
import os

gi.require_version('Gtk', '3.0')
gi.require_version('GtkLayerShell', '0.1')
from gi.repository import Gtk, GLib, GtkLayerShell, GdkPixbuf, Gdk

SPRITES_D1 = "/home/cristopher/.config/eww/doom-assets/doom1/sprites"
SPRITES_D2 = "/home/cristopher/.config/eww/doom-assets/doom2/sprites"

# Ancho y alto fijo del widget
WIDGET_W = 250
WIDGET_H = 290
SPRITE_W = 190
SPRITE_H = 310

ENEMIES = {
    "troo": {"name": "Imp",               "dir": SPRITES_D1, "walk": ["a","b","c","d"]},
    "poss": {"name": "Zombie",            "dir": SPRITES_D1, "walk": ["a","b","c","d"]},
    "spos": {"name": "Shotgun Guy",       "dir": SPRITES_D1, "walk": ["a","b","c","d"]},
    "sarg": {"name": "Demon",             "dir": SPRITES_D1, "walk": ["a","b","c","d"]},
    "head": {"name": "Cacodemon",         "dir": SPRITES_D1, "walk": ["a","b","c","d"]},
    "boss": {"name": "Baron of Hell",     "dir": SPRITES_D1, "walk": ["a","b","c","d"]},
    "cybr": {"name": "Cyberdemon",        "dir": SPRITES_D1, "walk": ["a","b","c","d"]},
    "cpos": {"name": "Chaingunner",       "dir": SPRITES_D2, "walk": ["a","b","c","d"]},
    "skel": {"name": "Revenant",          "dir": SPRITES_D2, "walk": ["a","b"]},
    "fatt": {"name": "Mancubus",          "dir": SPRITES_D2, "walk": ["a","b","c","d"]},
    "vile": {"name": "Archvile",          "dir": SPRITES_D2, "walk": ["a","b","c","d","e","f"]},
    "pain": {"name": "Pain Elemental",    "dir": SPRITES_D2, "walk": ["a","b","c","d"]},
    "bos2": {"name": "Hell Knight",       "dir": SPRITES_D2, "walk": ["a","b"]},
    "play": {"name": "Doomguy",           "dir": SPRITES_D1, "walk": ["a","b","c","d"]},
}

# Secuencia de ángulos para simular rotación completa
# 1=frente, 2,3,4=giro derecha, 5=espalda, 6,7,8=giro izquierda (espejo)
ROTATION = [1, 2, 3, 4, 5, 6, 7, 8]

def find_sprite(sprite_dir, code, frame, angle):
    files = os.listdir(sprite_dir)
    for f in files:
        name = f[:-4].lower()
        if not name.startswith(code):
            continue
        rest = name[len(code):]
        if len(rest) < 2:
            continue
        f1 = rest[0]
        a1 = rest[1]
        if f1 == frame and a1.isdigit() and int(a1) == angle:
            return os.path.join(sprite_dir, f), False
        if len(rest) >= 4:
            f2 = rest[2]
            a2 = rest[3]
            if a2.isdigit() and int(a2) == angle:
                if f2 == frame:
                    return os.path.join(sprite_dir, f), True
                if f1 == frame:
                    return os.path.join(sprite_dir, f), True
    return None, False

def load_sprite(sprite_dir, code, frame, angle, target_w, target_h):
    """Carga y escala el sprite, aplicando espejo si es necesario."""
    path, needs_flip = find_sprite(sprite_dir, code, frame, angle)
    if not path:
        return None

    pixbuf = GdkPixbuf.Pixbuf.new_from_file(path)

    # Voltear horizontalmente si es ángulo espejo
    if needs_flip:
        pixbuf = pixbuf.flip(horizontal=True)

    # Escalar manteniendo proporción dentro del tamaño fijo
    w, h = pixbuf.get_width(), pixbuf.get_height()
    scale = min(target_w / w, target_h / h)
    nw, nh = max(1, int(w * scale)), max(1, int(h * scale))
    pixbuf = pixbuf.scale_simple(nw, nh, GdkPixbuf.InterpType.NEAREST)

    return pixbuf

class DoomWidget(Gtk.Window):
    def __init__(self):
        super().__init__()
        self.set_decorated(False)
        self.set_app_paintable(True)
        self.set_default_size(WIDGET_W, WIDGET_H)
        self.set_resizable(False)

        # Layer Shell
        GtkLayerShell.init_for_window(self)
        GtkLayerShell.set_layer(self, GtkLayerShell.Layer.BOTTOM)
        GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.RIGHT, True)
        GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.TOP, True)
        GtkLayerShell.set_margin(self, GtkLayerShell.Edge.RIGHT, 20)
        GtkLayerShell.set_margin(self, GtkLayerShell.Edge.TOP, 20)
        GtkLayerShell.set_exclusive_zone(self, -1)

        # Transparencia
        screen = self.get_screen()
        visual = screen.get_rgba_visual()
        if visual:
            self.set_visual(visual)

        # CSS para el fondo del widget
        css = b"""
        .doom-box {
            background: rgba(0, 0, 0, 0.75);
            border: 1px solid rgba(255, 80, 0, 0.6);
            border-radius: 8px;
            padding: 8px;
        }
        .doom-label {
            color: #ff5000;
            font-size: 16px;
            font-weight: bold;
        }
        .doom-title {
            color: #ff8800;
            font-size: 9px;
        }
        """
        style_provider = Gtk.CssProvider()
        style_provider.load_from_data(css)
        Gtk.StyleContext.add_provider_for_screen(
            self.get_screen(),
            style_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        # Layout principal
        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        outer.get_style_context().add_class("doom-box")
        self.add(outer)

        # Título
        logo_path = "/home/cristopher/.config/eww/doom-logo.png"
        if os.path.exists(logo_path):
            logo_pixbuf = GdkPixbuf.Pixbuf.new_from_file(logo_path)
            # Escalar el logo al ancho del widget
            lw = WIDGET_W - 16
            lh = int(logo_pixbuf.get_height() * lw / logo_pixbuf.get_width())
            logo_pixbuf = logo_pixbuf.scale_simple(lw, lh, GdkPixbuf.InterpType.BILINEAR)
            logo_image = Gtk.Image.new_from_pixbuf(logo_pixbuf)
            outer.pack_start(logo_image, False, False, 2)
        else:
            title = Gtk.Label(label="-- DOOM --")
            title.get_style_context().add_class("doom-title")
            outer.pack_start(title, False, False, 2)

        # Contenedor centrado para el sprite
        self.image_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.image_box.set_size_request(SPRITE_W, SPRITE_H)
        outer.pack_start(self.image_box, True, True, 4)

        # Imagen centrada
        self.image = Gtk.Image()
        self.image_box.set_center_widget(self.image)

        # Nombre del enemigo
        self.label = Gtk.Label()
        self.label.get_style_context().add_class("doom-label")
        outer.pack_start(self.label, False, False, 2)

        # Estado
        self.enemy_keys = list(ENEMIES.keys())
        self.current_enemy_idx = 0
        self.current_frame_idx = 0
        self.current_rotation_idx = 0

        # Timers
        GLib.timeout_add(6000, self.next_enemy)   # Cambiar enemigo cada 6s
        GLib.timeout_add(200, self.next_frame)    # Animar cada 200ms

        self.update_sprite()
        self.show_all()

    def next_enemy(self):
        self.current_enemy_idx = (self.current_enemy_idx + 1) % len(self.enemy_keys)
        self.current_frame_idx = 0
        self.current_rotation_idx = 0
        self.update_sprite()
        return True

    def next_frame(self):
        enemy_key = self.enemy_keys[self.current_enemy_idx]
        enemy = ENEMIES[enemy_key]

        self.current_rotation_idx = (self.current_rotation_idx + 1) % len(ROTATION)
        if self.current_rotation_idx == 0:
            self.current_frame_idx = (self.current_frame_idx + 1) % len(enemy["walk"])

        self.update_sprite()
        return True

    def update_sprite(self):
        enemy_key = self.enemy_keys[self.current_enemy_idx]
        enemy = ENEMIES[enemy_key]
        frame = enemy["walk"][self.current_frame_idx]
        angle = ROTATION[self.current_rotation_idx]

        pixbuf = load_sprite(enemy["dir"], enemy_key, frame, angle, SPRITE_W, SPRITE_H)
        if pixbuf:
            self.image.set_from_pixbuf(pixbuf)
        else:
            print(f"[NOT FOUND] enemy={enemy_key} frame={frame} angle={angle}")

        self.label.set_text(f"{enemy['name']}")

win = DoomWidget()
win.connect('destroy', Gtk.main_quit)
Gtk.main()