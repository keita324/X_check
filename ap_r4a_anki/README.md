# 応用情報技術者試験 令和4年度秋期 午前80問 Ankiデッキ（詳細解説版）

## 成果物
| ファイル | 内容 |
|---|---|
| `output/AP_R4_Autumn_80Q_Enhanced.apkg` | AnkiMobile 等でインポートするデッキ本体（80問・画像80枚内蔵） |
| `output/quality_report.md` | 品質チェック結果（自動生成） |
| `output/explanations_export.csv` | 解説データの一覧（Excelで開ける UTF-8 BOM付き CSV） |
| `data/explanations/qNN.yaml` | **解説の原本**（1問1ファイル） |
| `data/questions_meta.json` | 公式正解・前回の学習結果・分野 |
| `data/image_crops.json` | 各問題画像がPDFの何ページ・どの位置から切り出されたか |
| `media/ipa_r04a_qNN.jpg` | IPA公式PDFから切り出した問題画像 |
| `source/` | IPA公式の問題PDF・解答PDF、旧デッキ |

## 誤りを見つけたときの直し方
1. `data/explanations/q15.yaml` のように該当問題のファイルだけを編集する。
2. `python3 build_deck.py` で .apkg を再生成する（`python3 build_deck.py --only 15` で1問だけの試作も可）。
3. `python3 check_quality.py --apkg output/AP_R4_Autumn_80Q_Enhanced.apkg` で検査する。
4. Ankiに再インポートすると、同じ問題のカードは（GUIDが固定なので）**学習履歴を保ったまま内容だけ更新**されます。

YAMLの書き方：空行で段落、`- ` で箇条書き、`1. ` で手順、`| ` で計算式ブロック。`<b>` `<sup>` などのHTMLタグも使えます。
文中の不等号は全角の「＜」「＞」か `&lt;` `&gt;` を使ってください（半角 `<` はHTMLタグと誤認されます）。

## 必要なもの
```
pip install genanki pyyaml pillow   # 生成
apt install poppler-utils            # crop_from_pdf.py（画像の再切り出し）を使う場合のみ
```

## Ankiでの使い方
- 前回不正解・未回答の問題だけ：ブラウザ／カスタム学習で `tag:要復習`（46問）
- 前回不正解だけ：`tag:前回不正解`（45問）
- 分野別：`tag:AP_R4A::分野::テクノロジ::*` など
- 問題画像をタップすると拡大（横スクロール）できます。
