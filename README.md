# Yoroshikuonegaishima-su

## スクリプト概要

### 学生用

| コマンド | スクリプト | 説明 |
|---------|-----------|------|
| `yoroshikuonegaishima-su` | `yoroshikuonegaishima-su.py` | 課題ディレクトリの `*.c` を提出先へコピーする提出スクリプト |
| `scouter` | `scouter.py` | 基本問題（`j2pro*`）の提出状況とバトルポイントを確認する |
| `scouterPro` | `scouterPro.py` | 応用問題（`chohatten_*`）の提出状況とバトルポイントを確認する |
| `scouterExam` | `scouterExam.py` | 試験（`j2exam*`）の提出状況を確認する |

### 教員用

| スクリプト | 説明 |
|-----------|------|
| `scouter_allstudents.py` | 全学生の基本問題提出状況を一覧表示する |
| `scouterPro_allstudents.py` | 全学生の応用問題提出状況を一覧表示する |
| `scouterExam_allstudents.py` | 全学生の試験提出状況を一覧表示する |

---

## セットアップ（管理者）

### 1. スクリプトのインストール

```bash
./install.sh
```

`install.sh` を実行すると以下が `/usr/local/bin/` にインストールされる。

| コピー元 | コピー先 |
|---------|---------|
| `yoroshikuonegaishima-su.py` | `/usr/local/bin/yoroshikuonegaishima-su` |
| `grader.py` | `/usr/local/bin/grader.py` |
| `scouter.py` | `/usr/local/bin/scouter` |
| `scouterPro.py` | `/usr/local/bin/scouterPro` |
| `scouterExam.py` | `/usr/local/bin/scouterExam` |

### 2. config.py の配置

`config.py.example` を参考に `config.py` を作成し、`CONFIG_PATH` に記載されたパスに配置する。

```python
QUESTION_ROOT = "/path/to/questions"   # 課題定義ファイルのあるディレクトリ
SUBMISSION_BASE = "/path/to/send"      # 提出先のベースディレクトリ
```

### 3. questions ディレクトリ構造

```
QUESTION_ROOT/
├── j2pro0410/
│   ├── j2pro0410.md          # 課題定義（ファイル名, バトルポイント）
│   ├── No0410_1/             # テストケース
│   │   ├── sample-1.txt
│   │   └── sample-1-out.txt
│   └── No0410_2/
├── chohatten_zenki1/
│   ├── chohatten_zenki1.md
│   ├── sample-1.txt          # テストケース（1ファイルの場合は直下に置く）
│   └── sample-1-out.txt
├── chohatten_kouki1/
│   └── chohatten_kouki1.md
└── j2exam0601/
    └── j2exam0601.md
```

課題定義ファイルの書式（`j2pro0410.md` の例）:
```
No0410_1.c, 123
No0410_2.c, 1251
```

### 4. 提出先ディレクトリの作成

`SUBMISSION_BASE/<ユーザー名>/<課題ディレクトリ名>` を事前に作成しておく。
`setup_j2pro.py` を使用すると全学生分を一括作成できる。

---

## yoroshikuonegaishima-su — 提出スクリプト

### 使い方

```bash
yoroshikuonegaishima-su j2pro0410
yoroshikuonegaishima-su chohatten_zenki1
```

### 動作ルール
- 課題定義ファイルに記載されたファイル名だけを受理する。
- 提出先をソースディレクトリと同期する（ソースに存在しないファイルは提出先から削除）。
- 提出後に採点を実行し、結果を表示する。
- `*.c` 以外のファイルは無視する。

### 表示メッセージ
- 新規提出: `<ファイル名>: 新規に提出しました。`
- 上書き提出: `<ファイル名>: 上書きしました。`
- 削除: `<ファイル名>: 削除しました。`
- 不一致: `<ファイル名>: 受理しません。設定ファイルに存在しないファイル名です。`

---

## scouter — 基本問題提出状況確認

### 使い方

```bash
scouter
```

- 現在の月から前期（4〜8月）・後期（10〜2月）を自動判定し、対応する `j2pro*` のみ表示する。

### 出力例

```
j25401
O.K. : No0410_1.c (2026-04-10 14:12:51)
     : No0410_2.c
2/2
Battle Point=136
```

---

## scouterPro — 応用問題提出状況確認

### 使い方

```bash
scouterPro
```

- 現在の月から前期（`chohatten_zenki*`）・後期（`chohatten_kouki*`）を自動判定して表示する。

---

## scouterExam — 試験提出状況確認

### 使い方

```bash
scouterExam
```

- バトルポイントなし。提出有無のみ表示。
- 対象試験は `scouterExam.py` 内の `EXAM_DATE` を手動編集して指定する。

```python
EXAM_DATE = "0601"   # → j2exam0601 が対象
```

---

## 教員用スクリプト

```bash
python scouter_allstudents.py
python scouterPro_allstudents.py
python scouterExam_allstudents.py
```

- `j25.csv`（学生名簿）を読み込み、学生ごとに `学籍番号,氏名` の後に各 scouter の出力を表示する。
- `j25.csv` は `/home/jstaff/oeda/tools/config/j25.csv` を参照する（個人情報のため git 管理外）。
