#!/usr/bin/env python3
"""config/KobitoKey.keymap から README 用のレイヤー画像 (images/layer*.png) を生成する。

キーマップを変更したら必ずこのスクリプトを実行して画像を更新すること:

    python3 scripts/generate_keymap_images.py

依存: Pillow のみ (pip install pillow)。
フォント: DejaVu Sans Bold (英数字) + 日本語フォールバックフォント。

生成後、キーマップとスクリプトのハッシュを images/.keymap-hash に記録する。
CI (.github/workflows/keymap-images.yml) がこのハッシュを照合し、
キーマップだけ変更して画像を更新し忘れた場合はチェックが失敗する。

新しいビヘイビア/キーコードをキーマップで使うと、対応するラベルが
未定義の場合このスクリプトはエラーで停止する。KEY_LABELS などの辞書に
表示ラベルを追加してから再実行すること。
"""
import hashlib
import re
import subprocess
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    sys.exit("Pillow が必要です: pip install pillow (または venv を作成して導入)")

REPO = Path(__file__).resolve().parent.parent
KEYMAP = REPO / "config" / "KobitoKey.keymap"
OUTDIR = REPO / "images"
HASHFILE = OUTDIR / ".keymap-hash"

# ---------------------------------------------------------------- 描画仕様
# (既存の手作り画像 1280x690 をピクセル解析して合わせた値)
SS = 4                      # スーパーサンプリング倍率
W, H = 1280, 690
KEY = 67                    # キー一辺 px
RAD = 9                     # キー角丸半径
BODY = (30, 45, 52, 255)    # キー本体色
ORANGE = (243, 152, 0, 255) # キーラベル色
BLUE = (0, 161, 233, 255)   # コンボ枠色
WHITE = (255, 255, 255, 255)
BLACK = (26, 26, 26, 255)
COMBO_PAD = 6               # コンボ枠のはみ出し幅
COMBO_BRIDGE = 26           # コンボ2キー間をつなぐ帯の幅

MAIN_SIZE = 26              # メインラベル
SUB_SIZE = 16               # サブラベル (layerN / Option)
COMBO_SIZE = 23             # コンボラベル (ESC / 英数 など)
TITLE_SIZE = 23

# ラベルのベースライン位置 (キー中心からのオフセット)
BASE_SINGLE = 9.5           # 1行ラベル
BASE_MAIN = 2               # サブ付きのメインラベル
BASE_SUB = 21               # サブラベル
BASE_2LINE = (-3, 21)       # 2行ラベル (CLR ALL)

# 物理レイアウト: キーマップ順 (row-major 40キー) の (中心x, 中心y, 回転角)
KEYS = [
    (177.5, 306, 0), (263.5, 252.5, 0), (349, 231, 0), (434.5, 242, 0), (520.5, 252.5, 0),
    (758.5, 252.5, 0), (844, 242, 0), (930, 231, 0), (1015.5, 252.5, 0), (1101.5, 306, 0),
    (177.5, 392, 0), (263.5, 338.5, 0), (349, 317, 0), (434.5, 327.5, 0), (520.5, 338.5, 0),
    (758.5, 338.5, 0), (844, 327.5, 0), (930, 317, 0), (1015.5, 338.5, 0), (1101.5, 392, 0),
    (177.5, 477.5, 0), (263.5, 424, 0), (349, 402.5, 0), (434.5, 413, 0), (520.5, 424, 0),
    (758.5, 424, 0), (844, 413, 0), (930, 402.5, 0), (1015.5, 424, 0), (1101.5, 477.5, 0),
    (177.5, 563, 0), (263.5, 509.5, 0), (381, 509.5, 0), (474.9, 520.4, 14), (563.2, 553.4, 28),
    (715.6, 553.4, -28), (803.9, 520.3, -14), (897.5, 509.5, 0), (1015.5, 509.5, 0), (1101.5, 563, 0),
]

# ---------------------------------------------------------------- ラベル定義
# &kp のキーコード → 表示ラベル
KEY_LABELS = {
    **{c: c for c in "QWERTYUIOPASDFGHJKLZXCVBNM"},
    **{f"N{i}": str(i) for i in range(10)},
    "SEMI": ";", "COMMA": ",", "DOT": ".", "APOS": "'", "SLASH": "/",
    "MINUS": "-", "PLUS": "+", "EQUAL": "=", "ASTRK": "*",
    "LBKT": "[", "RBKT": "]", "BSLH": "\\", "GRAVE": "`",
    "TILDE": "~", "UNDER": "_", "PIPE": "|", "DQT": '"',
    "EXCL": "!", "AT": "@", "HASH": "#", "DLLR": "$", "PRCNT": "%",
    "CARET": "^", "AMPS": "&", "LPAR": "(", "RPAR": ")",
    "UP": "↑", "DOWN": "↓", "LEFT": "←", "RIGHT": "→",
    "LSHFT": "SHFT", "RSHFT": "SHFT", "LCTRL": "CTRL", "RCTRL": "CTRL",
    "LALT": "OPT", "RALT": "OPT", "LCMD": "CMD", "RCMD": "CMD",
    "SPACE": "SPC", "ENTER": "ENT", "BSPC": "BSPC", "DEL": "DEL",
    "TAB": "Tab", "ESC": "ESC", "LANG1": "かな", "LANG2": "英数",
}
# &mt の修飾キー → サブラベル
MOD_SUBLABELS = {"LALT": "Option", "RALT": "Option", "LCTRL": "Ctrl",
                 "LCMD": "Cmd", "LSHFT": "Shift"}

# レイヤーノード名 → タイトル表記 (None = "Layer N" のみ)
# 辞書にないノードはキーマップの label プロパティを使う
LAYER_TITLES = {
    "default_layer": None,
    "layer1": "Number&Bluetooth",
    "layer2": "SYMBOL & Arrow",
    "layer3": "AUTO MOUSE",
}

# 個別キーのラベル上書き {(レイヤー番号, キー位置): (メイン, サブ) or None}
# 既存デザイン踏襲: Layer 0 では LALT / 右手2つ目の SHFT を無地にしている
LABEL_OVERRIDES = {
    (0, 31): None,   # LALT
    (0, 38): None,   # RSHFT (2つ目)
}


def binding_label(b):
    """バインディング (例 ['&lt','1','SPACE']) → (メイン, サブ) or None"""
    try:
        head = b[0]
        if head in ("&trans", "&none"):
            return None
        if head == "&kp":
            return (KEY_LABELS[b[1]], None)
        if head == "&lt":
            return (KEY_LABELS[b[2]], f"layer{b[1]}")
        if head == "&mt":
            return (KEY_LABELS[b[2]], MOD_SUBLABELS[b[1]])
        if head == "&bt":
            if b[1] == "BT_SEL":
                return (f"BT{b[2]}", None)
            if b[1] == "BT_CLR":
                return ("CLR", None)
            if b[1] == "BT_CLR_ALL":
                return ("CLR\nALL", None)
        if head == "&mkp":
            return (b[1], None)
        if head == "&to":
            return (f"TO {b[1]}", None)
    except KeyError as e:
        raise ValueError(f"表示ラベル未定義のキーコード {e} (バインディング: {' '.join(b)})。"
                         f" scripts/generate_keymap_images.py の辞書に追加してください") from e
    raise ValueError(f"表示ラベル未定義のビヘイビア: {' '.join(b)}。"
                     f" scripts/generate_keymap_images.py の binding_label に追加してください")


# ---------------------------------------------------------------- keymap パース
def parse_keymap(text):
    """(layers, combos) を返す。
    layers: [(ノード名, label or None, [binding, ...40個])]
    combos: [([pos1, pos2], binding)]
    """
    layers, combos = [], []
    for m in re.finditer(r"(\w+)\s*\{([^{}]*)\}", text):
        name, body = m.group(1), m.group(2)
        bm = re.search(r"bindings\s*=\s*<([^>]*)>", body)
        if not bm:
            continue
        groups = []
        for tok in bm.group(1).split():
            if tok.startswith("&"):
                groups.append([tok])
            elif groups:
                groups[-1].append(tok)
        pm = re.search(r"key-positions\s*=\s*<([^>]*)>", body)
        if pm:  # combo 定義
            combos.append(([int(p) for p in pm.group(1).split()], groups[0]))
        else:   # レイヤー定義
            lm = re.search(r'label\s*=\s*"([^"]*)"', body)
            layers.append((name, lm.group(1) if lm else None, groups))
    return layers, combos


# ---------------------------------------------------------------- フォント
def find_font(candidates, fc_query):
    for c in candidates:
        if Path(c).exists():
            return c
    try:
        out = subprocess.run(["fc-match", "-f", "%{file}", fc_query],
                             capture_output=True, text=True, check=True).stdout.strip()
        if out and Path(out).exists():
            return out
    except Exception:
        pass
    sys.exit(f"フォントが見つかりません: {fc_query}")


FONT_LATIN = find_font(["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"],
                       "DejaVu Sans:bold")
FONT_JA = find_font(["/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf"],
                    ":lang=ja")


def font_for(text, size):
    ja = any(ord(ch) > 0x3000 for ch in text)
    return ImageFont.truetype(FONT_JA if ja else FONT_LATIN, size * SS), ja


# ---------------------------------------------------------------- 描画
def rot_rect_polygon(cx, cy, w, h, angle_deg):
    """中心(cx,cy)・幅w高h・回転angleの矩形の4頂点 (SS座標)"""
    import math
    a = math.radians(angle_deg)
    pts = []
    for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
        dx, dy = sx * w / 2, sy * h / 2
        pts.append(((cx + dx * math.cos(a) - dy * math.sin(a)) * SS,
                    (cy + dx * math.sin(a) + dy * math.cos(a)) * SS))
    return pts


def draw_key_body(big, draw, cx, cy, ang, size=KEY, rad=RAD, fill=BODY):
    if ang == 0:
        x0, y0 = (cx - size / 2) * SS, (cy - size / 2) * SS
        draw.rounded_rectangle([x0, y0, x0 + size * SS - 1, y0 + size * SS - 1],
                               radius=rad * SS, fill=fill)
    else:
        pad = 10
        lsize = (size + 2 * pad) * SS
        layer = Image.new("RGBA", (lsize, lsize), (0, 0, 0, 0))
        ld = ImageDraw.Draw(layer)
        o = pad * SS
        ld.rounded_rectangle([o, o, o + size * SS - 1, o + size * SS - 1],
                             radius=rad * SS, fill=fill)
        layer = layer.rotate(ang, resample=Image.BICUBIC, expand=False)
        big.alpha_composite(layer, (int(round(cx * SS - lsize / 2)),
                                    int(round(cy * SS - lsize / 2))))


def draw_label(draw, cx, cy, label):
    """(メイン, サブ) ラベルを水平に描く (既存画像同様、回転キーでも文字は水平)"""
    main, sub = label
    lines = main.split("\n")
    if len(lines) == 2:
        for ln, base in zip(lines, BASE_2LINE):
            fnt, _ = font_for(ln, MAIN_SIZE)
            draw.text((cx * SS, (cy + base) * SS), ln, font=fnt, fill=ORANGE, anchor="ms")
    else:
        base = BASE_MAIN if sub else BASE_SINGLE
        fnt, _ = font_for(main, MAIN_SIZE)
        draw.text((cx * SS, (cy + base) * SS), main, font=fnt, fill=ORANGE, anchor="ms")
    if sub:
        fnt, _ = font_for(sub, SUB_SIZE)
        draw.text((cx * SS, (cy + BASE_SUB) * SS), sub, font=fnt, fill=WHITE, anchor="ms")


def render_layer(index, node, label, bindings, combos):
    big = Image.new("RGBA", (W * SS, H * SS), WHITE)
    draw = ImageDraw.Draw(big)

    # タイトル
    title = LAYER_TITLES.get(node, label)
    text = f"Layer {index}" + (f"  “{title}”" if title else "")
    tfnt = ImageFont.truetype(FONT_LATIN, TITLE_SIZE * SS)
    draw.text((101 * SS, 69 * SS), text, font=tfnt, fill=BLACK, anchor="ls")

    # コンボ枠 (Layer 0 のみ): 2キーの膨張角丸矩形 + 中心間ブリッジをキーの下層に
    if index == 0:
        for positions, _ in combos:
            pts = [KEYS[p] for p in positions]
            for cx, cy, ang in pts:
                draw_key_body(big, draw, cx, cy, ang,
                              size=KEY + 2 * COMBO_PAD, rad=RAD + COMBO_PAD, fill=BLUE)
            if len(pts) == 2:
                import math
                (x1, y1, _), (x2, y2, _) = pts
                mx, my = (x1 + x2) / 2, (y1 + y2) / 2
                length = math.hypot(x2 - x1, y2 - y1)
                angle = math.degrees(math.atan2(y2 - y1, x2 - x1))
                draw.polygon(rot_rect_polygon(mx, my, length, COMBO_BRIDGE, angle),
                             fill=BLUE)

    # キー本体
    for cx, cy, ang in KEYS:
        draw_key_body(big, draw, cx, cy, ang)

    # キーラベル
    for pos, b in enumerate(bindings):
        label_ = LABEL_OVERRIDES.get((index, pos), ...)
        if label_ is ...:
            label_ = binding_label(b)
        elif label_ is not None and not isinstance(label_, tuple):
            label_ = (label_, None)
        if label_ is None:
            continue
        cx, cy, _ = KEYS[pos]
        draw_label(draw, cx, cy, label_)

    # コンボラベル (2キー中心の中点に白文字)
    if index == 0:
        for positions, binding in combos:
            lab = binding_label(binding)
            if not lab:
                continue
            xs = [KEYS[p][0] for p in positions]
            ys = [KEYS[p][1] for p in positions]
            mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
            fnt, ja = font_for(lab[0], COMBO_SIZE)
            # 日本語フォントに Bold がないため stroke で擬似ボールド化
            draw.text((mx * SS, my * SS), lab[0], font=fnt, fill=WHITE, anchor="mm",
                      stroke_width=SS // 2 if ja else 0, stroke_fill=WHITE)

    return big.convert("RGB").resize((W, H), Image.LANCZOS)


def current_hash():
    h = hashlib.sha256()
    h.update(KEYMAP.read_bytes())
    h.update(Path(__file__).read_bytes())
    return h.hexdigest()


def main():
    layers, combos = parse_keymap(KEYMAP.read_text())
    if not layers:
        sys.exit("キーマップからレイヤーを検出できませんでした")
    OUTDIR.mkdir(exist_ok=True)
    for i, (node, label, bindings) in enumerate(layers):
        if len(bindings) != len(KEYS):
            sys.exit(f"{node}: バインディング数 {len(bindings)} != {len(KEYS)}")
        img = render_layer(i, node, label, bindings, combos)
        out = OUTDIR / f"layer{i}.png"
        img.save(out)
        print(f"generated {out.relative_to(REPO)}")
    HASHFILE.write_text(current_hash() + "\n")
    print(f"updated {HASHFILE.relative_to(REPO)}")


if __name__ == "__main__":
    main()
