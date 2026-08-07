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

WIDGET_W = 250
WIDGET_H = 290
SPRITE_W = 210
SPRITE_H = 210
# Los frames se escalan a este % del área del sprite para dejar espacio
# a la rotación (a un ángulo bajo como este, casi no hace falta margen).
SPRITE_SCALE = 0.9
MAX_ROTATION_DEG = 5.0

CHARACTERS = {
    "Richard": "Richard",
    "Cobra": "Cobra",
    "Tony": "Tony",
    "Alex": "Alex",
    "Ash": "Ash",
    "Swan": "Swan",
    "Rat": "Rat",
    "Corey": "Corey",
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
        GtkLayerShell.set_margin(self, GtkLayerShell.Edge.TOP, 546)
        GtkLayerShell.set_exclusive_zone(self, -1)

        screen = self.get_screen()
        visual = screen.get_rgba_visual()
        if visual:
            self.set_visual(visual)

        css = b"""
        .hlm2-box {
            background: rgba(0, 0, 0, 0.75);
            border: 1px solid rgba(255, 0, 90, 0.7);
            border-radius: 8px;
            padding: 8px;
        }
        .hlm2-label {
            color: #ff005a;
            font-size: 19px;
            font-weight: bold;
        }
        .hlm2-title {
            color: #ff66a3;
            font-size: 10px;
        }
        """
        style_provider = Gtk.CssProvider()
        style_provider.load_from_data(css)
        Gtk.StyleContext.add_provider_for_screen(
            self.get_screen(),
            style_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        outer.get_style_context().add_class("hlm2-box")
        self.add(outer)

        if os.path.exists(LOGO_PATH):
            logo_pixbuf = GdkPixbuf.Pixbuf.new_from_file(LOGO_PATH)
            lw, lh = logo_pixbuf.get_width(), logo_pixbuf.get_height()
            nw = int((WIDGET_W - 16) * 0.8)
            nh = int(lh * nw / lw)
            logo_pixbuf = logo_pixbuf.scale_simple(nw, nh, GdkPixbuf.InterpType.BILINEAR)
            logo_image = Gtk.Image.new_from_pixbuf(logo_pixbuf)
            outer.pack_start(logo_image, False, False, 2)
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

        GLib.timeout_add(6000, self.next_character)
        GLib.timeout_add(110, self.next_frame)
        GLib.timeout_add(40, self.tick_rotation)

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
        return True

    def on_draw_sprite(self, widget, cr):
        if not self.current_pixbuf:
            return
        angle_deg = math.sin(self.rotation_phase) * MAX_ROTATION_DEG
        w = self.sprite_area.get_allocated_width()
        h = self.sprite_area.get_allocated_height()
        pw = self.current_pixbuf.get_width()
        ph = self.current_pixbuf.get_height()

        cr.save()
        cr.translate(w / 2, h / 2)
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
