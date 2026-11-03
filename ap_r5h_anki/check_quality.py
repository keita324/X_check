#!/usr/bin/env python3
"""解説データとデッキの品質チェック。結果を output/quality_report.md に書き出す。

  python3 check_quality.py            # 解説データの検査
  python3 check_quality.py --apkg output/AP_R4_Autumn_80Q_Enhanced.apkg   # 生成済みデッキの構造検査も行う
"""
import argparse
import difflib
import html
import json
import re
import sqlite3
import tempfile
import zipfile
from collections import defaultdict
from html.parser import HTMLParser
from pathlib import Path

from PIL import Image

import build_deck as B

CHOICES = B.CHOICES
GENERIC_PHRASES = [  # 旧デッキで全問に使い回されていた汎用文や、それに類する表現
    "問題文の「何を問うているか」を先に確認",
    "正解の理由と他の選択肢が違う理由",
    "重要語句を覚える",
    "他の選択肢も確認する",
]
VOID = {"br", "img", "hr"}


class TagChecker(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack, self.errors = [], []

    def handle_starttag(self, tag, attrs):
        if tag not in VOID:
            self.stack.append(tag)

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        if not self.stack or self.stack[-1] != tag:
            self.errors.append(f"閉じタグ不整合 </{tag}> (stack={self.stack[-3:]})")
        else:
            self.stack.pop()


def plain(s: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "", s or ""))


def check_html(s: str):
    errs = []
    # タグとして解釈されない裸の「<」（例: a<b）を検出
    for m in re.finditer(r"<", s):
        if not re.match(r"</?[a-zA-Z]", s[m.start():m.start() + 3]):
            errs.append(f"裸の'<'あり: …{s[max(0, m.start() - 10):m.start() + 10]}…")
    t = TagChecker()
    t.feed(s)
    t.close()
    errs += t.errors
    if t.stack:
        errs.append(f"閉じていないタグ: {t.stack}")
    return errs


def sentences(text: str):
    return [x.strip() for x in re.split(r"[。\n]", plain(text)) if len(x.strip()) >= 15]


def main(apkg=None):
    items = B.load_all()
    meta = {m["no"]: m for m, _ in items}
    problems = defaultdict(list)
    rows = []
    review_all = []
    sent_owner = defaultdict(set)

    for m, y in items:
        no = m["no"]
        for key in ("theme", "basics", "reasoning", "choices", "review"):
            if not y.get(key):
                problems[no].append(f"必須項目 {key} が空")
        ch = y.get("choices") or {}
        missing = [c for c in CHOICES if c not in ch]
        if missing:
            problems[no].append(f"選択肢解説が不足: {missing}")
        for c in CHOICES:
            t = str(ch.get(c, ""))
            has_mark = "<b>正解</b>" in t
            if c == y["answer"] and not has_mark:
                problems[no].append(f"正解の選択肢{c}に<b>正解</b>表記がない")
            if c != y["answer"] and has_mark:
                problems[no].append(f"不正解の選択肢{c}に<b>正解</b>表記がある")
        if not re.search(rf"<b>{y['answer']}</b>|正解は<b>{y['answer']}</b>", y.get("reasoning", "")):
            problems[no].append("考え方の中で正解記号が明示されていない")
        rv = y.get("review") or []
        if not 1 <= len(rv) <= 3:
            problems[no].append(f"復習ポイントが{len(rv)}項目（1〜3項目であること）")
        review_all += [(no, r) for r in rv]
        full = "\n".join([y.get("theme", ""), y.get("basics", ""), y.get("reasoning", ""),
                          "\n".join(str(v) for v in ch.values()), y.get("example", ""), "\n".join(rv)])
        for p in GENERIC_PHRASES:
            if p in plain(full):
                problems[no].append(f"汎用文の使い回し: {p}")
        for part_name, part in [("theme", y.get("theme")), ("basics", y.get("basics")), ("reasoning", y.get("reasoning")),
                                ("example", y.get("example")), ("review", "".join(f"<li>{r}</li>" for r in rv))] + \
                               [(f"choice{c}", str(v)) for c, v in ch.items()]:
            for e in check_html(part or ""):
                problems[no].append(f"[{part_name}] {e}")
        for s in sentences(full):
            sent_owner[s].add(no)
        n_chars = len(re.sub(r"\s", "", plain(full)))
        img = B.MEDIA / m["image"]
        size = Image.open(img).size if img.exists() else None
        if not size:
            problems[no].append("画像なし")
        rows.append(dict(no=no, answer=y["answer"], official=m["official_answer"], prev=m.get("previous_result", "-"),
                         chars=n_chars, review=len(rv), img=size))

    # 復習ポイントの重複（完全一致・高類似）
    dup_reviews = []
    for i in range(len(review_all)):
        for j in range(i + 1, len(review_all)):
            a, b = review_all[i], review_all[j]
            if a[0] == b[0]:
                continue
            r = difflib.SequenceMatcher(None, plain(a[1]), plain(b[1])).ratio()
            if r >= 0.6:
                dup_reviews.append((a[0], b[0], round(r, 2), plain(a[1])[:40], plain(b[1])[:40]))
    # 3問以上に出現する同一文（汎用的な説明の使い回し検出）
    shared = [(s, sorted(v)) for s, v in sent_owner.items() if len(v) >= 3]

    chars = [r["chars"] for r in rows]
    short = [r for r in rows if r["chars"] < 400]
    cnt = defaultdict(int)
    for r in rows:
        cnt[r["prev"]] += 1

    out = ["# 品質チェック結果", ""]
    out += ["## 1. 解説データ", "",
            f"- 収録問題数: {len(rows)} / 80",
            f"- 正解とIPA公式解答の一致: {sum(r['answer'] == r['official'] for r in rows)} / {len(rows)}",
            f"- 前回の学習結果: 正解 {cnt['正解']} / 不正解 {cnt['不正解']} / 未回答 {cnt['未回答']}",
            f"- 解説の文字数（空白除く・HTML除去後）: 最小 {min(chars)} / 中央値 {sorted(chars)[len(chars) // 2]} / 最大 {max(chars)}",
            f"- 400文字未満の問題: {[r['no'] for r in short] or 'なし'}",
            f"- 4択すべての選択肢解説あり: {sum(1 for _, y in items if all(c in (y.get('choices') or {}) for c in CHOICES))} / {len(rows)}",
            f"- 復習ポイント総数: {len(review_all)}（重複・高類似[類似度0.6以上]の組: {len(dup_reviews)}）",
            f"- 3問以上で同一の文（汎用文の使い回し候補）: {len(shared)}",
            f"- 旧デッキの汎用文（{len(GENERIC_PHRASES)}種）の残存: {sum(1 for v in problems.values() for p in v if '汎用文' in p)}",
            f"- 問題ごとの指摘事項: {sum(len(v) for v in problems.values())} 件", ""]
    if dup_reviews:
        out += ["### 類似した復習ポイント", ""] + [f"- 問{a} と 問{b}（{r}）: {x} ／ {y}" for a, b, r, x, y in dup_reviews] + [""]
    if shared:
        out += ["### 3問以上で共通する文", ""] + [f"- {s[:50]}… → 問{v}" for s, v in shared] + [""]
    if problems:
        out += ["### 指摘事項", ""] + [f"- 問{no}: {p}" for no in sorted(problems) for p in problems[no]] + [""]
    out += ["### 問題別一覧", "", "| 問 | 正解 | 公式 | 前回 | 解説文字数 | 復習P | 画像サイズ |", "|---|---|---|---|---|---|---|"]
    out += [f"| {r['no']} | {r['answer']} | {r['official']} | {r['prev']} | {r['chars']} | {r['review']} | {r['img'][0]}×{r['img'][1]} |" for r in rows]
    out.append("")

    if apkg:
        out += ["## 2. 生成デッキ（.apkg）の構造検査", ""] + check_apkg(apkg, meta)

    report = B.OUT / "quality_report.md"
    B.OUT.mkdir(exist_ok=True)
    report.write_text("\n".join(out), "utf-8")
    print("\n".join(out[:16]))
    print(f"... -> {report}")
    return 0 if not problems else 1


def check_apkg(path, meta):
    res = []
    z = zipfile.ZipFile(path)
    names = z.namelist()
    media = json.loads(z.read("media"))
    res.append(f"- zip内ファイル: collection.anki2 {'あり' if 'collection.anki2' in names else 'なし'}, media {len(media)}件")
    with tempfile.TemporaryDirectory() as td:
        z.extract("collection.anki2", td)
        c = sqlite3.connect(f"{td}/collection.anki2")
        res.append(f"- SQLite integrity_check: {c.execute('pragma integrity_check').fetchone()[0]}")
        col = c.execute("select ver, models, decks, dconf, conf from col").fetchone()
        ok = []
        for nm, v in zip(["models", "decks", "dconf", "conf"], col[1:]):
            try:
                json.loads(v)
                ok.append(f"{nm}=OK")
            except Exception as e:  # noqa: BLE001
                ok.append(f"{nm}=NG({e})")
        res.append(f"- col.ver={col[0]}、JSONデコード: {', '.join(ok)}")
        cols = [r[1] for r in c.execute("pragma table_info(cards)")]
        res.append(f"- cardsテーブルの列: {len(cols)}列（lapses列 {'あり' if 'lapses' in cols else 'なし'}）")
        nn = c.execute("select count(*) from notes").fetchone()[0]
        nc = c.execute("select count(*) from cards").fetchone()[0]
        orphan = c.execute("select count(*) from cards where nid not in (select id from notes)").fetchone()[0]
        decks = json.loads(col[2])
        bad_did = c.execute(f"select count(*) from cards where did not in ({','.join(decks.keys())})").fetchone()[0]
        res.append(f"- ノート {nn} 件 / カード {nc} 件 / 孤立カード {orphan} 件 / 存在しないデッキを参照するカード {bad_did} 件")
        flds = [r[0] for r in c.execute("select flds from notes")]
        refs = set()
        for f in flds:
            refs |= set(re.findall(r'src="([^"]+)"', f))
        missing = refs - set(media.values())
        res.append(f"- ノートが参照する画像 {len(refs)} 件、apkg内に存在しない画像 {len(missing)} 件")
        tags = [r[0] for r in c.execute("select tags from notes")]
        res.append(f"- タグ「前回不正解」 {sum('前回不正解' in t for t in tags)} 件、「前回正解」 {sum('前回正解' in t for t in tags)} 件、"
                   f"「前回未回答」 {sum('前回未回答' in t for t in tags)} 件、「要復習」 {sum('要復習' in t for t in tags)} 件")
        try:
            all_text = "".join(flds)
            all_text.encode("utf-8")
            res.append("- フィールドの文字コード: UTF-8で正常にエンコード可能（文字化けなし）")
        except UnicodeError as e:
            res.append(f"- 文字コードエラー: {e}")
    return res


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--apkg")
    a = ap.parse_args()
    raise SystemExit(main(a.apkg))
