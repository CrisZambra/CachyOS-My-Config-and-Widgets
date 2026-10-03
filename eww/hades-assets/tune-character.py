#!/usr/bin/env python3
"""
Herramienta interactiva para ajustar a mano, personaje por personaje, la
escala y posición del retrato dentro del marco del widget de Hades -
para los casos donde la normalización automática (misma altura para
todos, ver load_frame() en hades-widget.py) igual se ve desproporcionada
o demasiado chica/grande.

Uso:
    python3 tune-character.py

Controles:
    Re Pág / Av Pág   cambiar de personaje (anterior / siguiente)
    Flechas           mover el retrato (2px; con Shift, 10px)
    + / -             agrandar / achicar (5% por paso)
    0                 resetear el personaje actual (quita su ajuste)
    q / Esc           salir

Cada cambio se guarda al instante en character-overrides.json (al lado
de este script) - no hace falta guardar a mano. hades-widget.py lee ese
archivo en cada arranque; para ver el resultado en el widget real hay
que reiniciarlo (pkill -f hades-widget.py && python3 ../hades-widget.py).

Reusa load_frame() y draw_frame_and_portrait() de hades-widget.py
directamente (import por ruta, el nombre tiene un guion y no es un
módulo válido para "import" normal), así que esta vista previa es
pixel-por-pixel la misma que la del widget real: mismo marco, mismo
recorte duro a los costados/abajo, mismo logo encima.
"""
import gi
import importlib.util
import json
import os

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gtk, Gdk, GdkPixbuf

_HERE = os.path.dirname(os.path.abspath(__file__))
_WIDGET_PATH = os.path.join(_HERE, "..", "hades-widget.py")

_spec = importlib.util.spec_from_file_location("hades_widget", _WIDGET_PATH)
hw = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(hw)

MOVE_STEP = 2
MOVE_STEP_FAST = 10
SCALE_STEP = 0.05
SCALE_MIN = 0.3
SCALE_MAX = 3.0


class TuneWindow(Gtk.Window):
    def __init__(self):
        super().__init__(title="Ajustar personajes de Hades")
        self.set_resizable(False)

        self.overrides = hw.load_overrides()
        self.char_keys = sorted(
            k for k in hw.CHARACTERS
            if hw.count_frames(os.path.join(hw.PORTRAITS_DIR, k)) > 0
        )
        self.idx = 0
        self.base_pixbuf = None
        self.pixbuf = None
        self.offset_x = 0
        self.offset_y = 0

        # Mismo logo que el widget real, para juzgar bien el hueco de
        # arriba (top_headroom) con el que convive el retrato.
        self.logo_pixbuf = None
        self.top_headroom = 0
        if os.path.exists(hw.LOGO_PATH):
            logo_pixbuf = GdkPixbuf.Pixbuf.new_from_file(hw.LOGO_PATH)
            lw, lh = logo_pixbuf.get_width(), logo_pixbuf.get_height()
            nw = int((hw.LOGO_REF_W - 40) * 0.9)
            nh = int((lh - 30) * nw / lw)
            self.logo_pixbuf = logo_pixbuf.scale_simple(nw, nh, GdkPixbuf.InterpType.BILINEAR)
            self.top_headroom = nh + 12

        self.content_h = hw.SPRITE_H + self.top_headroom

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        vbox.set_margin_top(8)
        vbox.set_margin_bottom(8)
        vbox.set_margin_start(8)
        vbox.set_margin_end(8)
        self.add(vbox)

        self.info_label = Gtk.Label()
        self.info_label.set_justify(Gtk.Justification.CENTER)
        vbox.pack_start(self.info_label, False, False, 0)

        self.area = Gtk.DrawingArea()
        self.area.set_size_request(hw.SPRITE_W, self.content_h)
        self.area.connect('draw', self.on_draw)
        vbox.pack_start(self.area, False, False, 0)

        help_label = Gtk.Label(
            label="RePág/AvPág: cambiar personaje    Flechas: mover (Shift = x5)"
                  "    +/-: escalar    0: resetear    q: salir"
        )
        vbox.pack_start(help_label, False, False, 0)

        self.set_can_focus(True)
        self.connect('key-press-event', self.on_key)
        self.connect('destroy', Gtk.main_quit)

        self.load_current()
        self.show_all()

    def current_key(self):
        return self.char_keys[self.idx]

    def rescale_pixbuf(self):
        if not self.base_pixbuf:
            self.pixbuf = None
            return
        override = self.overrides.get(self.current_key(), {})
        scale = override.get("scale", 1.0)
        if scale == 1.0:
            self.pixbuf = self.base_pixbuf
            return
        pw, ph = self.base_pixbuf.get_width(), self.base_pixbuf.get_height()
        nw, nh = max(1, int(pw * scale)), max(1, int(ph * scale))
        self.pixbuf = self.base_pixbuf.scale_simple(nw, nh, GdkPixbuf.InterpType.BILINEAR)

    def load_current(self):
        char_key = self.current_key()
        char_dir = os.path.join(hw.PORTRAITS_DIR, char_key)
        self.base_pixbuf = hw.load_frame(
            char_dir, 0, hw.SPRITE_H * hw.SPRITE_SCALE, hw.SPRITE_W * hw.SPRITE_SCALE
        )
        override = self.overrides.get(char_key, {})
        self.offset_x = override.get("offset_x", 0)
        self.offset_y = override.get("offset_y", 0)
        self.rescale_pixbuf()
        self.update_label()
        self.area.queue_draw()

    def update_label(self):
        char_key = self.current_key()
        name = hw.CHARACTERS[char_key]
        override = self.overrides.get(char_key, {})
        scale = override.get("scale", 1.0)
        self.info_label.set_markup(
            f"<b>{name}</b>  ({char_key})   [{self.idx + 1}/{len(self.char_keys)}]\n"
            f"scale={scale:.2f}   offset_x={self.offset_x}   offset_y={self.offset_y}"
        )

    def mutate_override(self, **kwargs):
        char_key = self.current_key()
        override = dict(self.overrides.get(char_key, {}))
        override.update(kwargs)
        # Si quedó en los valores por defecto no hace falta guardar nada
        # para este personaje - se limpia para no ensuciar el archivo.
        if override.get("scale", 1.0) == 1.0 and override.get("offset_x", 0) == 0 \
                and override.get("offset_y", 0) == 0:
            self.overrides.pop(char_key, None)
        else:
            self.overrides[char_key] = override
        self.save()

        self.offset_x = override.get("offset_x", 0)
        self.offset_y = override.get("offset_y", 0)
        self.rescale_pixbuf()
        self.update_label()
        self.area.queue_draw()

    def save(self):
        with open(hw.OVERRIDES_PATH, "w") as f:
            json.dump(self.overrides, f, indent=2, sort_keys=True, ensure_ascii=False)

    def on_draw(self, widget, cr):
        w = widget.get_allocated_width()
        h = widget.get_allocated_height()
        hw.draw_frame_and_portrait(
            cr, w, h, self.top_headroom, self.pixbuf,
            self.offset_x, self.offset_y, self.logo_pixbuf
        )

    def on_key(self, widget, event):
        key = Gdk.keyval_name(event.keyval)
        shift = bool(event.state & Gdk.ModifierType.SHIFT_MASK)
        step = MOVE_STEP_FAST if shift else MOVE_STEP

        if key in ("q", "Q", "Escape"):
            Gtk.main_quit()
            return True

        if key == "Page_Up":
            self.idx = (self.idx - 1) % len(self.char_keys)
            self.load_current()
            return True
        if key == "Page_Down":
            self.idx = (self.idx + 1) % len(self.char_keys)
            self.load_current()
            return True

        if key == "Left":
            self.mutate_override(offset_x=self.offset_x - step)
            return True
        if key == "Right":
            self.mutate_override(offset_x=self.offset_x + step)
            return True
        if key == "Up":
            self.mutate_override(offset_y=self.offset_y - step)
            return True
        if key == "Down":
            self.mutate_override(offset_y=self.offset_y + step)
            return True

        if key in ("plus", "equal", "KP_Add"):
            scale = self.overrides.get(self.current_key(), {}).get("scale", 1.0)
            scale = min(SCALE_MAX, round(scale + SCALE_STEP, 2))
            self.mutate_override(scale=scale)
            return True
        if key in ("minus", "KP_Subtract"):
            scale = self.overrides.get(self.current_key(), {}).get("scale", 1.0)
            scale = max(SCALE_MIN, round(scale - SCALE_STEP, 2))
            self.mutate_override(scale=scale)
            return True

        if key == "0":
            self.mutate_override(scale=1.0, offset_x=0, offset_y=0)
            return True

        return False


win = TuneWindow()
Gtk.main()
