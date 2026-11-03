#!/usr/bin/env python3
"""応用情報 R5春 午前80問 Ankiデッキ生成スクリプト.

使い方:
    pip install genanki pyyaml pillow
    python3 build_deck.py            # output/AP_R5_Spring_80Q_Enhanced.apkg を生成
    python3 build_deck.py --only 3 15  # 指定問題だけのデッキを試作（確認用）

解説データ: data/explanations/qNN.yaml （1問1ファイル。誤りを見つけたらそのファイルだけ直して再実行）
問題画像:   media/ipa_r05h_qNN.jpg （IPA公式PDFから切り出した画像）
メタ情報:   data/questions_meta.json （公式正解・前回の学習結果・分野）

YAML本文の簡易記法:
    空行          → 段落区切り
    "- " で始まる行 → 箇条書き
    "1. " など    → 番号付き手順
    "| " で始まる行 → 計算式ブロック（等幅・枠付き）
    HTMLタグ（<b>, <sup>, <sub> など）はそのまま使用可
"""
import argparse
import html
import json
import re
import sys
from pathlib import Path

import genanki
import yaml

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
EXPL = DATA / "explanations"
MEDIA = ROOT / "media"
OUT = ROOT / "output"

# --- 固定ID（再生成しても同じIDになるので、Ankiに再インポートすると既存カードが更新される） ---
MODEL_ID = 1730000000821   # R4秋(…801)・R4春(…811)とは別のノートタイプ
DECK_ID = 1730000000822
DECK_NAME = "応用情報 R5春 午前80問 詳細解説版"
CHOICES = ["ア", "イ", "ウ", "エ"]

FIELDS = [
    "問番号", "問題画像", "正解", "テーマ", "基礎知識", "考え方",
    "選択肢解説", "具体例", "復習ポイント", "前回結果", "分野",
]

QFMT = """
<div class="meta">令和5年度 春期 応用情報技術者試験 午前｜問{{問番号}}</div>
<div class="qimg" onclick="this.classList.toggle('zoom')">{{問題画像}}</div>
<div class="hint">※画像をタップすると拡大（横スクロール）／もう一度タップで元に戻る</div>
<div class="credit">問題文・図表：IPA「令和5年度 春期 応用情報技術者試験 午前問題」原文画像</div>
"""

AFMT = """
{{FrontSide}}
<hr id="answer">
<div class="answer">正解：{{正解}}</div>
<div class="tags-line">{{#前回結果}}前回：{{前回結果}} ／ {{/前回結果}}{{分野}}</div>
{{#テーマ}}<div class="sec"><div class="h">① この問題のテーマ</div>{{テーマ}}</div>{{/テーマ}}
{{#基礎知識}}<div class="sec"><div class="h">② まず知っておきたい基礎知識</div>{{基礎知識}}</div>{{/基礎知識}}
{{#考え方}}<div class="sec"><div class="h">③ 正解までの考え方</div>{{考え方}}</div>{{/考え方}}
{{#選択肢解説}}<div class="sec"><div class="h">④ 選択肢別の解説</div>{{選択肢解説}}</div>{{/選択肢解説}}
{{#具体例}}<div class="sec"><div class="h">⑤ 具体例・イメージ</div>{{具体例}}</div>{{/具体例}}
{{#復習ポイント}}<div class="sec review"><div class="h">⑥ この問題の復習ポイント</div>{{復習ポイント}}</div>{{/復習ポイント}}
<div class="credit">解説は学習用に独自作成。正解はIPA公式解答例と照合済み。</div>
"""

CSS = """
.card{font-family:-apple-system,BlinkMacSystemFont,"Hiragino Sans","Hiragino Kaku Gothic ProN","Noto Sans JP",sans-serif;
 font-size:17px;line-height:1.75;text-align:left;color:#1d2731;background:#fff;padding:8px 10px;max-width:860px;margin:0 auto;
 word-break:break-word;overflow-wrap:anywhere;}
.nightMode.card,.nightMode .card,.night_mode.card,.night_mode .card{color:#e4e8ec;background:#1e1e1e;}
.meta{font-size:14px;color:#527083;margin-bottom:6px;font-weight:bold;}
.qimg img{display:block;width:100%;max-width:860px;height:auto;margin:0 auto;border:1px solid #d5dde3;border-radius:4px;background:#fff;}
.nightMode .qimg img{filter:none;}
.qimg{overflow-x:auto;-webkit-overflow-scrolling:touch;}
.qimg.zoom img{width:180%;max-width:none;}
.hint{font-size:11px;color:#8a979d;}
.credit{font-size:11px;color:#7b8a91;margin-top:6px;}
.answer{font-size:26px;font-weight:bold;color:#087a55;margin:12px 0 2px;}
.nightMode .answer{color:#68e0aa;}
.tags-line{font-size:13px;color:#6a7a83;margin-bottom:8px;}
.sec{margin:16px 0;}
.sec .h{font-weight:bold;font-size:17px;margin:0 0 6px;padding:3px 8px;border-left:5px solid #2781b8;background:#eef5fa;}
.nightMode .sec .h{background:#24323d;border-left-color:#5aa8dd;}
.sec p{margin:6px 0;}
.sec ul,.sec ol{margin:6px 0;padding-left:1.4em;}
.sec li{margin:4px 0;}
.calc{font-family:"SFMono-Regular",Menlo,Consolas,"Hiragino Sans",monospace;font-size:15px;background:#f6f8fa;border:1px solid #dde3e8;
 border-radius:6px;padding:6px 10px;margin:6px 0;overflow-x:auto;line-height:1.7;}
.nightMode .calc{background:#2a2f35;border-color:#3d454d;}
.calc div{white-space:pre-wrap;}
.choice{margin:8px 0;padding:6px 8px;border:1px solid #e1e6ea;border-radius:6px;}
.choice.ok{border-color:#2fa37a;background:#effaf5;}
.nightMode .choice{border-color:#3d454d;}
.nightMode .choice.ok{background:#1f3a30;border-color:#3cb58a;}
.choice .lbl{display:inline-block;min-width:1.6em;font-weight:bold;margin-right:4px;}
.choice .mark{font-size:13px;font-weight:bold;margin-right:4px;}
.choice.ok .mark{color:#087a55;} .choice.ng .mark{color:#b3423a;}
.nightMode .choice.ok .mark{color:#68e0aa;} .nightMode .choice.ng .mark{color:#ff8f86;}
.review{border:2px solid #f0b429;border-radius:8px;padding:4px 8px 6px;background:#fffaf0;}
.review .h{border-left-color:#f0b429;background:#fff1cf;}
.nightMode .review{background:#2d2717;border-color:#b98a1f;}
.nightMode .review .h{background:#3a321b;}
table.t{border-collapse:collapse;margin:6px 0;font-size:15px;}
table.t td,table.t th{border:1px solid #c9d2d8;padding:3px 7px;}
"""

_LIST_RE = re.compile(r"^(\d+)\.\s+(.*)$")


def render(text: str) -> str:
    """簡易記法 → HTML。"""
    if not text:
        return ""
    out = []
    blocks = re.split(r"\n\s*\n", text.strip())
    for block in blocks:
        lines = [ln.rstrip() for ln in block.split("\n") if ln.strip()]
        i = 0
        while i < len(lines):
            ln = lines[i]
            if ln.startswith("| "):
                buf = []
                while i < len(lines) and lines[i].startswith("| "):
                    buf.append(f"<div>{lines[i][2:]}</div>")
                    i += 1
                out.append('<div class="calc">' + "".join(buf) + "</div>")
            elif ln.startswith("- "):
                buf = []
                while i < len(lines) and lines[i].startswith("- "):
                    buf.append(f"<li>{lines[i][2:]}</li>")
                    i += 1
                out.append("<ul>" + "".join(buf) + "</ul>")
            elif _LIST_RE.match(ln):
                buf = []
                start = int(_LIST_RE.match(ln).group(1))
                while i < len(lines) and (_LIST_RE.match(lines[i]) or lines[i].startswith("| ")):
                    if lines[i].startswith("| "):  # 手順の中の計算式ブロック
                        calc = []
                        while i < len(lines) and lines[i].startswith("| "):
                            calc.append(f"<div>{lines[i][2:]}</div>")
                            i += 1
                        if buf:
                            buf[-1] = buf[-1][:-5] + '<div class="calc">' + "".join(calc) + "</div></li>"
                        continue
                    buf.append(f"<li>{_LIST_RE.match(lines[i]).group(2)}</li>")
                    i += 1
                attr = f' start="{start}"' if start != 1 else ""
                out.append(f"<ol{attr}>" + "".join(buf) + "</ol>")
            else:
                buf = []
                while i < len(lines) and not (lines[i].startswith(("| ", "- ")) or _LIST_RE.match(lines[i])):
                    buf.append(lines[i])
                    i += 1
                out.append("<p>" + "<br>".join(buf) + "</p>")
    return "".join(out)


def render_choices(choices: dict, answer: str) -> str:
    parts = []
    for c in CHOICES:
        if c not in choices:
            continue
        ok = c == answer
        cls = "ok" if ok else "ng"
        mark = "○ 正解" if ok else "× 誤り"
        parts.append(
            f'<div class="choice {cls}"><span class="lbl">{c}</span>'
            f'<span class="mark">{mark}</span>{render(str(choices[c]))}</div>'
        )
    # 個別解説が不要な問題用の補足
    if "共通" in choices:
        parts.append(render(str(choices["共通"])))
    return "".join(parts)


def load_all(only=None):
    meta = {m["no"]: m for m in json.loads((DATA / "questions_meta.json").read_text("utf-8"))}
    items = []
    for no in sorted(meta):
        if only and no not in only:
            continue
        path = EXPL / f"q{no:02d}.yaml"
        if not path.exists():
            raise SystemExit(f"解説ファイルがありません: {path}")
        y = yaml.safe_load(path.read_text("utf-8"))
        if y.get("q") != no:
            raise SystemExit(f"{path}: q（問題番号）が一致しません")
        if y["answer"] != meta[no]["official_answer"]:
            raise SystemExit(f"問{no}: 解説の正解 {y['answer']} が公式解答 {meta[no]['official_answer']} と不一致")
        items.append((meta[no], y))
    return items


def build(only=None, out_name="AP_R5_Spring_80Q_Enhanced.apkg"):
    model = genanki.Model(
        MODEL_ID,
        "AP R5春 IPA原文画像＋詳細解説",
        fields=[{"name": f} for f in FIELDS],
        templates=[{"name": "カード1", "qfmt": QFMT, "afmt": AFMT}],
        css=CSS,
        sort_field_index=0,
    )
    deck = genanki.Deck(DECK_ID, DECK_NAME,
                        description="IPA公式の問題画像（原文のまま）＋初心者向け詳細解説。"
                                    "分野別にタグで絞り込めます（例: tag:AP_R5H::分野::テクノロジ*）。")
    media_files = []
    for m, y in load_all(only):
        no = m["no"]
        img = MEDIA / m["image"]
        if not img.exists():
            raise SystemExit(f"画像がありません: {img}")
        media_files.append(str(img))
        result = m.get("previous_result", "")
        field = m["field"].replace("系", "")
        tags = ["R5春", "AP午前", f"問{no:02d}", f"AP_R5H::分野::{field}"]
        if y.get("category"):
            tags.append(f"AP_R5H::分野::{field}::{y['category']}")
        review = y.get("review") or []
        note = genanki.Note(
            model=model,
            fields=[
                f"{no:02d}",
                f'<img src="{html.escape(m["image"])}">',
                y["answer"],
                render(y.get("theme", "")),
                render(y.get("basics", "")),
                render(y.get("reasoning", "")),
                render_choices(y.get("choices", {}), y["answer"]),
                render(y.get("example", "")),
                "<ul>" + "".join(f"<li>{r}</li>" for r in review) + "</ul>" if review else "",
                result,
                f"{m['field']} ／ {y.get('category', '')}".rstrip(" ／"),
            ],
            tags=[t.replace(" ", "_") for t in tags],
            guid=genanki.guid_for("AP_R5H_AM", no),
            sort_field=f"{no:02d}",
            due=no,  # 新規カードを問題番号順に出題
        )
        deck.add_note(note)
    OUT.mkdir(exist_ok=True)
    pkg = genanki.Package(deck)
    pkg.media_files = media_files
    out = OUT / out_name
    pkg.write_to_file(str(out))
    print(f"wrote {out} ({len(deck.notes)} notes, {len(media_files)} images)")
    if not only:
        export_csv(OUT / "explanations_export.csv")
    return out


def result_of(m):
    return m.get("previous_result", "")


def export_csv(path):
    """解説データを一覧表（CSV, UTF-8 BOM付き＝Excelで文字化けしない）として書き出す。"""
    import csv
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["問", "正解", "前回結果", "分野", "テーマ", "基礎知識", "考え方", "ア", "イ", "ウ", "エ", "具体例", "復習ポイント"])
        for m, y in load_all():
            ch = y.get("choices", {})
            w.writerow([m["no"], y["answer"], result_of(m), y.get("category", ""), y.get("theme", "").strip(),
                        y.get("basics", "").strip(), y.get("reasoning", "").strip(), *[ch.get(c, "") for c in CHOICES],
                        y.get("example", "").strip(), "\n".join(y.get("review", []))])
    print(f"wrote {path}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", type=int, nargs="*", help="指定した問題番号だけで試作")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    only = set(a.only) if a.only else None
    name = a.out or ("AP_R5_Spring_80Q_Enhanced.apkg" if not only else "preview.apkg")
    build(only, name)
