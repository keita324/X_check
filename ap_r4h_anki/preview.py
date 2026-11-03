#!/usr/bin/env python3
"""カード裏面をHTMLとして書き出し、iPhoneサイズでスクリーンショットを撮る（レイアウト確認用）。

  python3 preview.py 1 2 3      # output/preview/q01.html ... と q01.png を作成
  python3 preview.py --html-all # 全80問のHTMLだけを作成（ブラウザで目視確認用）
"""
import re
import shutil
import sys
from pathlib import Path

import build_deck as B

OUTDIR = B.OUT / "preview"


def card_html(m, y):
    fields = {
        "問番号": f"{m['no']:02d}",
        "問題画像": f'<img src="../../media/{m["image"]}">',
        "正解": y["answer"],
        "テーマ": B.render(y.get("theme", "")),
        "基礎知識": B.render(y.get("basics", "")),
        "考え方": B.render(y.get("reasoning", "")),
        "選択肢解説": B.render_choices(y.get("choices", {}), y["answer"]),
        "具体例": B.render(y.get("example", "")),
        "復習ポイント": "<ul>" + "".join(f"<li>{r}</li>" for r in y.get("review", [])) + "</ul>",
        "前回結果": m.get("previous_result", ""),
        "分野": f"{m['field']} ／ {y.get('category', '')}",
    }

    def fill(t):
        t = re.sub(r"\{\{#(.+?)\}\}(.*?)\{\{/\1\}\}", lambda mm: mm.group(2) if fields.get(mm.group(1)) else "", t, flags=re.S)
        return re.sub(r"\{\{(.+?)\}\}", lambda mm: fields.get(mm.group(1), ""), t)

    body = fill(B.AFMT.replace("{{FrontSide}}", B.QFMT))
    return (f'<!doctype html><html lang="ja"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<style>body{{margin:0}}{B.CSS}</style></head><body><div class="card">{body}</div></body></html>')


def main(argv):
    OUTDIR.mkdir(parents=True, exist_ok=True)
    html_only = "--html-all" in argv
    nums = None if html_only else {int(a) for a in argv}
    items = B.load_all(nums)
    paths = []
    for m, y in items:
        p = OUTDIR / f"q{m['no']:02d}.html"
        p.write_text(card_html(m, y), "utf-8")
        paths.append(p)
    if html_only:
        print(f"{len(paths)} html files in {OUTDIR}")
        return
    import json, subprocess
    js = """
const {chromium}=require('playwright');
(async()=>{const b=await chromium.launch();const p=await b.newPage({viewport:{width:390,height:844},deviceScaleFactor:1});
for(const f of JSON.parse(process.argv[1])){await p.goto('file://'+f);await p.waitForTimeout(200);
const sw=await p.evaluate(()=>document.documentElement.scrollWidth);
await p.screenshot({path:f.replace(/\\.html$/,'.png'),fullPage:true});console.log(f.split('/').pop(),'scrollWidth',sw);}
await b.close();})();
"""
    subprocess.run(["node", "-e", js, json.dumps([str(p) for p in paths])], check=True)

if __name__ == "__main__":
    main(sys.argv[1:])
