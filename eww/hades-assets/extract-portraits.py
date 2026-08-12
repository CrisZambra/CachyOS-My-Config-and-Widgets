#!/usr/bin/env python3
"""
Extrae los retratos de diálogo de Hades desde tu propia copia instalada
del juego (GUI.pkg) y los recorta al bounding box real de cada personaje.

Requiere el paquete deppth2 (más pillow y lz4, que instala como
dependencias): https://github.com/SGG-Modding/deppth
  pip install --user deppth2 pillow lz4
(o dentro de un venv propio - ver README del repo)

Uso:
  ./extract-portraits.py "/ruta/a/Hades/Content/Win/Packages/GUI.pkg" [salida]
"""
import os
import shutil
import subprocess
import sys
import tempfile

try:
    from deppth2 import deppth2 as dpkg
except ImportError:
    print("Falta el módulo deppth2. Instálalo con:\n"
          "  pip install --user deppth2 pillow lz4\n"
          "(o dentro de un venv propio - ver README)")
    sys.exit(1)

# Cada personaje puede tener varias variantes/expresiones de retrato
# (ej. Zagreus_Explaining01, Zagreus_Serious01...) - se usan como los
# "frames" que el widget va alternando, a falta de la animación de boca
# real del juego (esa existe, pero como overlays separados que Hades
# compone en tiempo real sobre el retrato base - fuera de alcance acá).
CHARACTERS = {
    "Zagreus": ["Portraits_Zagreus_01", "Portraits_Zagreus_Explaining01",
                "Portraits_Zagreus_Serious01", "Portraits_Zagreus_Defiant01",
                "Portraits_Zagreus_Unwell01"],
    "Hades": ["Portraits_Hades_01", "Portraits_Hades_Averted01",
              "Portraits_Hades_Helm01", "Portraits_Hades_HelmCape01"],
    "Persephone": ["Portraits_Persephone_01", "Portraits_Persephone_Joy01",
                   "Portraits_Persephone_FiredUp01",
                   "Portraits_Persephone_Calculating01",
                   "Portraits_Persephone_Apprehensive01"],
    "Nyx": ["Portraits_Nyx_01", "Portraits_Nyx_Averted_01"],
    "Achilles": ["Portraits_Achilles_01"],
    "Alecto": ["Portraits_Alecto_01"],
    "Aphrodite": ["Portraits_Aphrodite_01"],
    "Ares": ["Portraits_Ares_01", "Portraits_AresGeneric_01"],
    "Artemis": ["Portraits_Artemis_01", "Portraits_ArtemisArrow_01"],
    "Athena": ["Portraits_Athena_01"],
    "Bouldy": ["Portraits_Bouldy_01"],
    "Cerberus": ["Portraits_Cerberus_01"],
    "Chaos": ["Portraits_Chaos_01", "Portraits_Chaos_02"],
    "Charon": ["Portraits_Charon_01"],
    "Demeter": ["Portraits_Demeter_01"],
    "Dionysus": ["Portraits_Dionysus_01"],
    "Eurydice": ["Portraits_Eurydice_01"],
    "Hermes": ["Portraits_Hermes_01"],
    "Hypnos": ["Portraits_Hypnos_01"],
    "Medusa": ["Portraits_Medusa_01", "Portraits_Medusa_Confident01",
               "Portraits_Medusa_Empathetic01"],
    "Megaera": ["Portraits_Megaera_01", "Portraits_Megaera_Pleased01",
                "Portraits_Megaera_Standoffish01"],
    "Minotaur": ["Portraits_Minotaur_01", "Portraits_Minotaur_Armored01"],
    "Orpheus": ["Portraits_Orpheus_01"],
    "Patroclus": ["Portraits_Patroclus_01", "Portraits_Patroclus_Neutral01"],
    "Poseidon": ["Portraits_Poseidon_01"],
    "Sisyphus": ["Portraits_Sisyphus_01", "Portraits_SisyphusGeneric_01"],
    "Skelly": ["Portraits_Skelly_01"],
    "Thanatos": ["Portraits_Thanatos_01", "Portraits_Thanatos_Pleased01"],
    "Theseus": ["Portraits_Theseus_01", "Portraits_Theseus_Armored01"],
    "Tisiphone": ["Portraits_Tisiphone_01"],
    "Zeus": ["Portraits_Zeus_01"],
}


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    pkg_path = sys.argv[1]
    out_dir = sys.argv[2] if len(sys.argv) > 2 else os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "portraits")

    tmp_dir = tempfile.mkdtemp(prefix="hades-extract-")
    try:
        print("Extrayendo subtexturas de GUI.pkg (puede tardar ~1 min)...")
        dpkg.extract(pkg_path, tmp_dir, subtextures=True, logger=lambda s: None)

        src_dir = os.path.join(tmp_dir, "textures", "Portraits")
        os.makedirs(out_dir, exist_ok=True)

        for key, stems in CHARACTERS.items():
            frame_srcs = [os.path.join(src_dir, f"{s}.png") for s in stems]
            frame_srcs = [f for f in frame_srcs if os.path.exists(f)]
            if not frame_srcs:
                print(f"  [omitido] no encontrado: {key}")
                continue

            char_dir = os.path.join(out_dir, key)
            os.makedirs(char_dir, exist_ok=True)

            frame_paths = []
            for i, src in enumerate(frame_srcs):
                dst = os.path.join(char_dir, f"frame{i:02d}.png")
                shutil.copy(src, dst)
                frame_paths.append(dst)

            # Igual que con Hotline Miami 2: recortamos al bounding box
            # real, usando la UNIÓN entre todas las variantes/expresiones
            # del personaje para que no "salte" de tamaño al alternar.
            min_x = min_y = 10**9
            max_x = max_y = 0
            for fp in frame_paths:
                geom = subprocess.run(
                    ["identify", "-format", "%@", fp],
                    check=True, capture_output=True, text=True,
                ).stdout.strip()
                wh, xy = geom.split("+", 1)
                fw, fh = (int(v) for v in wh.split("x"))
                fx, fy = (int(v) for v in xy.split("+"))
                min_x = min(min_x, fx)
                min_y = min(min_y, fy)
                max_x = max(max_x, fx + fw)
                max_y = max(max_y, fy + fh)

            pad = 6
            crop_w = max_x - min_x + pad * 2
            crop_h = max_y - min_y + pad * 2
            crop_x = max(0, min_x - pad)
            crop_y = max(0, min_y - pad)

            for fp in frame_paths:
                subprocess.run(
                    ["convert", fp, "-crop", f"{crop_w}x{crop_h}+{crop_x}+{crop_y}",
                     "+repage", fp],
                    check=True, capture_output=True,
                )

            print(f"  ✓ {key}: {len(frame_paths)} frame(s) -> {char_dir} "
                  f"(recorte {crop_w}x{crop_h})")

        print(f"\nListo. Retratos en: {out_dir}")
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
