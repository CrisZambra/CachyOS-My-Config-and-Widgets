#!/usr/bin/env python3
"""
extract-character.py

Extrae TODOS los sprites (con la paleta por defecto, la #0) de un
personaje de Guilty Gear XX Accent Core Plus R, desde el .bin del
propio juego instalado (Resource/obj/<código>.bin - "sl"=Sol Badguy,
"ky"=Ky Kiske, etc; los que empiezan con "e" son la variante EX).

El formato de archivo (cifrado, contenedor, compresión, paletas) no
está documentado oficialmente: esto es un port a Python del código de
saltern/ggpr_bin (https://github.com/saltern/ggpr_bin), la librería
Rust detrás de GearStudio, la herramienta de modding de la comunidad
para este juego.

Uso:
    python3 extract-character.py \
        "$HOME/.local/share/Steam/steamapps/common/Guilty Gear XX Accent Core Plus R/Resource/obj/sl.bin" \
        ~/Documents/ggxx-sprites/Sol

No mapea movimientos (no existe ninguna tabla pública que diga "el
sprite tal es el Golpe/Patada/etc. de tal personaje" - ver README) -
solo saca todos los sprites numerados para elegir a mano cuáles usar.
"""
import struct
import sys
from pathlib import Path

from PIL import Image

MERSENNE_LENGTH = 624
MERSENNE_INIT = 0x6C078965
LAST_OUT = 0x43415046
ENCRYPTED_SIGNATURE = 0x41534743
MASK32 = 0xFFFFFFFF


class MersenneTwister:
    def __init__(self, seed):
        self.table = [seed]
        for i in range(1, MERSENNE_LENGTH):
            prev = self.table[i - 1]
            self.table.append((MERSENNE_INIT * (prev ^ (prev >> 30)) + i) & MASK32)
        self.index = MERSENNE_LENGTH

    def twist(self):
        for i in range(MERSENNE_LENGTH):
            value = (self.table[i] & 0x80000000) + (self.table[(i + 1) % MERSENNE_LENGTH] & 0x7FFFFFFF)
            self.table[i] = self.table[(i + 397) % MERSENNE_LENGTH] ^ (value >> 1)
            if value & 1:
                self.table[i] ^= 0x9908B0DF
        self.index = 0

    def next(self):
        if self.index >= MERSENNE_LENGTH:
            self.twist()
        value = self.table[self.index]
        value ^= value >> 11
        value ^= (value << 7) & 0x9D2C5680
        value ^= (value << 15) & 0xEFC60000
        value ^= value >> 18
        self.index += 1
        return value & MASK32


def decrypt_file(filename: str, data: bytes) -> bytes:
    seed = 0
    for b in filename.upper().encode("ascii"):
        seed = (seed * 137 + b) & MASK32
    twister = MersenneTwister(seed)
    last_out = LAST_OUT
    out = bytearray()
    cursor = 0
    n = len(data)
    while cursor + 4 <= n:
        value_in = struct.unpack_from("<I", data, cursor)[0]
        last_out = (last_out ^ value_in ^ twister.next()) & MASK32
        out += struct.pack("<I", last_out)
        cursor += 4
    return bytes(out)


def get_pointers(data: bytes, cursor: int = 0):
    pointers = []
    while cursor + 3 < len(data):
        ptr = struct.unpack_from("<I", data, cursor)[0]
        if ptr == 0xFFFFFFFF:
            break
        pointers.append(ptr)
        cursor += 4
    return pointers


def get_header(data: bytes):
    mode = struct.unpack_from("<H", data, 0x00)[0]
    if data[0x00] > 0x05:
        compressed = ((mode & 0xF000) >> 8) != 0
        hi_lo_nibble = (mode & 0xF00) >> 8
        if hi_lo_nibble == 0x0F:
            clut = 0x00
        elif hi_lo_nibble == 0x00:
            clut = 0x20
        else:
            clut = 0x10
        bit_depth = 8 if (mode & 0xF) == 3 else 4
        width = struct.unpack_from("<H", data, 0x02)[0]
        height = struct.unpack_from("<H", data, 0x04)[0]
    else:
        compressed = mode > 0x00
        clut = struct.unpack_from("<H", data, 0x02)[0]
        bit_depth = struct.unpack_from("<H", data, 0x04)[0]
        width = struct.unpack_from("<H", data, 0x06)[0]
        height = struct.unpack_from("<H", data, 0x08)[0]
    return {
        "compressed": compressed, "mode": mode, "clut": clut,
        "bit_depth": bit_depth, "width": width, "height": height,
    }


def bpp_from_4(pixels: bytes):
    out = bytearray()
    for b in pixels:
        out.append(b & 0xF)
        out.append(b >> 4)
    return bytes(out)


def decompress_rplus(data: bytes, header):
    pointer = 0x10
    if header["clut"] == 0x20:
        pointer += (2 ** header["bit_depth"]) * 4
    iterations = struct.unpack_from("<I", bytes([
        data[pointer + 2], data[pointer + 3], data[pointer + 0], data[pointer + 1]
    ]), 0)[0]
    pointer += 4
    byte_data = bytearray()
    p = pointer
    while p + 1 < len(data):
        byte_data.append(data[p + 1])
        byte_data.append(data[p])
        p += 2
    bitbuf = int.from_bytes(byte_data, "big")
    total_bits = len(byte_data) * 8
    bitpos = 0

    def read_bits(n):
        nonlocal bitpos
        shift = total_bits - bitpos - n
        value = (bitbuf >> shift) & ((1 << n) - 1)
        bitpos += n
        return value

    pixel_vector = bytearray()
    pixel_count = header["width"] * header["height"]
    for _ in range(iterations):
        if read_bits(1):
            pixel_vector.append(read_bits(8))
            if len(pixel_vector) + 1 < pixel_count:
                pixel_vector.append(read_bits(8))
        else:
            window_origin = max(0, len(pixel_vector) - 512)
            offset = read_bits(9)
            length = 3 + read_bits(7)
            for i in range(length):
                pixel_vector.append(pixel_vector[window_origin + offset + i])
    if header["bit_depth"] == 4:
        pixel_vector = bytearray(bpp_from_4(bytes(pixel_vector)))
    pixel_vector = pixel_vector[:pixel_count]
    pixel_vector.extend([0] * (pixel_count - len(pixel_vector)))
    return bytes(pixel_vector)


def decompress_ggx(data: bytes, header):
    pointer = 0x10
    if header["clut"] != 0x00:
        color_count = 2 ** header["bit_depth"]
        if header["clut"] == 0x10:
            color_count //= 2
        pointer += color_count * 4
    pixel_vector = bytearray()
    pixel_count = header["width"] * header["height"]
    while len(pixel_vector) < pixel_count:
        b = data[pointer]
        if (b & 0xC0) == 0:
            for _ in range(b + 1):
                pointer += 1
                v = data[pointer]
                if header["bit_depth"] == 4:
                    pixel_vector.append(v & 0xF)
                    pixel_vector.append(v >> 4)
                else:
                    pixel_vector.append(v)
        else:
            token_count = (b + 0xC3) & 0xFF
            if header["bit_depth"] == 4:
                token_count *= 2
            last = pixel_vector[-1]
            for _ in range(token_count):
                pixel_vector.append(last)
        pointer += 1
    return bytes(pixel_vector[:pixel_count])


def get_embedded_palette(data: bytes, header):
    if header["clut"] == 0x00:
        return None
    color_count = 2 ** header["bit_depth"]
    if header["clut"] == 0x10:
        color_count //= 2
    return data[0x10:0x10 + color_count * 4]


def get_sprite_data(data: bytes):
    header = get_header(data[0x00:0x10])
    if header["compressed"]:
        if header["mode"] > 0x12:
            pixels = decompress_ggx(data, header)
        elif header["mode"] == 0x05:
            raise NotImplementedError("mode 5")
        else:
            pixels = decompress_rplus(data, header)
        palette = get_embedded_palette(data, header)
    else:
        palette = None
        if header["clut"] == 0x20:
            color_count = 2 ** header["bit_depth"]
            palette = data[0x10:0x10 + color_count * 4]
            pointer = 0x10 + color_count * 4
        else:
            pointer = 0x10
        pixels = data[pointer:]
        if header["bit_depth"] == 4:
            pixels = bpp_from_4(pixels)
        pixels = pixels[:header["width"] * header["height"]]
    return header, pixels, palette


def render_indexed(width, height, pixels: bytes, palette: bytes) -> Image.Image:
    img = Image.new("RGBA", (width, height))
    pal_colors = []
    for i in range(len(palette) // 4):
        r, g, b, a = palette[4 * i:4 * i + 4]
        a = 255 if a == 0x80 else min(255, a * 2)
        pal_colors.append((r, g, b, a))
    data = [pal_colors[p] if p < len(pal_colors) else (0, 0, 0, 0) for p in pixels]
    img.putdata(data)
    return img


def extract_character(src: Path, out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    raw = src.read_bytes()
    if struct.unpack_from("<I", bytes(raw[-4:][::-1]))[0] == ENCRYPTED_SIGNATURE:
        data = decrypt_file(src.name, raw)
    else:
        data = raw

    top_pointers = get_pointers(data)

    for obj_i, start in enumerate(top_pointers):
        end = top_pointers[obj_i + 1] if obj_i + 1 < len(top_pointers) else len(data)
        obj_data = data[start:end]
        obj_pointers = get_pointers(obj_data)

        if len(obj_pointers) != 4:
            continue

        cells_off, sprites_off, scripts_off, palettes_off = obj_pointers
        sprite_pointers = get_pointers(obj_data, sprites_off)
        palette_pointers = get_pointers(obj_data, palettes_off)

        if not sprite_pointers or not palette_pointers:
            continue

        # Cada paleta trae su propio encabezado de 16 bytes ANTES de
        # los colores (igual que el header de un sprite) - saltarlo
        # es necesario, si no los colores quedan todos corridos y el
        # personaje sale con una paleta que no es la suya.
        pal_cursor = palettes_off + palette_pointers[0]
        pal_color_count = 0x10 if obj_data[pal_cursor + 0x04] == 0x04 else 0x100
        default_palette = obj_data[pal_cursor + 0x10:pal_cursor + 0x10 + pal_color_count * 4]

        ok, failed = 0, 0
        for s in range(len(sprite_pointers)):
            s_start = sprites_off + sprite_pointers[s]
            s_end = sprites_off + sprite_pointers[s + 1] if s + 1 < len(sprite_pointers) else scripts_off
            sprite_bin = obj_data[s_start:s_end]
            try:
                header, pixels, embedded_pal = get_sprite_data(sprite_bin)
                pal = embedded_pal if embedded_pal else default_palette
                if header["width"] == 0 or header["height"] == 0:
                    failed += 1
                    continue
                img = render_indexed(header["width"], header["height"], pixels, pal)
                img.save(out_dir / f"sprite_{s:04d}.png")
                ok += 1
            except Exception as e:
                failed += 1
                print(f"  sprite {s}: FAILED ({e})")

        print(f"Object #{obj_i} (player): {ok} ok, {failed} failed, out={out_dir}")
        return True

    print("No player object found")
    return False


if __name__ == "__main__":
    extract_character(Path(sys.argv[1]), Path(sys.argv[2]))
