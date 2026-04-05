# Yoroshikuonegaishima-su

## スクリプト概要

| スクリプト | 説明 |
|-----------|------|
| `yorosikuonegaishima-su` | 課題ディレクトリの `*.c` を提出先へコピーする提出スクリプト |
| `scouter` | 自分の課題提出状況とバトルポイントを確認するスクリプト |

---

## セットアップ（管理者）

1. スクリプトを `/usr/local/bin/` にコピーして実行権限を付与する。
   ```bash
   cp yorosikuonegaishima-su.py /usr/local/bin/yorosikuonegaishima-su
   cp scouter.py /usr/local/bin/scouter
   chmod 755 /usr/local/bin/yorosikuonegaishima-su
   chmod 755 /usr/local/bin/scouter
   ```

2. `config.py.example` を参考に `config.py` を作成し、本番パスに配置する。
   - 配置先: スクリプト内の `CONFIG_PATH` に記載されたパス
   - 内容:
     ```python
     QUESTION_ROOT = "/path/to/questions"   # 課題定義ファイル（*.md）のあるディレクトリ
     SUBMISSION_BASE = "/path/to/send"      # 提出先のベースディレクトリ
     ```

3. 課題定義ファイルを `QUESTION_ROOT/<課題ディレクトリ名>.md` として作成する。
   - 書式: `<ファイル名>, <バトルポイント>`
   - 例 (`j2pro0408.md`):
     ```
     No0408_1.c, 123
     No0408_2.c, 1251
     ```

4. 提出先ディレクトリ（`SUBMISSION_BASE/<ユーザー名>/<課題ディレクトリ名>`）を事前に作成しておく。

---

## yorosikuonegaishima-su — 提出スクリプト

### 使い方

```bash
yorosikuonegaishima-su j2pro0408
```

- 課題ディレクトリ名を 1 つ指定する。
- 指定ディレクトリ直下の `*.c` だけが対象。サブディレクトリは探索しない。

### 動作ルール
- 課題定義ファイルに記載されたファイル名だけを受理する。
- 一致しない `*.c` は受理しない。
- 不一致ファイルがあっても、一致するファイルは提出される。
- `*.c` 以外のファイルは無視する。
- 提出先は `SUBMISSION_BASE/<ユーザー名>/<課題ディレクトリ名>`。
- 同名ファイルがない場合は新規提出、ある場合は上書き。

### 表示メッセージ
- 新規提出: `<ファイル名>: 新規に提出しました。`
- 上書き提出: `<ファイル名>: 上書きしました。`
- 不一致: `<ファイル名>: 受理しません。設定ファイルに存在しないファイル名です。`
- 課題ディレクトリ未存在: `<課題ディレクトリ>: 課題ディレクトリが存在しません。`
- 設定ファイル未存在: `<設定ファイル名>: 設定ファイルが存在しません。`
- 提出先ディレクトリ未存在: `<提出先ディレクトリ>: 提出先ディレクトリが存在しません。`
- `.c` ファイルなし: `<課題ディレクトリ>: 送信対象の .c ファイルがありません。`
- 受理ファイルなし: `受理されたファイルはありませんでした。`
- 使い方エラー: `使い方: yorosikuonegaishima-su <課題ディレクトリ>`

---

## scouter — 提出状況確認スクリプト

### 使い方

```bash
scouter
```

- 引数不要。実行ユーザーの提出状況を自動で表示する。

### 出力例

```
j24001
O.K. : No0408_1.c
     : No0408_2.c
1/2
Battle Point=123
```

### 動作ルール
- `QUESTION_ROOT/*.md` をファイル名順に処理する。
- 各課題について `SUBMISSION_BASE/<ユーザー名>/<課題ディレクトリ名>/<ファイル名>` の存在を確認する。
- 提出済み課題のバトルポイントを合算して表示する。

---

## 関連文書
- 提出スクリプト仕様: `docs/specs/submission-script.md`
- 提出スクリプト実装計画: `docs/plans/submission-script.md`
- 提出状況確認スクリプト仕様: `docs/specs/check-assignment.md`
- 提出状況確認スクリプト実装計画: `docs/plans/check-assignment.md`
