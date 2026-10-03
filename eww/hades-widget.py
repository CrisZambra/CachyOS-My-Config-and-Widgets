#!/usr/bin/env python3
import gi
import json
import os
import random

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
gi.require_version('GtkLayerShell', '0.1')
gi.require_version('PangoCairo', '1.0')
from gi.repository import Gtk, Gdk, GLib, GtkLayerShell, GdkPixbuf, Pango, PangoCairo

PORTRAITS_DIR = "/home/cristopher/.config/eww/hades-assets/portraits"
LOGO_PATH = "/home/cristopher/.config/eww/hades-logo.png"
# Ajustes manuales por personaje (escala/posición), generados con
# hades-assets/tune-character.py. Si el archivo no existe, o un
# personaje no tiene entrada, se usa el comportamiento normal
# (scale=1.0, offset_x=0, offset_y=0) sin ningún cambio.
OVERRIDES_PATH = "/home/cristopher/.config/eww/hades-assets/character-overrides.json"

WIDGET_W = 504
WIDGET_H = 655
# El logo ya se afinó a mano (tamaño/posición) con el ancho de widget
# que había en ese momento (520). Se guarda ese valor aparte y no
# WIDGET_W, para que si el widget se achica/agranda después el logo no
# cambie de tamaño solo - sigue la referencia con la que se ajustó.
LOGO_REF_W = 520
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
NAME_COLOR = (0.910, 0.757, 0.439)
NAME_FONT = "Cinzel Bold 34"

CHARACTERS = {
    "Zagreus": "Zagreo",
    "Hades": "Hades",
    "Persephone": "Perséfone",
    "Nyx": "Nix",
    "Achilles": "Aquiles",
    "Alecto": "Alecto",
    "Aphrodite": "Afrodita",
    "Ares": "Ares",
    "Artemis": "Artemisa",
    "Athena": "Atenea",
    "Bouldy": "Bouldy",
    "Cerberus": "Cerbero",
    "Chaos": "Caos",
    "Charon": "Caronte",
    "Demeter": "Deméter",
    "Dionysus": "Dioniso",
    "Eurydice": "Eurídice",
    "Hermes": "Hermes",
    "Hypnos": "Hipnos",
    "Medusa": "Medusa",
    "Megaera": "Megera",
    "Minotaur": "Minotauro",
    "Orpheus": "Orfeo",
    "Patroclus": "Patroclo",
    "Poseidon": "Poseidón",
    "Sisyphus": "Sísifo",
    "Skelly": "Skelly",
    "Thanatos": "Tánatos",
    "Theseus": "Teseo",
    "Tisiphone": "Tisífone",
    "Zeus": "Zeus",
}


def count_frames(char_dir):
    if not os.path.isdir(char_dir):
        return 0
    return len([f for f in os.listdir(char_dir) if f.startswith("frame") and f.endswith(".png")])


def load_overrides():
    if not os.path.exists(OVERRIDES_PATH):
        return {}
    try:
        with open(OVERRIDES_PATH) as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        print(f"[overrides] no se pudo leer {OVERRIDES_PATH}: {e}")
        return {}


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


def draw_frame_and_portrait(cr, w, h, top_headroom, pixbuf, offset_x, offset_y, logo_pixbuf=None):
    # Lógica de dibujo compartida entre el widget real (HadesWidget.on_draw_sprite)
    # y hades-assets/tune-character.py, para que la herramienta de ajuste
    # muestre EXACTAMENTE lo mismo que se ve en el escritorio.
    frame_top = top_headroom + FRAME_MARGIN_Y

    cr.rectangle(FRAME_MARGIN_X, frame_top,
                 w - FRAME_MARGIN_X * 2, h - frame_top - FRAME_MARGIN_Y)
    cr.set_line_width(FRAME_LINE_WIDTH)
    r, g, b = GOLD
    cr.set_source_rgba(r, g, b, 1)
    cr.stroke()

    if pixbuf:
        pw = pixbuf.get_width()
        ph = pixbuf.get_height()

        cr.save()
        half_line = FRAME_LINE_WIDTH / 2
        cr.rectangle(FRAME_MARGIN_X - half_line, 0,
                     w - FRAME_MARGIN_X * 2 + half_line * 2,
                     h - FRAME_MARGIN_Y + half_line)
        cr.clip()

        x = (w - pw) / 2 + offset_x
        y = (h - FRAME_MARGIN_Y) - ph + offset_y
        cr.translate(x, y)
        Gdk.cairo_set_source_pixbuf(cr, pixbuf, 0, 0)
        cr.paint()
        cr.restore()

    if logo_pixbuf:
        lw = logo_pixbuf.get_width()
        Gdk.cairo_set_source_pixbuf(cr, logo_pixbuf, (w - lw) / 2, 0)
        cr.paint()


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
        GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.TOP, True)
        GtkLayerShell.set_margin(self, GtkLayerShell.Edge.RIGHT, 20)
        GtkLayerShell.set_margin(self, GtkLayerShell.Edge.TOP, 20)
        GtkLayerShell.set_exclusive_zone(self, -1)

        screen = self.get_screen()
        visual = screen.get_rgba_visual()
        if visual:
            self.set_visual(visual)

        css = b"""
        .hades-label {
            color: #e8c170;
            font-family: "Cinzel";
            font-size: 24px;
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
        outer.set_margin_top(6)
        outer.set_margin_bottom(6)
        outer.set_margin_start(8)
        outer.set_margin_end(8)
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
            nw = int((LOGO_REF_W - 40) * 0.9)
            nh = int((lh - 30) * nw / lw)
            self.logo_pixbuf = logo_pixbuf.scale_simple(nw, nh, GdkPixbuf.InterpType.BILINEAR)
            self.top_headroom = nh + 12
        else:
            title = Gtk.Label(label="-- HADES --")
            title.get_style_context().add_class("hades-label")
            outer.pack_start(title, False, False, 2)

        content_h = SPRITE_H + self.top_headroom
        self.image_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.image_box.set_size_request(SPRITE_W, content_h)
        outer.pack_start(self.image_box, False, False, 2)

        self.sprite_area = Gtk.DrawingArea()
        self.sprite_area.set_size_request(SPRITE_W, content_h)
        self.sprite_area.connect('draw', self.on_draw_sprite)
        self.image_box.set_center_widget(self.sprite_area)

        # El nombre YA NO es un Gtk.Label metido en la caja vertical: GTK
        # solo "ve" el sprite_area como un bloque opaco de altura fija y
        # arranca el nombre justo debajo de él, mucho más cerca del
        # borde exterior que de la línea del marco interior (que está
        # FRAME_MARGIN_Y más arriba, DENTRO de ese bloque). Para
        # centrarlo de verdad entre ambas líneas se dibuja con Pango
        # directo sobre bg_area (que sí conoce la ventana completa), en
        # on_draw_bg, usando la posición real del sprite_area.
        self.current_name = ""

        self.overrides = load_overrides()

        self.char_keys = [k for k in CHARACTERS
                           if count_frames(os.path.join(PORTRAITS_DIR, k)) > 0]
        self.current_char_idx = random.randrange(len(self.char_keys))
        self.current_pixbuf = None
        self.offset_x = 0
        self.offset_y = 0

        GLib.timeout_add(6000, self.next_character)

        self.update_portrait()
        self.show_all()

    def next_character(self):
        # random.choice puro en vez de recorrer una lista barajada una
        # sola vez al inicio: con la lista barajada, después de la
        # primera vuelta completa el orden se repetía siempre igual -
        # esto elige un personaje al azar cada vez (evitando repetir el
        # mismo dos veces seguidas, para que siempre se note el cambio).
        if len(self.char_keys) > 1:
            new_idx = random.randrange(len(self.char_keys))
            while new_idx == self.current_char_idx:
                new_idx = random.randrange(len(self.char_keys))
            self.current_char_idx = new_idx
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

        if self.current_name:
            # Línea inferior del marco interior, en coordenadas de esta
            # ventana completa: la posición real del sprite_area (según
            # lo asignó GTK) más lo mismo que usa on_draw_sprite para
            # ubicar esa línea dentro de su propio lienzo.
            sprite_alloc = self.sprite_area.get_allocation()
            inner_frame_bottom = sprite_alloc.y + (sprite_alloc.height - FRAME_MARGIN_Y)
            outer_frame_bottom = h - margin
            band_center_y = (inner_frame_bottom + outer_frame_bottom) / 2

            layout = PangoCairo.create_layout(cr)
            layout.set_font_description(Pango.FontDescription(NAME_FONT))
            layout.set_text(self.current_name, -1)
            text_w, text_h = layout.get_pixel_size()

            r, g, b = NAME_COLOR
            cr.set_source_rgba(r, g, b, 1)
            cr.move_to((w - text_w) / 2, band_center_y - text_h / 2)
            PangoCairo.show_layout(cr, layout)

    def on_draw_sprite(self, widget, cr):
        w = widget.get_allocated_width()
        h = widget.get_allocated_height()
        draw_frame_and_portrait(cr, w, h, self.top_headroom, self.current_pixbuf,
                                 self.offset_x, self.offset_y, self.logo_pixbuf)

    def update_portrait(self):
        char_key = self.char_keys[self.current_char_idx]
        char_dir = os.path.join(PORTRAITS_DIR, char_key)
        override = self.overrides.get(char_key, {})

        pixbuf = load_frame(char_dir, 0, SPRITE_H * SPRITE_SCALE, SPRITE_W * SPRITE_SCALE)
        if pixbuf:
            # Ajuste manual opcional (ver hades-assets/tune-character.py):
            # escala extra encima de la normalización automática, y
            # desplazamiento en píxeles desde la posición por defecto
            # (centrado horizontal, pies en la línea del marco).
            extra_scale = override.get("scale", 1.0)
            if extra_scale != 1.0:
                pw, ph = pixbuf.get_width(), pixbuf.get_height()
                nw = max(1, int(pw * extra_scale))
                nh = max(1, int(ph * extra_scale))
                pixbuf = pixbuf.scale_simple(nw, nh, GdkPixbuf.InterpType.BILINEAR)
            self.current_pixbuf = pixbuf
            self.offset_x = override.get("offset_x", 0)
            self.offset_y = override.get("offset_y", 0)
            self.sprite_area.queue_draw()
        else:
            print(f"[NOT FOUND] char={char_key}")

        self.current_name = CHARACTERS[char_key]
        self.bg_area.queue_draw()


if __name__ == "__main__":
    win = HadesWidget()
    win.connect('destroy', Gtk.main_quit)
    Gtk.main()
