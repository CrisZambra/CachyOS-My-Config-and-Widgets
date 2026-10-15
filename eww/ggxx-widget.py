#!/usr/bin/env python3
"""
ggxx-widget.py

Widget de escritorio con el sprite de Sol Badguy (Guilty Gear XX Accent
Core Plus R), que reacciona a teclado/mouse - pero SOLO cuando no hay
ninguna ventana en primer plano (consulta `hyprctl activewindow` cada
1s; mientras juegas o programas, el widget no toma el teclado y no
reacciona a nada, para no interferir).

Controles (solo activos con el escritorio vacío, y el click con el
cursor encima del widget):
    a -> Golpe (P)
    w -> Patada (K)
    e -> Slash (S)
    f -> Heavy Slash (HS)
    x -> Dust
    g -> Burst
    click derecho sobre el widget -> Golpe (P)

Cada ataque es una SECUENCIA de varios sprites consecutivos (no uno
solo) para que se vea como una animación completa, no un golpe
instantáneo. Los sprites se eligieron a mano de entre los ~564 que
tiene Sol en sl.bin (ver ggxx-assets/extract-character.py) - no hay
ninguna tabla pública que diga qué sprite/secuencia es "el" Golpe/
Patada/etc. real del juego, así que son secuencias elegidas por
parecido visual, no necesariamente el movimiento exacto del juego.
Usa siempre la paleta #0 (la que trae por defecto cada personaje).
"""
import gi
import json
import os
import subprocess

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
gi.require_version('GtkLayerShell', '0.1')
from gi.repository import Gtk, Gdk, GLib, GtkLayerShell, GdkPixbuf

ASSETS_DIR = "/home/cristopher/.config/eww/ggxx-assets/sol"

WIDGET_W = 420
WIDGET_H = 460
SPRITE_W = 380
SPRITE_H = 360
SPRITE_SCALE = 0.95
FRAME_MS = 90  # cuánto dura cada frame de la animación

BG_COLOR = (0.05, 0.05, 0.06)
BORDER_COLOR = (0.75, 0.1, 0.1)
NAME_COLOR = "#e03a3a"

# Tecla (GDK keyval name) -> (prefijo de archivo de la secuencia, cuántos
# frames tiene, nombre a mostrar)
KEY_BINDINGS = {
    "a": ("punch", 4, "Golpe"),
    "w": ("kick", 6, "Patada"),
    "e": ("slash", 5, "Slash"),
    "f": ("heavy_slash", 6, "Heavy Slash"),
    "x": ("dust", 7, "Dust"),
    "g": ("burst", 7, "Burst"),
}
IDLE_FILE = "idle.png"


def load_scaled(path, target_h, max_w):
    pixbuf = GdkPixbuf.Pixbuf.new_from_file(path)
    w, h = pixbuf.get_width(), pixbuf.get_height()
    scale = target_h / h
    nw, nh = max(1, int(w * scale)), max(1, int(h * scale))
    pixbuf = pixbuf.scale_simple(nw, nh, GdkPixbuf.InterpType.BILINEAR)
    if nw > max_w:
        crop_x = (nw - max_w) // 2
        pixbuf = pixbuf.new_subpixbuf(crop_x, 0, max_w, nh)
    return pixbuf


class GGXXWidget(Gtk.Window):
    def __init__(self):
        super().__init__()
        self.set_decorated(False)
        self.set_app_paintable(True)
        self.set_default_size(WIDGET_W, WIDGET_H)
        self.set_resizable(False)

        GtkLayerShell.init_for_window(self)
        GtkLayerShell.set_layer(self, GtkLayerShell.Layer.BOTTOM)
        GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.LEFT, True)
        GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.BOTTOM, True)
        GtkLayerShell.set_margin(self, GtkLayerShell.Edge.LEFT, 20)
        # 60 y no 20: la barra de HyprPanel vive abajo de toda la
        # pantalla (~51px) y si no se deja ese hueco tapa el texto de
        # ayuda del widget.
        GtkLayerShell.set_margin(self, GtkLayerShell.Edge.BOTTOM, 60)
        GtkLayerShell.set_exclusive_zone(self, -1)
        # Arranca sin foco de teclado - solo lo toma cuando el
        # escritorio está vacío (ver _check_focus).
        GtkLayerShell.set_keyboard_mode(self, GtkLayerShell.KeyboardMode.NONE)

        screen = self.get_screen()
        visual = screen.get_rgba_visual()
        if visual:
            self.set_visual(visual)

        css = b"""
        .ggxx-label {
            color: #e0e0e0;
            font-size: 16px;
            font-weight: bold;
        }
        .ggxx-title {
            color: """ + NAME_COLOR.encode() + b""";
            font-size: 20px;
            font-weight: bold;
        }
        .ggxx-hint {
            color: #888888;
            font-size: 10px;
        }
        """
        style_provider = Gtk.CssProvider()
        style_provider.load_from_data(css)
        Gtk.StyleContext.add_provider_for_screen(
            self.get_screen(), style_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        overlay = Gtk.Overlay()
        self.add(overlay)

        self.bg_area = Gtk.DrawingArea()
        self.bg_area.connect('draw', self.on_draw_bg)
        overlay.add(self.bg_area)

        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        outer.set_margin_top(10)
        outer.set_margin_bottom(8)
        outer.set_margin_start(10)
        outer.set_margin_end(10)
        overlay.add_overlay(outer)

        title = Gtk.Label(label="-- GUILTY GEAR --")
        title.get_style_context().add_class("ggxx-title")
        outer.pack_start(title, False, False, 2)

        self.image_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.image_box.set_size_request(SPRITE_W, SPRITE_H)
        outer.pack_start(self.image_box, False, False, 4)

        self.sprite_area = Gtk.DrawingArea()
        self.sprite_area.set_size_request(SPRITE_W, SPRITE_H)
        self.sprite_area.connect('draw', self.on_draw_sprite)
        self.image_box.set_center_widget(self.sprite_area)

        self.label = Gtk.Label(label="Sol Badguy")
        self.label.get_style_context().add_class("ggxx-label")
        outer.pack_start(self.label, False, False, 2)

        hint = Gtk.Label(
            label="A=P  W=K  E=S  F=HS  X=Dust  G=Burst  (click der.=P) - solo con escritorio vacío"
        )
        hint.get_style_context().add_class("ggxx-hint")
        outer.pack_start(hint, False, False, 0)

        # Pixbufs precargados: la pose idle, y cada secuencia de
        # ataque como una lista de pixbufs.
        self.idle_pixbuf = load_scaled(
            os.path.join(ASSETS_DIR, IDLE_FILE), SPRITE_H * SPRITE_SCALE, SPRITE_W * SPRITE_SCALE
        )
        self.sequences = {}
        for key, (prefix, frame_count, _name) in KEY_BINDINGS.items():
            frames = []
            for i in range(frame_count):
                path = os.path.join(ASSETS_DIR, f"{prefix}_{i:02d}.png")
                if os.path.exists(path):
                    frames.append(load_scaled(
                        path, SPRITE_H * SPRITE_SCALE, SPRITE_W * SPRITE_SCALE
                    ))
            self.sequences[key] = frames

        self.current_pixbuf = self.idle_pixbuf
        self.anim_source = None

        # Reactividad: solo con el escritorio vacío (sin ventana en
        # primer plano). Se consulta cada 1s; al estar vacío, el
        # widget toma el foco de teclado bajo demanda.
        self.armed = False
        GLib.timeout_add(1000, self._check_focus)

        self.add_events(Gdk.EventMask.BUTTON_PRESS_MASK | Gdk.EventMask.KEY_PRESS_MASK)
        self.connect('key-press-event', self.on_key_press)
        self.connect('button-press-event', self.on_button_press)
        self.set_can_focus(True)

        self.show_all()

    def _check_focus(self):
        try:
            out = subprocess.run(
                ['hyprctl', 'activewindow', '-j'],
                capture_output=True, text=True, timeout=1
            ).stdout
            focused = bool(json.loads(out or '{}'))
        except Exception:
            focused = False

        armed = not focused
        if armed != self.armed:
            self.armed = armed
            GtkLayerShell.set_keyboard_mode(
                self,
                GtkLayerShell.KeyboardMode.ON_DEMAND if armed
                else GtkLayerShell.KeyboardMode.NONE
            )
        return True

    def trigger_pose(self, key, display_name):
        if not self.armed:
            return
        frames = self.sequences.get(key)
        if not frames:
            return

        if self.anim_source:
            GLib.source_remove(self.anim_source)

        self.label.set_text(f"Sol Badguy - {display_name}")
        self._play_frame(frames, 0)

    def _play_frame(self, frames, index):
        if index >= len(frames):
            self.current_pixbuf = self.idle_pixbuf
            self.label.set_text("Sol Badguy")
            self.sprite_area.queue_draw()
            self.anim_source = None
            return False

        self.current_pixbuf = frames[index]
        self.sprite_area.queue_draw()
        self.anim_source = GLib.timeout_add(
            FRAME_MS, self._play_frame, frames, index + 1
        )
        return False

    def on_key_press(self, widget, event):
        if not self.armed:
            return False
        keyval_name = Gdk.keyval_name(event.keyval)
        if keyval_name is None:
            return False
        key = keyval_name.lower()
        if key in KEY_BINDINGS:
            _prefix, _count, display_name = KEY_BINDINGS[key]
            self.trigger_pose(key, display_name)
            return True
        return False

    def on_button_press(self, widget, event):
        if not self.armed:
            return False
        if event.button == 3:  # click derecho
            _prefix, _count, display_name = KEY_BINDINGS["a"]
            self.trigger_pose("a", display_name)
            return True
        return False

    def on_draw_bg(self, widget, cr):
        w = widget.get_allocated_width()
        h = widget.get_allocated_height()

        cr.rectangle(0, 0, w, h)
        r, g, b = BG_COLOR
        cr.set_source_rgba(r, g, b, 1)
        cr.fill_preserve()

        cr.set_line_width(2)
        r, g, b = BORDER_COLOR
        cr.set_source_rgba(r, g, b, 1)
        cr.stroke()

    def on_draw_sprite(self, widget, cr):
        w = widget.get_allocated_width()
        h = widget.get_allocated_height()

        pixbuf = self.current_pixbuf
        if not pixbuf:
            return

        pw = pixbuf.get_width()
        ph = pixbuf.get_height()
        x = (w - pw) / 2
        y = h - ph
        Gdk.cairo_set_source_pixbuf(cr, pixbuf, x, y)
        cr.paint()


if __name__ == "__main__":
    win = GGXXWidget()
    win.connect('destroy', Gtk.main_quit)
    Gtk.main()
