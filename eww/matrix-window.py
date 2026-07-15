#!/usr/bin/env python3
import gi
import random
import cairo

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
gi.require_version('GtkLayerShell', '0.1')

from gi.repository import Gtk, Gdk, GLib, GtkLayerShell

CHARS = "ABCDEF0123456789@#$%*!?"
WIDTH = 500
HEIGHT = 400
FONT_SIZE = 14
cols = WIDTH // FONT_SIZE
rows = HEIGHT // FONT_SIZE

drops = [float(random.randint(0, rows)) for _ in range(cols)]
trails = [[0.0] * rows for _ in range(cols)]

def random_char():
    return random.choice(CHARS)

class MatrixArea(Gtk.DrawingArea):
    def __init__(self):
        super().__init__()
        self.set_size_request(WIDTH, HEIGHT)
        self.connect('draw', self.draw)
        GLib.timeout_add(67, self.tick)  # ~15fps

    def tick(self):
        for i in range(cols):
            row = int(drops[i]) % rows
            trails[i][row] = 1.0
            for j in range(rows):
                if trails[i][j] > 0:
                    trails[i][j] = max(0, trails[i][j] - 0.0536)
            drops[i] = drops[i] + 1.34
            if drops[i] > rows + random.randint(0, 10):
                drops[i] = 0.0
        self.queue_draw()
        return True

    def draw(self, widget, cr):
        cr.set_source_rgba(0, 0, 0, 0.6) #background
        cr.rectangle(0, 0, WIDTH, HEIGHT)
        cr.fill()

        cr.select_font_face("monospace",
            cairo.FONT_SLANT_NORMAL,
            cairo.FONT_WEIGHT_NORMAL)
        cr.set_font_size(FONT_SIZE)

        for i in range(cols):
            head = int(drops[i]) % rows
            for j in range(rows):
                alpha = trails[i][j]
                if alpha > 0.01:
                    if j == head:
                        cr.set_source_rgba(0.8, 1.0, 0.8, 1.0)
                    else:
                        cr.set_source_rgba(0.0, alpha, 0.0, alpha)
                    cr.move_to(i * FONT_SIZE, (j + 1) * FONT_SIZE)
                    cr.show_text(random_char())

class MatrixWindow(Gtk.Window):
    def __init__(self):
        super().__init__()
        self.set_default_size(WIDTH, HEIGHT)
        self.set_decorated(False)
        self.set_app_paintable(True)

        # Transparencia
        screen = self.get_screen()
        visual = screen.get_rgba_visual()
        if visual:
            self.set_visual(visual)

        # Layer Shell — poner en capa BOTTOM detrás de todo
        GtkLayerShell.init_for_window(self)
        GtkLayerShell.set_layer(self, GtkLayerShell.Layer.BOTTOM)
        GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.LEFT, True)
        GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.TOP, True)
        GtkLayerShell.set_margin(self, GtkLayerShell.Edge.LEFT, 20)
        GtkLayerShell.set_margin(self, GtkLayerShell.Edge.TOP, 155)
        GtkLayerShell.set_exclusive_zone(self, -1)

        area = MatrixArea()
        self.add(area)
        self.show_all()

win = MatrixWindow()
win.connect('destroy', Gtk.main_quit)
Gtk.main()