#!/usr/bin/env python3
"""
Extrae las "caras" animadas (sprites que hablan en los diálogos) de
Hotline Miami 2: Wrong Number desde el .wad del juego instalado, y
corta cada atlas en sus frames individuales (PNG por frame).

Formato del .wad ("AGAR" container + "AGTEXTUREPACKER" sprite atlas)
reverse-engineered para este script; no distribuye ningún asset del
juego, solo lee tu propia copia instalada.

Uso:
  ./extract-faces.py "/ruta/a/Hotline Miami 2/hlm2_data_desktop.wad" [salida]
"""
import struct
import subprocess
import sys
import os

# Todas las "caras" de diálogo del juego (nombre interno -> nombre
# mostrado), extraídas de Atlases/Sprites/Faces/sprFace<nombre>.png en
# el WAD. Se excluyen a propósito los props sin cara (teléfono, radio,
# TV, diario, notas, walkie-talkie, carrito de golf) y unos pocos
# assets con un patrón de nombre distinto (sprBikerFace, sprCobraBlood,
# sprHenchmanFace1/2, sprite2772) que no calzan con el template
# sprFace<nombre> que usa este script.
CHARACTERS = {
    "50Manager": "Manager",
    "50ManagerGlad": "Manager (Glad)",
    "Alex": "Alex",
    "Andy": "Andy",
    "Ash": "Ash",
    "Biker": "Biker",
    "BikerHelmet": "Biker (Helmet)",
    "BlackSquad": "Black Squad",
    "Cobra": "Cobra",
    "CobraHappy": "Cobra (Happy)",
    "CobraPhone": "Cobra (Phone)",
    "ColombianBoss": "Colombian Boss",
    "Cop": "Cop",
    "CopPanic": "Cop (Panic)",
    "CopPhone": "Cop (Phone)",
    "CopyClerk": "Copy Clerk",
    "Corey": "Corey",
    "CSI": "CSI",
    "Dennis": "Dennis",
    "Director": "Director",
    "Father": "Father",
    "FatSquad": "Fat Squad",
    "GangLeader": "Gang Leader",
    "General": "General",
    "GeneralBlood": "General (Blood)",
    "GeneralDown": "General (Down)",
    "GeneralPanther": "General (Panther)",
    "Girl": "Girl",
    "GirlAngry": "Girl (Angry)",
    "Guard": "Guard",
    "Hammer": "Hammer",
    "Henchman": "Henchman",
    "HenchmanGirlfriend": "Henchman's Girlfriend",
    "Hobo": "Hobo",
    "Host": "Host",
    "HostAnxious": "Host (Anxious)",
    "HostTwitch": "Host (Twitch)",
    "Inspector": "Inspector",
    "Jonatan": "Jonatan",
    "Judge": "Judge",
    "Lawyer": "Lawyer",
    "Mark": "Mark",
    "Nicke": "Nicke",
    "NickeStore": "Nicke (Store)",
    "NPC1": "NPC",
    "Pig": "Pig",
    "PigAngry": "Pig (Angry)",
    "PigButcher": "Pig Butcher",
    "PigMask": "Pig (Mask)",
    "PigPhone": "Pig (Phone)",
    "PigPsycho": "Pig (Psycho)",
    "PigSilent": "Pig (Silent)",
    "PizzaDude": "Pizza Dude",
    "Police": "Police",
    "PoliceChief": "Police Chief",
    "PoliceInterrogation": "Police (Interrogation)",
    "PoliceScared": "Police (Scared)",
    "PrisonBoss": "Prison Boss",
    "Prosecutor": "Prosecutor",
    "Rat": "Rat",
    "RatCassettes": "Rat (Cassettes)",
    "RatMom": "Rat's Mom",
    "RatPhone": "Rat (Phone)",
    "RatShades": "Rat (Shades)",
    "Richard": "Richard",
    "Robber": "Robber",
    "RussianCobra": "Russian Cobra",
    "RussianParty": "Russian Party",
    "SaunaGangster": "Sauna Gangster",
    "Sister": "Sister",
    "Soldier": "Soldier",
    "Son": "Son",
    "SonAngry": "Son (Angry)",
    "SonGate": "Son (Gate)",
    "SonGateCover": "Son (Gate Cover)",
    "SonRobber": "Son (Robber)",
    "Swan": "Swan",
    "Swat": "Swat",
    "SwatBoss": "Swat Boss",
    "Tattooer": "Tattooer",
    "Tony": "Tony",
    "Ventriloquist": "Ventriloquist",
    "VIPGuard": "VIP Guard",
    "Waitress": "Waitress",
    "Writer": "Writer",
    "WriterWife": "Writer's Wife",
    "Bear": "Bear",
    "Tiger": "Tiger",
    "Zebra": "Zebra",
}

# Bear, Tiger y Zebra son personajes jugables (los otros "Fans"
# enmascarados, inspirados en el protagonista de Hotline Miami 1) pero
# el juego no les dio un retrato de diálogo animado - no existe
# sprFaceBear/Tiger/Zebra. Lo más parecido que hay en el mismo atlas
# es el ícono estático de su máscara (sprMask<nombre>), así que se usa
# ese en su lugar (sin animación de boca, es una sola imagen).
SPRITE_NAME_OVERRIDES = {
    "Bear": "sprMaskBear",
    "Tiger": "sprMaskTiger",
    "Zebra": "sprMaskZebra",
}


def parse_wad(wad_path):
    with open(wad_path, "rb") as f:
        data = f.read()

    if data[0:4] != b"AGAR":
        raise ValueError("No es un WAD formato AGAR (hlm2_data_desktop.wad)")

    pos = 4
    major, minor, ext_header_size = struct.unpack_from("<3I", data, pos)
    pos += 12
    pos += ext_header_size

    file_count = struct.unpack_from("<I", data, pos)[0]
    pos += 4

    entries = {}
    for _ in range(file_count):
        namelen = struct.unpack_from("<I", data, pos)[0]
        pos += 4
        name = data[pos:pos + namelen].decode("utf-8", "replace")
        pos += namelen
        size, off = struct.unpack_from("<QQ", data, pos)
        pos += 16
        entries[name] = (size, off)

    # Tabla de directorios extra (formato AGAR v2) - hay que saltarla
    # para calcular correctamente el inicio de los datos.
    dir_count = struct.unpack_from("<I", data, pos)[0]
    pos += 4
    for _ in range(dir_count):
        dirnamelen = struct.unpack_from("<I", data, pos)[0]
        pos += 4
        pos += dirnamelen
        entry_count = struct.unpack_from("<I", data, pos)[0]
        pos += 4
        for _ in range(entry_count):
            enamelen = struct.unpack_from("<I", data, pos)[0]
            pos += 4
            pos += enamelen
            pos += 1  # entry type (uint8)

    data_start = pos
    return data, entries, data_start


def extract_entry(data, entries, data_start, name):
    size, off = entries[name]
    abs_off = data_start + off
    return data[abs_off:abs_off + size]


def parse_atlas_meta(meta_bytes):
    """Parsea el .meta AGTEXTUREPACKER y devuelve {sprite_name: [(x,y,w,h), ...]}"""
    d = meta_bytes
    pos = 0
    strlen = d[pos]
    pos += 1
    magic = d[pos:pos + strlen].decode()
    pos += strlen
    if magic != "AGTEXTUREPACKER":
        raise ValueError(f"meta desconocido: {magic}")

    pos += 4  # version
    sprite_count = struct.unpack_from("<I", d, pos)[0]
    pos += 4

    sprites = {}
    for _ in range(sprite_count):
        namelen = d[pos]
        pos += 1
        name = d[pos:pos + namelen].decode()
        pos += namelen
        frame_count = struct.unpack_from("<I", d, pos)[0]
        pos += 4

        frames = []
        for _ in range(frame_count):
            _pad0, w, h, atlas_x, atlas_y = struct.unpack_from("<5i", d, pos)
            pos += 20
            pos += 4  # u0 (float, no lo necesitamos)
            pos += 4  # pad
            pos += 4  # u1 (float)
            pos += 4  # v1 (float)
            frames.append((atlas_x, atlas_y, w, h))

        sprites[name] = frames

    return sprites


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    wad_path = sys.argv[1]
    out_dir = sys.argv[2] if len(sys.argv) > 2 else os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "faces")

    data, entries, data_start = parse_wad(wad_path)
    os.makedirs(out_dir, exist_ok=True)

    for internal_name in CHARACTERS:
        sprite_name = SPRITE_NAME_OVERRIDES.get(internal_name, f"sprFace{internal_name}")
        png_key = f"Atlases/Sprites/Faces/{sprite_name}.png"
        meta_key = f"Atlases/Sprites/Faces/{sprite_name}.meta"

        if png_key not in entries or meta_key not in entries:
            print(f"  [omitido] no encontrado: {internal_name}")
            continue

        png_bytes = extract_entry(data, entries, data_start, png_key)
        meta_bytes = extract_entry(data, entries, data_start, meta_key)

        atlas_path = os.path.join(out_dir, f"_atlas_{internal_name}.png")
        with open(atlas_path, "wb") as f:
            f.write(png_bytes)

        sprites = parse_atlas_meta(meta_bytes)
        frames = sprites.get(sprite_name)
        if not frames:
            print(f"  [omitido] sin frames en meta: {internal_name}")
            continue

        char_dir = os.path.join(out_dir, internal_name)
        os.makedirs(char_dir, exist_ok=True)

        for i, (x, y, w, h) in enumerate(frames):
            frame_path = os.path.join(char_dir, f"frame{i:02d}.png")
            subprocess.run(
                ["convert", atlas_path, "-crop", f"{w}x{h}+{x}+{y}",
                 "+repage", frame_path],
                check=True, capture_output=True,
            )

        os.remove(atlas_path)

        # El cuadro que el atlas le asigna a cada personaje trae una
        # cantidad de margen transparente muy distinta (ej. Richard usa
        # un lienzo de 120x120 para un dibujo de 64x79, mientras que
        # Cobra usa 72x72 para 59x67) - eso hacía que unos personajes
        # se vieran mucho más chicos que otros al escalar por igual.
        # Recortamos al bounding box real del contenido, usando la
        # UNIÓN entre todos los frames del personaje (no cada frame
        # por separado) para que la animación no "salte" de tamaño.
        frame_paths = [os.path.join(char_dir, f"frame{i:02d}.png")
                        for i in range(len(frames))]
        min_x = min_y = 10**9
        max_x = max_y = 0
        for fp in frame_paths:
            geom = subprocess.run(
                ["identify", "-format", "%@", fp],
                check=True, capture_output=True, text=True,
            ).stdout.strip()
            # formato: WxH+X+Y
            wh, xy = geom.split("+", 1)
            fw, fh = (int(v) for v in wh.split("x"))
            fx, fy = (int(v) for v in xy.split("+"))
            min_x = min(min_x, fx)
            min_y = min(min_y, fy)
            max_x = max(max_x, fx + fw)
            max_y = max(max_y, fy + fh)

        pad = 4
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

        print(f"  ✓ {internal_name}: {len(frames)} frames -> {char_dir} "
              f"(recorte {crop_w}x{crop_h})")

    print(f"\nListo. Frames en: {out_dir}")


if __name__ == "__main__":
    main()
