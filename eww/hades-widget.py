#!/usr/bin/env python3
import gi
import os
import random

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
gi.require_version('GtkLayerShell', '0.1')
from gi.repository import Gtk, Gdk, GLib, GtkLayerShell, GdkPixbuf

PORTRAITS_DIR = "/home/cristopher/.config/eww/hades-assets/portraits"
LOGO_PATH = "/home/cristopher/.config/eww/hades-logo.png"

WIDGET_W = 520
WIDGET_H = 680
SPRITE_W = 480
SPRITE_H = 420
SPRITE_SCALE = 0.97
# El "cuadro" en el que se encierra el retrato se dibuja más angosto
# que el área real del sprite a propósito: así, partes del personaje
# que sobresalen del torso (manos, arma, pelo) quedan por fuera del
# marco - el mismo efecto que el margen izquierdo del widget de
# Hotline Miami 2, pero pensado para las cuatro esquinas.
FRAME_MARGIN_X = 68
FRAME_MARGIN_Y = 55
FRAME_LINE_WIDTH = 3

# Paleta del "House of Hades": negro con vetas rojo sangre y filos
# dorados en la UI del juego.
BG_COLOR = (0.07, 0.03, 0.03)
GOLD = (0.78, 0.62, 0.28)
BLOOD_RED = (0.45, 0.05, 0.05)

CHARACTERS = {
    "Zagreus": "Zagreus",
    "Hades": "Hades",
    "Persephone": "Persephone",
    "Nyx": "Nyx",
    "Achilles": "Achilles",
    "Alecto": "Alecto",
    "Aphrodite": "Aphrodite",
    "Ares": "Ares",
    "Artemis": "Artemis",
    "Athena": "Athena",
    "Bouldy": "Bouldy",
    "Cerberus": "Cerberus",
    "Chaos": "Chaos",
    "Charon": "Charon",
    "Demeter": "Demeter",
    "Dionysus": "Dionysus",
    "Eurydice": "Eurydice",
    "Hermes": "Hermes",
    "Hypnos": "Hypnos",
    "Medusa": "Medusa",
    "Megaera": "Megaera",
    "Minotaur": "Minotaur",
    "Orpheus": "Orpheus",
    "Patroclus": "Patroclus",
    "Poseidon": "Poseidon",
    "Sisyphus": "Sisyphus",
    "Skelly": "Skelly",
    "Thanatos": "Thanatos",
    "Theseus": "Theseus",
    "Tisiphone": "Tisiphone",
    "Zeus": "Zeus",
}


def count_frames(char_dir):
    if not os.path.isdir(char_dir):
        return 0
    return len([f for f in os.listdir(char_dir) if f.startswith("frame") and f.endswith(".png")])


def load_frame(char_dir, index, target_h, max_w):
    # Los PNG extraídos del juego vienen recortados cada uno a su propio
    # contenido, con tamaños y proporciones muy dispares entre personajes
    # (de 615x1028 a 1835x1105 según el personaje). Si se escalaran para
    # "caber" en una caja fija (como antes), los personajes anchos
    # terminaban diminutos y cada uno quedaba a una altura distinta.
    # En vez de eso, se escala TODOS a la misma altura objetivo (mismo
    # tamaño de cuerpo aparente) siempre - el ancho sale de ahí y
    # normalmente sobresale del marco a los costados, que es el efecto
    # buscado.
    path = os.path.join(char_dir, f"frame{index:02d}.png")
    if not os.path.exists(path):
        return None
    pixbuf = GdkPixbuf.Pixbuf.new_from_file(path)
    w, h = pixbuf.get_width(), pixbuf.get_height()
    scale = target_h / h
    nw, nh = max(1, int(w * scale)), max(1, int(h * scale))
    pixbuf = pixbuf.scale_simple(nw, nh, GdkPixbuf.InterpType.BILINEAR)

    # Los pocos personajes extremadamente anchos (tridente, arco, capa
    # extendida) rebasarían el área del widget entero a esta escala. En
    # vez de encogerlos (se verían chicos junto al resto), se les hace
    # "zoom": se recorta el sobrante de ambos costados por igual,
    # manteniendo el cuerpo al mismo tamaño que los demás y perdiendo
    # solo la punta de lo que sobresale.
    if nw > max_w:
        crop_x = (nw - max_w) // 2
        pixbuf = pixbuf.new_subpixbuf(crop_x, 0, max_w, nh)

    return pixbuf


class HadesWidget(Gtk.Window):
    def __init__(self):
        super().__init__()
        self.set_decorated(False)
        self.set_app_paintable(True)
        self.set_default_size(WIDGET_W, WIDGET_H)
        self.set_resizable(False)

        GtkLayerShell.init_for_window(self)
        GtkLayerShell.set_layer(self, GtkLayerShell.Layer.BOTTOM)
        GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.RIGHT, True)
        GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.BOTTOM, True)
        GtkLayerShell.set_margin(self, GtkLayerShell.Edge.RIGHT, 20)
        GtkLayerShell.set_margin(self, GtkLayerShell.Edge.BOTTOM, 20)
        GtkLayerShell.set_exclusive_zone(self, -1)

        screen = self.get_screen()
        visual = screen.get_rgba_visual()
        if visual:
            self.set_visual(visual)

        css = b"""
        .hades-label {
            color: #e8c170;
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

        # El logo y el retrato ya NO van en cajas separadas apiladas: al
        # ser cajas GTK distintas, había un borde recto exactamente
        # donde terminaba la caja del logo y empezaba la del sprite, y
        # cualquier parte del personaje (pelo, cabeza) que llegara hasta
        # ahí se veía "cortada" en línea recta contra el PNG del logo.
        # Ahora el logo se pinta DENTRO del mismo lienzo que el retrato,
        # encima de él (según lo pedido), así que donde el logo es
        # transparente el retrato se sigue viendo con su propio alfa, y
        # solo lo tapa donde el logo tiene píxeles opacos - sin costura.
        self.logo_pixbuf = None
        self.top_headroom = 0
        if os.path.exists(LOGO_PATH):
            logo_pixbuf = GdkPixbuf.Pixbuf.new_from_file(LOGO_PATH)
            lw, lh = logo_pixbuf.get_width(), logo_pixbuf.get_height()
            nw = int((WIDGET_W - 30) * 0.9)
            nh = int(lh * nw / lw)
            self.logo_pixbuf = logo_pixbuf.scale_simple(nw, nh, GdkPixbuf.InterpType.BILINEAR)
            self.top_headroom = nh + 12
        else:
            title = Gtk.Label(label="-- HADES --")
            title.get_style_context().add_class("hades-label")
            outer.pack_start(title, False, False, 2)

        content_h = SPRITE_H + self.top_headroom
        self.image_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.image_box.set_size_request(SPRITE_W, content_h)
        outer.pack_start(self.image_box, False, False, 4)

        self.sprite_area = Gtk.DrawingArea()
        self.sprite_area.set_size_request(SPRITE_W, content_h)
        self.sprite_area.connect('draw', self.on_draw_sprite)
        self.image_box.set_center_widget(self.sprite_area)

        self.label = Gtk.Label()
        self.label.get_style_context().add_class("hades-label")
        outer.pack_start(self.label, False, False, 2)

        self.char_keys = [k for k in CHARACTERS
                           if count_frames(os.path.join(PORTRAITS_DIR, k)) > 0]
        random.shuffle(self.char_keys)
        self.current_char_idx = 0
        self.current_pixbuf = None

        GLib.timeout_add(6000, self.next_character)

        self.update_portrait()
        self.show_all()

    def next_character(self):
        self.current_char_idx = (self.current_char_idx + 1) % len(self.char_keys)
        self.update_portrait()
        return True

    def on_draw_bg(self, widget, cr):
        w = widget.get_allocated_width()
        h = widget.get_allocated_height()

        # Panel rectangular oscuro con un filo dorado, como los paneles
        # de diálogo/códice de Hades, más una veta roja interior.
        cr.rectangle(0, 0, w, h)
        r, g, b = BG_COLOR
        cr.set_source_rgba(r, g, b, 1)
        cr.fill_preserve()

        cr.set_line_width(2)
        r, g, b = BLOOD_RED
        cr.set_source_rgba(r, g, b, 1)
        cr.stroke()

        margin = 6
        cr.rectangle(margin, margin, w - margin * 2, h - margin * 2)
        cr.set_line_width(2)
        r, g, b = GOLD
        cr.set_source_rgba(r, g, b, 1)
        cr.stroke()

    def on_draw_sprite(self, widget, cr):
        w = widget.get_allocated_width()
        h = widget.get_allocated_height()

        # El marco arranca "top_headroom" más abajo que el lienzo (ese
        # hueco es donde vive el logo, ver más abajo) para que la
        # posición/tamaño del marco no cambie aunque el lienzo ahora sea
        # más alto para darle sitio al logo.
        frame_top = self.top_headroom + FRAME_MARGIN_Y

        # El marco se dibuja primero, más angosto que el lienzo, para
        # que el retrato (pintado encima) tape el trazo donde lo cubre
        # y deje el resto del trazo visible - así el personaje se ve
        # "salir" del cuadro en vez de quedar recortado por él.
        cr.rectangle(FRAME_MARGIN_X, frame_top,
                     w - FRAME_MARGIN_X * 2, h - frame_top - FRAME_MARGIN_Y)
        cr.set_line_width(FRAME_LINE_WIDTH)
        r, g, b = GOLD
        cr.set_source_rgba(r, g, b, 1)
        cr.stroke()

        if self.current_pixbuf:
            pw = self.current_pixbuf.get_width()
            ph = self.current_pixbuf.get_height()

            # Todos los retratos terminan (pies) en el mismo punto
            # vertical en vez de centrarse cada uno según su propio alto
            # - así no "flotan" a alturas distintas por tener recortes
            # dispares. Ese punto coincide con la línea inferior del
            # marco.
            cr.save()

            # Izquierda, derecha y abajo son límites duros: nada del
            # retrato se dibuja más allá de esas tres líneas del marco.
            # Arriba se deja sin recortar (solo lo limita el borde
            # superior del lienzo, mucho más arriba ahora gracias al
            # hueco del logo) para que la cabeza/pelo pueda seguir
            # saliendo - lo que sobresalga por ahí queda debajo del
            # logo, que se pinta encima al final con su propio alfa en
            # vez de un corte recto.
            half_line = FRAME_LINE_WIDTH / 2
            cr.rectangle(FRAME_MARGIN_X - half_line, 0,
                         w - FRAME_MARGIN_X * 2 + half_line * 2,
                         h - FRAME_MARGIN_Y + half_line)
            cr.clip()

            x = (w - pw) / 2
            y = (h - FRAME_MARGIN_Y) - ph
            cr.translate(x, y)
            Gdk.cairo_set_source_pixbuf(cr, self.current_pixbuf, 0, 0)
            cr.paint()
            cr.restore()

        if self.logo_pixbuf:
            lw = self.logo_pixbuf.get_width()
            Gdk.cairo_set_source_pixbuf(cr, self.logo_pixbuf, (w - lw) / 2, 0)
            cr.paint()

    def update_portrait(self):
        char_key = self.char_keys[self.current_char_idx]
        char_dir = os.path.join(PORTRAITS_DIR, char_key)

        pixbuf = load_frame(char_dir, 0, SPRITE_H * SPRITE_SCALE, SPRITE_W * SPRITE_SCALE)
        if pixbuf:
            self.current_pixbuf = pixbuf
            self.sprite_area.queue_draw()
        else:
            print(f"[NOT FOUND] char={char_key}")

        self.label.set_text(CHARACTERS[char_key])


win = HadesWidget()
win.connect('destroy', Gtk.main_quit)
Gtk.main()
