#!/usr/bin/env python3
import gi
import os
import math
import random

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
gi.require_version('GtkLayerShell', '0.1')
from gi.repository import Gtk, Gdk, GLib, GtkLayerShell, GdkPixbuf

FACES_DIR = "/home/cristopher/.config/eww/hlm2-assets/faces"
LOGO_PATH = "/home/cristopher/.config/eww/hlm2-logo.png"

WIDGET_W = 400
WIDGET_H = 540
SPRITE_W = 360
SPRITE_H = 360
# Margen mínimo (px) entre el borde superior del lienzo y la cabeza -
# se calcula la posición dinámicamente por personaje/frame para que
# quede lo más arriba posible SIN recortarse (antes, un pivote fijo
# hacía que las cabezas más altas se cortaran por arriba).
SPRITE_TOP_MARGIN = 0
# Los frames se escalan a este % del área del sprite para dejar espacio
# a la rotación (a un ángulo bajo como este, casi no hace falta margen).
SPRITE_SCALE = 0.97
MAX_ROTATION_DEG = 5.0
# En el menú de Hotline Miami 1 el logo no solo se inclina de lado a
# lado, también "respira" (se agranda/achica) como si se moviera hacia
# adelante y atrás. LOGO_SCALE_PULSE es cuánto varía el tamaño (0.05 =
# +-5%).
LOGO_SCALE_PULSE = 0.05

# El "Neon Void" de Hotline Miami: el fondo detrás de los retratos que
# hablan cicla de color constantemente. El juego lo tiene hardcodeado
# en el código (no hay ningún asset con los valores exactos - se
# confirmó al no encontrar ninguna textura ni shader con esos colores),
# así que esto es una aproximación usando la paleta documentada del
# juego (cian/rosa) más los pares mencionados por la comunidad
# (cian-púrpura, verde-naranja) ciclando en secuencia.
VOID_COLORS = [
    (0x2e, 0xff, 0xff),  # cian
    (0xb0, 0x26, 0xff),  # púrpura
    (0xfe, 0x6d, 0xbc),  # rosa/magenta
    (0xff, 0x6b, 0x00),  # naranja
    (0x39, 0xff, 0x74),  # verde neón
]
VOID_CUT = 0.18  # qué tan angosto es el lado inferior respecto al superior

CHARACTERS = {
    "BikerHelmet": "Biker (Helmet)",
    "Cop": "Cop",
    "Father": "Father",
    "GeneralDown": "General (Down)",
    "Henchman": "Henchman",
    "NickeStore": "Nicke (Store)",
    "PigButcher": "Pig Butcher",
    "PigMask": "Pig (Mask)",
    "RatShades": "Rat (Shades)",
    "Richard": "Richard",
    "Son": "Son",
    "Writer": "Writer",
    "Bear": "Bear",
    "Tiger": "Tiger",
    "Zebra": "Zebra",
}


def count_frames(char_dir):
    if not os.path.isdir(char_dir):
        return 0
    return len([f for f in os.listdir(char_dir) if f.startswith("frame") and f.endswith(".png")])


def load_frame(char_dir, index, target_w, target_h):
    path = os.path.join(char_dir, f"frame{index:02d}.png")
    if not os.path.exists(path):
        return None
    pixbuf = GdkPixbuf.Pixbuf.new_from_file(path)
    w, h = pixbuf.get_width(), pixbuf.get_height()
    scale = min(target_w / w, target_h / h)
    nw, nh = max(1, int(w * scale)), max(1, int(h * scale))
    return pixbuf.scale_simple(nw, nh, GdkPixbuf.InterpType.NEAREST)


def lerp_color(c1, c2, t):
    return tuple(c1[i] + (c2[i] - c1[i]) * t for i in range(3))


class HLM2Widget(Gtk.Window):
    def __init__(self):
        super().__init__()
        self.set_decorated(False)
        self.set_app_paintable(True)
        self.set_default_size(WIDGET_W, WIDGET_H)
        self.set_resizable(False)

        GtkLayerShell.init_for_window(self)
        GtkLayerShell.set_layer(self, GtkLayerShell.Layer.BOTTOM)
        GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.RIGHT, True)
        GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.TOP, True)
        GtkLayerShell.set_margin(self, GtkLayerShell.Edge.RIGHT, 20)
        GtkLayerShell.set_margin(self, GtkLayerShell.Edge.TOP, 20)
        GtkLayerShell.set_exclusive_zone(self, -1)

        screen = self.get_screen()
        visual = screen.get_rgba_visual()
        if visual:
            self.set_visual(visual)

        css = b"""
        .hlm2-label {
            color: #ffffff;
            font-size: 19px;
            font-weight: bold;
        }
        """
        style_provider = Gtk.CssProvider()
        style_provider.load_from_data(css)
        Gtk.StyleContext.add_provider_for_screen(
            self.get_screen(),
            style_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        overlay = Gtk.Overlay()
        self.add(overlay)

        self.bg_area = Gtk.DrawingArea()
        self.bg_area.connect('draw', self.on_draw_bg)
        overlay.add(self.bg_area)

        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        outer.set_margin_top(10)
        outer.set_margin_bottom(10)
        outer.set_margin_start(10)
        outer.set_margin_end(10)
        overlay.add_overlay(outer)

        self.logo_pixbuf = None
        if os.path.exists(LOGO_PATH):
            logo_pixbuf = GdkPixbuf.Pixbuf.new_from_file(LOGO_PATH)
            lw, lh = logo_pixbuf.get_width(), logo_pixbuf.get_height()
            nw = int((WIDGET_W - 10) * 0.9)
            nh = int(lh * nw / lw)
            self.logo_pixbuf = logo_pixbuf.scale_simple(nw, nh, GdkPixbuf.InterpType.BILINEAR)

            # Lienzo un poco más grande que el logo para que, al
            # balancearse como en Hotline Miami 1, las puntas no se
            # recorten contra el borde del área de dibujo.
            box_w = int(nw * 1.2)
            box_h = int(nh * 1.2)
            self.logo_area = Gtk.DrawingArea()
            self.logo_area.set_size_request(box_w, box_h)
            self.logo_area.connect('draw', self.on_draw_logo)
            outer.pack_start(self.logo_area, False, False, 2)
        else:
            title = Gtk.Label(label="-- HOTLINE MIAMI 2 --")
            title.get_style_context().add_class("hlm2-title")
            outer.pack_start(title, False, False, 2)

        self.image_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.image_box.set_size_request(SPRITE_W, SPRITE_H)
        outer.pack_start(self.image_box, True, True, 4)

        self.sprite_area = Gtk.DrawingArea()
        self.sprite_area.set_size_request(SPRITE_W, SPRITE_H)
        self.sprite_area.connect('draw', self.on_draw_sprite)
        self.image_box.set_center_widget(self.sprite_area)

        self.label = Gtk.Label()
        self.label.get_style_context().add_class("hlm2-label")
        outer.pack_start(self.label, False, False, 2)

        self.char_keys = [k for k in CHARACTERS
                           if count_frames(os.path.join(FACES_DIR, k)) > 0]
        random.shuffle(self.char_keys)
        self.current_char_idx = 0
        self.current_frame_idx = 0
        self.frame_count = 1
        self.current_pixbuf = None
        self.rotation_phase = 0.0
        self.void_phase = 0.0

        GLib.timeout_add(6000, self.next_character)
        GLib.timeout_add(110, self.next_frame)
        GLib.timeout_add(40, self.tick_rotation)
        GLib.timeout_add(40, self.tick_void)

        self.update_face()
        self.show_all()

    def next_character(self):
        self.current_char_idx = (self.current_char_idx + 1) % len(self.char_keys)
        self.current_frame_idx = 0
        self.update_face()
        return True

    def next_frame(self):
        if self.frame_count > 1:
            self.current_frame_idx = (self.current_frame_idx + 1) % self.frame_count
            self.update_face()
        return True

    def tick_rotation(self):
        self.rotation_phase += 0.05
        self.sprite_area.queue_draw()
        if self.logo_pixbuf:
            self.logo_area.queue_draw()
        return True

    def on_draw_logo(self, widget, cr):
        if not self.logo_pixbuf:
            return
        angle_deg = math.sin(self.rotation_phase) * MAX_ROTATION_DEG
        scale = 1.0 + math.cos(self.rotation_phase) * LOGO_SCALE_PULSE
        w = widget.get_allocated_width()
        h = widget.get_allocated_height()
        lw = self.logo_pixbuf.get_width()
        lh = self.logo_pixbuf.get_height()

        cr.save()
        cr.translate((w - 60) / 2, h / 2)
        cr.rotate(math.radians(angle_deg))
        cr.scale(scale, scale)
        cr.translate(-lw / 2, -lh / 2)
        Gdk.cairo_set_source_pixbuf(cr, self.logo_pixbuf, 0, 0)
        cr.paint()
        cr.restore()

    def tick_void(self):
        self.void_phase = (self.void_phase + 0.006) % len(VOID_COLORS)
        self.bg_area.queue_draw()
        return True

    def current_void_color(self):
        i = int(self.void_phase)
        t = self.void_phase - i
        c1 = VOID_COLORS[i]
        c2 = VOID_COLORS[(i + 1) % len(VOID_COLORS)]
        r, g, b = lerp_color(c1, c2, t)
        return r / 255, g / 255, b / 255

    def on_draw_bg(self, widget, cr):
        w = widget.get_allocated_width()
        h = widget.get_allocated_height()
        cut = w * VOID_CUT

        # Cuadrilátero: lado derecho vertical (ángulos rectos arriba y
        # abajo), lado superior más largo que el inferior, lado
        # izquierdo en diagonal - un rectángulo con un triángulo recto
        # pegado arriba a la izquierda.
        cr.move_to(0, 0)
        cr.line_to(w, 0)
        cr.line_to(w, h)
        cr.line_to(cut, h)
        cr.close_path()

        r, g, b = self.current_void_color()
        cr.set_source_rgba(r, g, b, 1)
        cr.fill_preserve()

        # Borde negro-blanco-negro: se traza el mismo contorno tres
        # veces con ancho decreciente, así cada trazo más fino solo
        # deja ver el "anillo" exterior del anterior.
        cr.set_line_width(10)
        cr.set_source_rgba(0, 0, 0, 1)
        cr.stroke_preserve()

        cr.set_line_width(6)
        cr.set_source_rgba(1, 1, 1, 1)
        cr.stroke_preserve()

        cr.set_line_width(2)
        cr.set_source_rgba(0, 0, 0, 1)
        cr.stroke()

    def on_draw_sprite(self, widget, cr):
        if not self.current_pixbuf:
            return
        angle_deg = math.sin(self.rotation_phase) * MAX_ROTATION_DEG
        w = self.sprite_area.get_allocated_width()
        h = self.sprite_area.get_allocated_height()
        pw = self.current_pixbuf.get_width()
        ph = self.current_pixbuf.get_height()

        # Sube la cabeza lo más posible sin que se recorte contra el
        # borde superior del lienzo: el centro de rotación se calcula
        # a partir del tamaño real de esta imagen, con un pequeño
        # margen extra para la leve rotación del bamboleo.
        half_diag = (ph / 2) * 1.05
        pivot_y = min(h / 2, SPRITE_TOP_MARGIN -10 + half_diag)

        cr.save()
        cr.translate((w - 30) / 2, pivot_y)
        cr.rotate(math.radians(angle_deg))
        cr.translate(-pw / 2, -ph / 2)
        Gdk.cairo_set_source_pixbuf(cr, self.current_pixbuf, 0, 0)
        cr.paint()
        cr.restore()

    def update_face(self):
        char_key = self.char_keys[self.current_char_idx]
        char_dir = os.path.join(FACES_DIR, char_key)
        self.frame_count = count_frames(char_dir)

        pixbuf = load_frame(char_dir, self.current_frame_idx,
                             SPRITE_W * SPRITE_SCALE, SPRITE_H * SPRITE_SCALE)
        if pixbuf:
            self.current_pixbuf = pixbuf
            self.sprite_area.queue_draw()
        else:
            print(f"[NOT FOUND] char={char_key} frame={self.current_frame_idx}")

        self.label.set_text(CHARACTERS[char_key])


win = HLM2Widget()
win.connect('destroy', Gtk.main_quit)
Gtk.main()
