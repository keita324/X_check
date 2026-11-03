#!/usr/bin/env python3
"""IPA公式の問題PDFから、問1〜問80の画像を切り出して media/ に保存する。

  python3 crop_from_pdf.py source/2022r04a_ap_am_qs.pdf

- PDFに埋め込まれたページ画像（200dpi）を pdfimages（poppler-utils）でそのまま取り出す。
  再圧縮以外の加工（文字の書換え・拡大縮小・色変更）は行わない。
- 各ページの行を検出し、左端が最も左にある行（「問N」で始まる行）を問題の開始とみなす。
  開始行から次の問題の開始直前（またはページ本文の末尾）までを1問として切り出す。
- 旧デッキの画像は一部の問題で下端が切れていた（秋期の例：問18・問22の選択肢ウ・エ）ため、
  このスクリプトで全問を作り直している。
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent
MEDIA = ROOT / "media"
FIRST_Q_PAGE = 2        # 0始まり。表紙・注意事項の次のページ
LAST_Q_PAGE = 34        # 問80があるページ（35〜38=メモ用紙, 39=裏表紙）
FOOTER_Y = 1900         # これより下はページ番号
PAD = 22


def lines(a):
    ink = a < 128
    rows = ink.sum(1)
    segs, inl, s = [], False, 0
    for y, v in enumerate(rows):
        if v > 2 and not inl:
            s, inl = y, True
        elif v <= 2 and inl:
            inl = False
            if y - s > 8:
                xs = np.where(ink[s:y].any(0))[0]
                segs.append((s, y, int(xs.min()), int(xs.max())))
    return [g for g in segs if g[0] < FOOTER_Y]


def main(pdf):
    MEDIA.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory() as td:
        subprocess.run(["pdfimages", "-j", pdf, f"{td}/p"], check=True)
        pages = {i: Image.open(f"{td}/p-{i:03d}.jpg").convert("L") for i in range(FIRST_Q_PAGE, LAST_Q_PAGE + 1)}
        pages = {i: im.copy() for i, im in pages.items()}
    starts = []  # (page, y_top, left_margin)
    page_lines = {}
    for i, im in pages.items():
        segs = lines(np.asarray(im))
        page_lines[i] = segs
        # 左端ぎりぎりの汚れ（スキャン時の影など）は余白判定から除外
        txt = [g for g in segs if 15 <= g[1] - g[0] <= 45 and g[2] >= 60]
        mn = min(g[2] for g in txt)
        a = np.asarray(im) < 128
        for g in txt:
            if g[2] > mn + 15:
                continue
            # 「問」は全角の大きな字なので、行頭30pxの中に縦18px以上のインクがあるはず（引用符などの誤検出を除外）
            ys = np.where(a[g[0]:g[1], g[2]:g[2] + 30].any(1))[0]
            if len(ys) and ys.max() - ys.min() >= 18:
                starts.append((i, g[0], mn))
    if len(starts) != 80:
        raise SystemExit(f"問題の開始行を80個検出できませんでした: {len(starts)}個")
    report = []
    for k, (p, y0, mn) in enumerate(starts):
        nxt = starts[k + 1] if k + 1 < len(starts) else None
        limit = nxt[1] if nxt and nxt[0] == p else FOOTER_Y
        body = [g for g in page_lines[p] if y0 <= g[0] < limit]
        y1 = max(g[1] for g in body)
        x0 = max(0, mn - PAD - 10)
        x1 = min(pages[p].width, max(max(g[3] for g in body) + PAD, x0 + 1150))
        bottom = min(pages[p].height, y1 + PAD)
        if nxt and nxt[0] == p:  # 次の問題の行に食い込まないようにする
            bottom = min(bottom, nxt[1] - 4)
        crop = pages[p].crop((x0, max(0, y0 - PAD), x1, bottom))
        name = f"ipa_r04h_q{k + 1:02d}.jpg"
        crop.save(MEDIA / name, quality=92, optimize=True)
        report.append(dict(no=k + 1, file=name, pdf_page=p + 1, y=[y0, y1], size=crop.size))
    (ROOT / "data" / "image_crops.json").write_text(json.dumps(report, ensure_ascii=False, indent=1), "utf-8")
    print(f"{len(report)} images written to {MEDIA}")


if __name__ == "__main__":
    main(sys.argv[1])
