#!/usr/bin/env python3
"""
Procedural sprite generator for Social Empires Clone.
Pillow ile temiz, izometrik tarzda sprite'lar üretir.

Katalogdaki tüm bina/birim tiplerini kapsar (worker, swordsman, mage,
barracks_*_1/2, arrow_tower_1/2 dahil). Gölge + katmanlı detay ekler.
"""

import os
from PIL import Image, ImageDraw

ASSETS_DIR = os.path.join(os.path.dirname(__file__), "..", "assets")


def save(img: Image.Image, subdir: str, name: str):
    path = os.path.join(ASSETS_DIR, subdir, name)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path, "PNG")
    print(f"  saved {path}")


def shade(color, d):
    return tuple(max(0, min(255, c + d)) for c in color)


def ground_shadow(draw, cx, cy, w, h):
    """Zemin gölgesi (yarı saydam elips)."""
    draw.ellipse([(cx - w // 2, cy - h // 2), (cx + w // 2, cy + h // 2)],
                 fill=(0, 0, 0, 70))


def iso_diamond(draw, cx, cy, w, h, fill, outline=None):
    points = [(cx, cy - h // 2), (cx + w // 2, cy), (cx, cy + h // 2), (cx - w // 2, cy)]
    draw.polygon(points, fill=fill, outline=outline)


def iso_box(draw, cx, cy, w, h, height, top_color, side_color, front_color):
    half_w, half_h = w // 2, h // 2
    draw.polygon([(cx, cy - half_h), (cx + half_w, cy), (cx, cy + half_h), (cx - half_w, cy)],
                 fill=top_color, outline=(0, 0, 0))
    draw.polygon([(cx, cy + half_h), (cx + half_w, cy), (cx + half_w, cy + height),
                  (cx, cy + half_h + height)], fill=side_color, outline=(0, 0, 0))
    draw.polygon([(cx, cy + half_h), (cx - half_w, cy), (cx - half_w, cy + height),
                  (cx, cy + half_h + height)], fill=front_color, outline=(0, 0, 0))


def generate_terrain():
    print("Generating terrain sprites...")
    size = (64, 32)
    for name, col in [("grass", (34, 139, 34)), ("dirt", (139, 90, 43)), ("water", (30, 144, 255))]:
        img = Image.new("RGBA", size, (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        iso_diamond(d, 32, 16, 64, 32, fill=col, outline=shade(col, -30))
        # hafif doku noktaları
        if name == "grass":
            for px, py in [(24, 14), (40, 18), (32, 20), (28, 10)]:
                d.line([(px, py), (px, py - 3)], fill=shade(col, -25))
        elif name == "water":
            d.line([(20, 16), (30, 14)], fill=shade(col, 40))
            d.line([(36, 18), (46, 16)], fill=shade(col, 40))
        save(img, "terrain", f"{name}.png")


def _draw_building(name, roof_color, side=(140, 140, 140), front=(100, 100, 100),
                   w=56, h=28, height=28, level=1, flag=None, tower=False):
    size = (96, 88)
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cx, cy = 48, 30
    ground_shadow(d, cx, cy + height // 2 + 8, w + 12, 18)
    if tower:
        iso_box(d, cx, cy, 36, 18, height, roof_color, side, front)
        # tepe siperleri
        d.rectangle([(cx - 20, cy - 12), (cx + 20, cy - 6)], fill=shade(roof_color, -20))
    else:
        iso_box(d, cx, cy, w, h, height, roof_color, side, front)
    # kapı
    d.rectangle([(cx - 5, cy + h // 2 + height - 14), (cx + 5, cy + h // 2 + height - 2)],
                fill=(70, 45, 20))
    # seviye göstergesi (bayrak/pip)
    if flag:
        d.line([(cx, cy - h // 2), (cx, cy - h // 2 - 14)], fill=(90, 60, 30), width=2)
        d.polygon([(cx, cy - h // 2 - 14), (cx + 10, cy - h // 2 - 10),
                   (cx, cy - h // 2 - 6)], fill=flag)
    for i in range(level - 1):
        d.ellipse([(cx - 18 + i * 8, cy - 2), (cx - 12 + i * 8, cy + 4)], fill=(255, 215, 0))
    save(img, "buildings", f"{name}.png")


def generate_buildings():
    print("Generating building sprites...")
    # Town Hall
    _draw_building("townhall", (160, 120, 70), (150, 100, 55), (110, 70, 35),
                   w=64, h=32, height=40, level=1, flag=(220, 40, 40))
    # House
    _draw_building("house", (190, 140, 100), (160, 100, 60), (120, 70, 35),
                   w=46, h=23, height=22)
    # Kaynak binaları
    _draw_building("woodcutter", (60, 130, 60), (50, 110, 50), (35, 80, 35))
    _draw_building("quarry", (150, 150, 150), (130, 130, 130), (95, 95, 95))
    _draw_building("farm", (240, 200, 60), (220, 180, 50), (180, 150, 30))
    _draw_building("gold_mine", (230, 185, 60), (210, 165, 45), (170, 130, 25))
    # Barakalar (renk = sınıf, level = pip + bayrak)
    barracks = {
        "spear": (110, 110, 150),
        "sword": (150, 110, 110),
        "archer": (110, 150, 110),
    }
    for cls, roof in barracks.items():
        for lvl in (1, 2):
            flag = (220, 40, 40) if lvl == 2 else None
            _draw_building(f"barracks_{cls}_{lvl}", roof, shade(roof, -25), shade(roof, -55),
                           w=56, h=28, height=30, level=lvl, flag=flag)
        # eski isim (geriye dönük)
        _draw_building(f"barracks_{cls}", roof, shade(roof, -25), shade(roof, -55))
    # eski rider barakası
    _draw_building("barracks_rider", (140, 120, 90), (120, 100, 75), (90, 75, 55))
    # Kuleler
    for lvl in (1, 2):
        flag = (60, 120, 220) if lvl == 2 else None
        _draw_building(f"arrow_tower_{lvl}", (120, 120, 140), (100, 100, 120),
                       (75, 75, 95), height=44 + lvl * 6, level=lvl, flag=flag, tower=True)


def _new_unit_canvas():
    img = Image.new("RGBA", (32, 36), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    ground_shadow(d, 16, 31, 18, 8)
    return img, d


def _draw_weapon(d, weapon, dx=0, dy=0):
    """Silahı verilen ofsetle çizer (animasyon kareleri için)."""
    def L(p1, p2, **kw):
        d.line([(p1[0] + dx, p1[1] + dy), (p2[0] + dx, p2[1] + dy)], **kw)

    def P(pts, **kw):
        d.polygon([(x + dx, y + dy) for x, y in pts], **kw)

    def A(box, **kw):
        d.arc([(box[0] + dx, box[1] + dy), (box[2] + dx, box[3] + dy)], **kw)

    def E(box, **kw):
        d.ellipse([(box[0] + dx, box[1] + dy), (box[2] + dx, box[3] + dy)], **kw)

    def R(box, **kw):
        d.rectangle([(box[0] + dx, box[1] + dy), (box[2] + dx, box[3] + dy)], **kw)

    if weapon == "spear":
        L((26, -2), (24, 30), fill=(180, 180, 190), width=2)
        P([(26, -4), (29, 1), (24, 0)], fill=(200, 200, 210))
    elif weapon == "sword":
        L((25, 10), (25, 26), fill=(210, 210, 220), width=3)
        L((22, 12), (28, 12), fill=(120, 90, 40), width=2)
    elif weapon == "bow":
        A((22, 8, 30, 28), start=300, end=60, fill=(150, 100, 50), width=2)
        L((26, 9), (26, 27), fill=(220, 220, 220))
    elif weapon == "club":
        L((24, 12), (28, 26), fill=(110, 70, 40), width=3)
        E((25, 22, 31, 30), fill=(90, 60, 35))
    elif weapon == "tool":  # worker
        L((25, 10), (25, 24), fill=(120, 80, 40), width=2)
        R((23, 8, 28, 12), fill=(160, 160, 170))
    elif weapon == "staff":  # mage
        L((26, 6), (24, 28), fill=(120, 80, 40), width=2)
        E((23, 2, 30, 9), fill=(120, 220, 255))


def _draw_body(d, color, body_dy=0, leg=0, legs=False):
    outline = shade(color, -50)
    if legs:
        d.line([(13, 28 + body_dy), (13 - leg, 33)], fill=outline, width=2)
        d.line([(19, 28 + body_dy), (19 + leg, 33)], fill=outline, width=2)
    d.ellipse([(8, 14 + body_dy), (24, 30 + body_dy)], fill=color, outline=outline)
    head = shade(color, 30)
    d.ellipse([(10, 5 + body_dy), (22, 17 + body_dy)], fill=head, outline=outline)
    d.ellipse([(13, 9 + body_dy), (15, 11 + body_dy)], fill=(255, 255, 255))
    d.ellipse([(17, 9 + body_dy), (19, 11 + body_dy)], fill=(255, 255, 255))
    d.point((14, 10 + body_dy), fill=(0, 0, 0))
    d.point((18, 10 + body_dy), fill=(0, 0, 0))


def _draw_punch(d, color, extend):
    """Köylü yumruğu: ileri uzanan kol + yumruk."""
    skin = shade(color, 45)
    hx = 24 + extend
    d.line([(22, 20), (hx, 18)], fill=shade(color, -30), width=3)
    d.ellipse([(hx - 2, 15), (hx + 4, 21)], fill=skin, outline=shade(color, -50))


def _draw_unit(name, color, weapon="none"):
    # idle (base)
    img, d = _new_unit_canvas()
    _draw_body(d, color)
    _draw_weapon(d, weapon)
    save(img, "units", f"{name}.png")

    # yürüme (gövde zıplaması + bacaklar + silah sallanışı)
    for i, (dy, leg, wdx) in enumerate([(-1, 2, 1), (0, -2, -1)]):
        img, d = _new_unit_canvas()
        _draw_body(d, color, body_dy=dy, leg=leg, legs=True)
        _draw_weapon(d, weapon, dx=wdx, dy=dy)
        save(img, "units", f"{name}_walk_{i}.png")

    # saldırı / yumruk
    if name == "worker":
        for i, ext in enumerate([0, 6]):
            img, d = _new_unit_canvas()
            _draw_body(d, color)
            _draw_punch(d, color, ext)
            save(img, "units", f"{name}_attack_{i}.png")
    else:
        for i, (wdx, wdy) in enumerate([(-2, -3), (3, 2)]):
            img, d = _new_unit_canvas()
            _draw_body(d, color)
            _draw_weapon(d, weapon, dx=wdx, dy=wdy)
            save(img, "units", f"{name}_attack_{i}.png")


def generate_units():
    print("Generating unit sprites...")
    units = [
        ("worker", (180, 150, 90), "tool"),
        ("spearman", (60, 120, 230), "spear"),
        ("swordsman", (90, 110, 220), "sword"),
        ("rider", (60, 160, 200), "sword"),
        ("archer", (60, 200, 150), "bow"),
        ("mage", (150, 90, 220), "staff"),
        ("troll_knife", (200, 70, 70), "sword"),
        ("troll_club", (180, 50, 50), "club"),
        ("troll_archer", (170, 60, 60), "bow"),
    ]
    for name, color, weapon in units:
        _draw_unit(name, color, weapon)


def generate_effects():
    print("Generating effect sprites...")
    size = (28, 34)
    flames = [
        [(14, 32), (8, 18), (12, 21), (14, 7), (16, 21), (20, 18)],
        [(14, 32), (9, 20), (13, 17), (14, 5), (15, 17), (19, 20)],
        [(14, 32), (7, 19), (12, 23), (14, 9), (17, 22), (21, 19)],
    ]
    inners = [
        [(14, 29), (11, 20), (14, 12), (17, 20)],
        [(14, 28), (12, 19), (14, 10), (16, 19)],
        [(14, 30), (11, 21), (14, 13), (18, 21)],
    ]
    for i, (outer, inner) in enumerate(zip(flames, inners)):
        img = Image.new("RGBA", size, (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        d.polygon(outer, fill=(220, 80, 20))
        d.polygon(inner, fill=(255, 180, 40))
        d.polygon([(14, 26), (13, 21), (14, 15), (15, 21)], fill=(255, 240, 160))
        save(img, "effects", f"fire_{i}.png")


def generate_resources():
    print("Generating resource node sprites...")
    size = (32, 36)

    def base():
        img = Image.new("RGBA", size, (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        ground_shadow(d, 16, 31, 20, 8)
        return img, d

    img, d = base()
    d.rectangle([(14, 20), (18, 31)], fill=(101, 67, 33))
    d.polygon([(16, 4), (27, 21), (5, 21)], fill=(34, 139, 34), outline=(20, 100, 20))
    d.polygon([(16, 10), (24, 23), (8, 23)], fill=(50, 165, 50))
    save(img, "terrain", "wood_node.png")

    img, d = base()
    d.polygon([(8, 29), (12, 14), (20, 10), (26, 20), (24, 29)], fill=(128, 128, 128), outline=(80, 80, 80))
    d.polygon([(12, 14), (20, 10), (18, 18), (10, 20)], fill=(165, 165, 165))
    save(img, "terrain", "stone_node.png")

    img, d = base()
    d.rectangle([(15, 22), (17, 31)], fill=(139, 90, 43))
    d.polygon([(16, 6), (22, 22), (10, 22)], fill=(255, 215, 0), outline=(200, 160, 0))
    d.polygon([(14, 10), (18, 10), (16, 22)], fill=(245, 205, 60))
    save(img, "terrain", "food_node.png")

    img, d = base()
    d.polygon([(8, 29), (12, 14), (20, 10), (26, 20), (24, 29)], fill=(180, 140, 40), outline=(120, 90, 20))
    d.polygon([(12, 14), (20, 10), (18, 18), (10, 20)], fill=(225, 175, 45))
    save(img, "terrain", "gold_node.png")

    img, d = base()
    d.polygon([(16, 4), (24, 16), (16, 30), (8, 16)], fill=(138, 43, 226), outline=(80, 20, 150))
    d.polygon([(16, 8), (20, 16), (16, 25), (12, 16)], fill=(175, 95, 245))
    save(img, "terrain", "gem_node.png")


def generate_construction():
    """Generate construction site scaffolding sprite."""
    print("Generating construction sprite...")
    size = (96, 88)
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cx, cy = 48, 30

    # Ground shadow
    ground_shadow(d, cx, cy + 20, 60, 20)

    # Scaffolding frame (wooden beams)
    beam_color = (160, 120, 70)
    beam_dark = (120, 85, 45)

    # Vertical posts
    for ox in (-20, 0, 20):
        d.rectangle([(cx + ox - 3, cy - 10), (cx + ox + 3, cy + 40)],
                    fill=beam_color, outline=beam_dark)

    # Horizontal cross beams
    for oy in (0, 15, 30):
        d.rectangle([(cx - 23, cy + oy - 2), (cx + 23, cy + oy + 2)],
                    fill=beam_color, outline=beam_dark)

    # Diagonal X-braces
    d.line([(cx - 20, cy), (cx + 20, cy + 15)], fill=beam_dark, width=2)
    d.line([(cx + 20, cy), (cx - 20, cy + 15)], fill=beam_dark, width=2)
    d.line([(cx - 20, cy + 15), (cx + 20, cy + 30)], fill=beam_dark, width=2)
    d.line([(cx + 20, cy + 15), (cx - 20, cy + 30)], fill=beam_dark, width=2)

    # Foundation blocks
    d.polygon([(cx - 25, cy + 35), (cx, cy + 45), (cx + 25, cy + 35), (cx, cy + 25)],
              fill=(100, 80, 60), outline=(70, 55, 40))

    save(img, "buildings", "construction.png")


def generate_resource_phases():
    """Generate depleted and growing phases for all resource types."""
    print("Generating resource phase sprites...")
    size = (32, 36)

    def base():
        img = Image.new("RGBA", size, (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        ground_shadow(d, 16, 31, 20, 8)
        return img, d

    # Wood phases
    img, d = base()
    d.rectangle([(14, 22), (18, 31)], fill=(120, 80, 50))  # cut trunk
    d.polygon([(16, 22), (20, 28), (12, 28)], fill=(160, 110, 70))  # stump top
    d.ellipse([(12, 28), (20, 32)], fill=(101, 67, 33))  # soil
    save(img, "terrain", "wood_node_stump.png")

    img, d = base()
    d.rectangle([(15, 24), (17, 31)], fill=(101, 67, 33))
    d.polygon([(16, 14), (20, 24), (12, 24)], fill=(60, 160, 60), outline=(40, 120, 40))  # small sprout
    save(img, "terrain", "wood_node_sapling.png")

    # Stone phases
    img, d = base()
    d.ellipse([(12, 26), (20, 32)], fill=(139, 119, 101))  # dirt/fragments
    d.polygon([(14, 28), (16, 24), (18, 28)], fill=(160, 140, 120))  # tiny rock
    save(img, "terrain", "stone_node_stump.png")

    img, d = base()
    d.polygon([(10, 28), (14, 18), (20, 16), (24, 26), (22, 30)],
              fill=(140, 140, 140), outline=(100, 100, 100))  # medium rock
    d.polygon([(14, 18), (20, 16), (18, 24), (12, 26)], fill=(170, 170, 170))
    save(img, "terrain", "stone_node_sapling.png")

    # Food phases
    img, d = base()
    d.ellipse([(10, 26), (22, 34)], fill=(101, 80, 50))  # empty soil
    save(img, "terrain", "food_node_stump.png")

    img, d = base()
    d.rectangle([(15, 24), (17, 31)], fill=(139, 90, 43))
    d.polygon([(16, 16), (19, 24), (13, 24)], fill=(255, 215, 0), outline=(200, 160, 0))  # small yellow plant
    save(img, "terrain", "food_node_sapling.png")

    # Gold phases
    img, d = base()
    d.ellipse([(11, 26), (21, 34)], fill=(160, 130, 80))  # dirt mound
    d.point([(13, 29), (17, 30), (15, 32)], fill=(200, 170, 50))  # tiny specks
    save(img, "terrain", "gold_node_stump.png")

    img, d = base()
    d.polygon([(10, 30), (14, 18), (20, 16), (24, 24), (22, 30)],
              fill=(180, 140, 50), outline=(130, 100, 30))  # small nuggets
    d.polygon([(14, 18), (20, 16), (18, 26), (12, 28)], fill=(210, 170, 60))
    save(img, "terrain", "gold_node_sapling.png")

    # Gem phases
    img, d = base()
    d.ellipse([(11, 26), (21, 34)], fill=(80, 60, 90))  # dark soil
    d.point([(14, 29), (17, 31)], fill=(138, 43, 226))  # faint sparkle
    save(img, "terrain", "gem_node_stump.png")

    img, d = base()
    d.polygon([(14, 18), (18, 14), (20, 22), (16, 26)],
              fill=(160, 100, 210), outline=(100, 50, 150))  # small crystal
    d.polygon([(16, 20), (19, 17), (20, 24), (17, 26)], fill=(190, 130, 240))
    save(img, "terrain", "gem_node_sapling.png")


def main():
    print("=== Procedural Sprite Generator ===")
    generate_terrain()
    generate_buildings()
    generate_units()
    generate_resources()
    generate_effects()
    generate_construction()
    generate_resource_phases()
    print("=== Done ===")


if __name__ == "__main__":
    main()
