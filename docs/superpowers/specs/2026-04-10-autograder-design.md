# 自動採点モジュール設計仕様

## 概要

学生が `yorosikuonegaishima-su` コマンドで .c ファイルを提出すると、自動的に採点を行い結果を表示する。採点は独立した `grader.py` モジュールに実装し、提出スクリプトからインポートして呼び出す。

## 目的

- 提出と同時にコンパイルの可否・テストケースの通過状況を学生へフィードバックする。
- 将来的なLLMによる部分点採点を受け入れられる拡張可能な構造にする。

## アーキテクチャ

### 新規ファイル

- `grader.py` — 採点モジュール（コンパイル・テストケース・LLMスタブ）
- `tests/test_grader.py` — grader.py の単体テスト

### 変更ファイル

- `yorosikuonegaishima-su.py` — ファイルコピー後に `grader.grade_file()` を呼び出す処理を追加

### 処理フロー（提出時）

```
yorosikuonegaishima-su.py
  └── process_submission()
        ├── .c ファイルを SUBMISSION_BASE にコピー（既存処理）
        └── grade_file() を呼び出す  ← 追加
              ├── [1] コンパイルチェック（gcc）
              │     └── 失敗 → 結果表示 + grade_result.json 保存 → 終了
              ├── [2] テストケース採点（sample-*.txt / sample-*-out.txt）
              │     └── 各テストケース: 実行して stdout を期待出力と比較
              └── [3] LLM部分点採点（将来実装、現在はスタブ）
                    └── rubric.md が存在する場合のみ（現在はスキップ）
```

## テストケースディレクトリ構造

```
QUESTION_ROOT/
  j2pro0108/
    No0108_1/
      sample-1.txt        — 標準入力
      sample-1-out.txt    — 期待出力
      sample-2.txt
      sample-2-out.txt
      rubric.md           — 部分点基準（将来用、現在は無視）
```

テストケースディレクトリ名はファイル名の拡張子を除いたもの（例: `No0108_1.c` → `No0108_1/`）。

## `grader.py` インターフェース

### `GradeResult` データクラス

```python
@dataclass
class GradeResult:
    filename: str
    compile: Literal["ok", "error"]
    compile_error: str          # コンパイルエラー時のコンパイラ出力（正常時は空文字）
    tests_passed: int
    tests_total: int
    partial_score: int | None   # LLM採点結果（現在は常に None）
    score: int                  # 獲得点数
```

### 主要関数

```python
def grade_file(
    source_path: Path,       # コピー済みの .c ファイルパス
    question_root: Path,     # QUESTION_ROOT
    assignment_name: str,    # 課題ディレクトリ名（例: j2pro0108）
) -> GradeResult
```

```python
def print_result(result: GradeResult) -> None
```

```python
def save_result(result: GradeResult, dest_dir: Path) -> None
# 保存ファイル名: <stem>_grade.json（例: No0108_1_grade.json）
```

## 採点ロジック詳細

### [1] コンパイルチェック

- `gcc <source.c> -o <tmpdir>/a.out` を実行（タイムアウト: 30秒）
- 成功 → `compile="ok"`、次フェーズへ
- 失敗 → `compile="error"`、`compile_error` にコンパイラ出力を格納、以降スキップ、score=0

### [2] テストケース採点

- テストケースディレクトリ: `QUESTION_ROOT/<assignment_name>/<stem>/`
- `sample-N.txt` / `sample-N-out.txt` のペアを自動検出（N は 1 から連番）
- テストケースが0件の場合: `tests_passed=0`、`tests_total=0`、`score=0`（除算エラーを防ぐ）
- 各テストケース: stdin に `sample-N.txt` を渡して実行、stdout を `sample-N-out.txt` と比較（末尾空白は strip）
- 実行タイムアウト: 10秒（ハング防止のみ、TLEは考慮しない）
- スコア: `tests_passed / tests_total * 100`（整数切り捨て）

### [3] LLM部分点採点（スタブ）

- `rubric.md` の存在確認のみ行い、内容は処理しない
- `partial_score=None` を返す
- 将来: rubric.md を読み込み、LLM API に採点を依頼する

## 採点結果の表示

```
--- 採点結果: No0108_1.c ---
コンパイル: OK
テスト: 2/3 通過
スコア: 66点
```

コンパイルエラー時:

```
--- 採点結果: No0108_1.c ---
コンパイル: エラー
No0108_1.c:3:1: error: ...
スコア: 0点
```

## 採点結果ファイル

保存先: `SUBMISSION_BASE/<ユーザー名>/<課題dir>/<stem>_grade.json`（例: `No0108_1_grade.json`）

複数ファイルを提出した場合でも上書きされないよう、ファイル名の stem に基づいて個別保存する。

```json
{
  "filename": "No0108_1.c",
  "compile": "ok",
  "tests_passed": 2,
  "tests_total": 3,
  "partial_score": null,
  "score": 66
}
```

## テスト方針（`tests/test_grader.py`）

既存の `test_submission_script.py` と同じスタイル（`unittest`、`tempfile`、`redirect_stdout`）で記述する。

| テストケース | 内容 |
|---|---|
| `test_compile_error` | コンパイルエラーになる .c → compile="error"、score=0 |
| `test_compile_ok_no_testcases` | テストケースなし → compile="ok"、tests=0/0 |
| `test_all_tests_pass` | 全テスト通過 → score=100 |
| `test_partial_tests_pass` | 一部通過 → スコアが割合に応じた値 |
| `test_save_result` | grade_result.json が正しく保存される |
| `test_print_result` | 表示出力が期待通り |

## 制約・前提

- `gcc` が実行環境に存在すること（標準的な Linux 環境を前提）
- 標準ライブラリのみ使用（`subprocess`、`tempfile`、`json`、`dataclasses`）
- LLM採点は今回スコープ外（インターフェースのみ定義）
- 対象は初学者の C プログラム（TLE は考慮しない）

## 非対象

- LLM採点の実装
- 複数ファイルを結合するコンパイル
- ネットワーク通信
- GUI
