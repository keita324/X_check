#!/usr/bin/env python3
"""Build index.html: subset Noto Sans JP to the glyphs actually used, inline every asset."""
import base64, html, io, os, re, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT  = os.path.join(os.path.dirname(ROOT), 'index.html')
TMPL = os.path.join(ROOT, 'page.tmpl.html')
ASSETS   = os.path.join(ROOT, 'assets')
# Noto Sans JP variable (the face the official d ticket site uses). Not committed - fetch with:
#   curl -L -o build/NotoSansJP-VF.ttf \
#     https://raw.githubusercontent.com/notofonts/noto-cjk/main/Sans/Variable/TTF/Subset/NotoSansJP-VF.ttf
FONT_SRC = os.environ.get('NOTO_VF', os.path.join(ROOT, 'NotoSansJP-VF.ttf'))

tmpl = open(TMPL, encoding='utf-8').read()

# ---- 1. characters actually rendered -------------------------------------
visible = re.sub(r'<(style|script)\b.*?</\1>', ' ', tmpl, flags=re.S|re.I)
visible = re.sub(r'<[^>]+>', ' ', visible)
visible = html.unescape(visible)
chars = set(visible)

# safety net: full kana, ASCII, and the punctuation a future editor will reach for
chars |= set(chr(c) for c in range(0x20, 0x7F))                 # ASCII
chars |= set(chr(c) for c in range(0x3041, 0x309F))             # hiragana
chars |= set(chr(c) for c in range(0x30A0, 0x30FF))             # katakana
chars |= set('　、。・「」『』（）〈〉《》【】〔〕！？：；…‥ー－‐‑—–―～〜／＼％＋＝＜＞＊＃＆＠×÷±°′″©®™§¶†‡•◯○●◎△▲▽▼□■◇◆☆★※→←↑↓⇒⇔≪≫№℡㈱¥＄€£')
chars |= set('０１２３４５６７８９ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺ')
chars |= set('ａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚ')
chars.discard('\n'); chars.discard('\t'); chars.discard('\r')
text = ''.join(sorted(chars))
print(f'[font] {len(text)} unique characters requested')

# ---- 2. subset the variable font ----------------------------------------
from fontTools import subset as ftsubset
opts = ftsubset.Options()
opts.flavor = 'woff2'
opts.layout_features = ['kern', 'palt', 'vert', 'vrt2', 'liga', 'clig', 'ccmp', 'locl', 'mark', 'mkmk']
opts.name_IDs   = ['*']
opts.notdef_outline = True
opts.recalc_bounds  = True
opts.drop_tables    = ['DSIG']
font = ftsubset.load_font(FONT_SRC, opts)
sub = ftsubset.Subsetter(options=opts)
sub.populate(text=text)
sub.subset(font)
buf = io.BytesIO()
ftsubset.save_font(font, buf, opts)
font_bytes = buf.getvalue()
print(f'[font] subset woff2 = {len(font_bytes)/1024:.0f} KB '
      f'(from {os.path.getsize(FONT_SRC)/1024/1024:.1f} MB)')

# ---- 3. inline assets ----------------------------------------------------
MIME = {'.png':'image/png', '.jpg':'image/jpeg', '.jpeg':'image/jpeg',
        '.svg':'image/svg+xml', '.webp':'image/webp'}
def datauri(name):
    p = os.path.join(ASSETS, name)
    ext = os.path.splitext(name)[1].lower()
    b = open(p, 'rb').read()
    print(f'[img ] {name:26s} {len(b)/1024:6.0f} KB raw')
    return f'data:{MIME[ext]};base64,' + base64.b64encode(b).decode()

repl = {
    '__FONT_B64__'        : base64.b64encode(font_bytes).decode(),
    '__IMG_LOGO__'        : datauri('dticket-logo.png'),
    '__IMG_UI__'          : datauri('dticket-ui.jpg'),
    '__IMG_V_TOKYODOME__' : datauri('venue-tokyodome.jpg'),
    '__IMG_V_IGARENA__'   : datauri('venue-igarena.jpg'),
    '__IMG_V_KOKURITSU__' : datauri('venue-kokuritsu.jpg'),
    '__IMG_V_YOKOHAMA__'  : datauri('venue-yokohama.jpg'),
}
out = tmpl
for k, v in repl.items():
    if k not in out:
        sys.exit(f'ERROR: token {k} not found in template')
    out = out.replace(k, v)

left = re.findall(r'__[A-Z0-9_]+__', out)
if left:
    sys.exit(f'ERROR: unreplaced tokens {set(left)}')

open(OUT, 'w', encoding='utf-8').write(out)
print(f'\n[done] {OUT}  {os.path.getsize(OUT)/1024/1024:.2f} MB')
