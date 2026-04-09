# Autograder Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `yorosikuonegaishima-su` で .c ファイルを提出すると自動採点が走り、コンパイル結果・テスト通過状況・スコアを表示して `<stem>_grade.json` に保存する。

**Architecture:** 採点ロジックを `grader.py` モジュールに独立させ、`yorosikuonegaishima-su.py` がファイルコピー後に `grader.grade_file()` を呼び出す。TDD で `tests/test_grader.py` を先に書き、実装はすべてテストが通ってからコミットする。

**Tech Stack:** Python 3 標準ライブラリのみ（`subprocess`, `tempfile`, `json`, `dataclasses`）、gcc

---

## File Map

| ファイル | 役割 |
|---|---|
| `grader.py` (新規) | `GradeResult` dataclass + `grade_file()` / `print_result()` / `save_result()` / `_run_tests()` |
| `tests/test_grader.py` (新規) | grader.py の単体テスト（6ケース） |
| `yorosikuonegaishima-su.py` (変更) | ファイルコピー後に grader を呼び出す2行追加 |
| `tests/test_submission_script.py` (変更) | 採点結果が出力に含まれることを確認するテストを追加 |

---

## Task 1: GradeResult dataclass と test_grader.py の骨格を作る

**Files:**
- Create: `grader.py`
- Create: `tests/test_grader.py`

- [ ] **Step 1: tests/test_grader.py を作成する（失敗するテストを書く）**

```python
# tests/test_grader.py
from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

GRADER_PATH = Path(__file__).resolve().parent.parent / "grader.py"
SPEC = importlib.util.spec_from_file_location("grader", GRADER_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules["grader"] = MODULE  # Python 3.13+ で dataclass が sys.modules を参照するため必要
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class GraderTest(unittest.TestCase):
    def make_workspace(self) -> tuple[Path, Path, Path]:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        root = Path(temp_dir.name)
        question_root = root / "questions"
        submission_dir = root / "submissions" / "j2pro0108"
        question_root.mkdir(parents=True)
        submission_dir.mkdir(parents=True)
        return root, question_root, submission_dir

    def write_c_file(self, dest_dir: Path, name: str, content: str) -> Path:
        path = dest_dir / name
        path.write_text(content, encoding="utf-8")
        return path

    def test_grade_result_has_expected_fields(self) -> None:
        result = MODULE.GradeResult(
            filename="No0108_1.c",
            compile="ok",
            compile_error="",
            tests_passed=0,
            tests_total=0,
            partial_score=None,
            score=0,
        )
        self.assertEqual(result.filename, "No0108_1.c")
        self.assertEqual(result.compile, "ok")
        self.assertEqual(result.compile_error, "")
        self.assertEqual(result.tests_passed, 0)
        self.assertEqual(result.tests_total, 0)
        self.assertIsNone(result.partial_score)
        self.assertEqual(result.score, 0)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: テストが失敗することを確認する**

```bash
python -m pytest tests/test_grader.py::GraderTest::test_grade_result_has_expected_fields -v
```

Expected: `ERROR` または `ModuleNotFoundError`（grader.py が存在しないため）

- [ ] **Step 3: grader.py を作成して GradeResult dataclass を実装する**

```python
# grader.py
from __future__ import annotations

import json
import subprocess
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal


@dataclass
class GradeResult:
    filename: str
    compile: Literal["ok", "error"]
    compile_error: str
    tests_passed: int
    tests_total: int
    partial_score: int | None
    score: int
```

- [ ] **Step 4: テストが通ることを確認する**

```bash
python -m pytest tests/test_grader.py::GraderTest::test_grade_result_has_expected_fields -v
```

Expected: `PASSED`

- [ ] **Step 5: コミットする**

```bash
git checkout -b feature/autograder
git add grader.py tests/test_grader.py
git commit -m "Add GradeResult dataclass and test skeleton"
```

---

## Task 2: コンパイルチェックを実装する

**Files:**
- Modify: `grader.py`
- Modify: `tests/test_grader.py`

- [ ] **Step 1: コンパイルチェックのテストを tests/test_grader.py に追加する**

`GraderTest` クラスに以下のメソッドを追加する:

```python
def test_compile_error_returns_error_result(self) -> None:
    _, question_root, submission_dir = self.make_workspace()
    c_file = self.write_c_file(
        submission_dir, "No0108_1.c", "not valid c code {\n"
    )
    result = MODULE.grade_file(c_file, question_root, "j2pro0108")
    self.assertEqual(result.compile, "error")
    self.assertEqual(result.score, 0)
    self.assertNotEqual(result.compile_error, "")
    self.assertEqual(result.tests_passed, 0)
    self.assertEqual(result.tests_total, 0)

def test_compile_ok_returns_ok_result(self) -> None:
    _, question_root, submission_dir = self.make_workspace()
    c_file = self.write_c_file(
        submission_dir,
        "No0108_1.c",
        "#include <stdio.h>\nint main(void){return 0;}\n",
    )
    result = MODULE.grade_file(c_file, question_root, "j2pro0108")
    self.assertEqual(result.compile, "ok")
    self.assertEqual(result.compile_error, "")
```

- [ ] **Step 2: テストが失敗することを確認する**

```bash
python -m pytest tests/test_grader.py::GraderTest::test_compile_error_returns_error_result tests/test_grader.py::GraderTest::test_compile_ok_returns_ok_result -v
```

Expected: `FAILED` (`AttributeError: module 'grader' has no attribute 'grade_file'`)

- [ ] **Step 3: grade_file() と _run_tests() のスタブを grader.py に追加する**

`GradeResult` dataclass の定義の後に追記する:

```python
def _run_tests(exe_path: Path, testcase_dir: Path) -> tuple[int, int]:
    """テストケースを実行して (passed, total) を返す。スタブ: 常に (0, 0)。"""
    return 0, 0


def grade_file(
    source_path: Path,
    question_root: Path,
    assignment_name: str,
) -> GradeResult:
    filename = source_path.name
    stem = source_path.stem

    with tempfile.TemporaryDirectory() as tmpdir:
        exe_path = Path(tmpdir) / "a.out"
        proc = subprocess.run(
            ["gcc", str(source_path), "-o", str(exe_path)],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if proc.returncode != 0:
            return GradeResult(
                filename=filename,
                compile="error",
                compile_error=proc.stderr,
                tests_passed=0,
                tests_total=0,
                partial_score=None,
                score=0,
            )

        testcase_dir = question_root / assignment_name / stem
        tests_passed, tests_total = _run_tests(exe_path, testcase_dir)

    score = (tests_passed * 100 // tests_total) if tests_total > 0 else 0
    return GradeResult(
        filename=filename,
        compile="ok",
        compile_error="",
        tests_passed=tests_passed,
        tests_total=tests_total,
        partial_score=None,
        score=score,
    )
```

- [ ] **Step 4: テストが通ることを確認する**

```bash
python -m pytest tests/test_grader.py::GraderTest::test_compile_error_returns_error_result tests/test_grader.py::GraderTest::test_compile_ok_returns_ok_result -v
```

Expected: 2 tests `PASSED`

- [ ] **Step 5: コミットする**

```bash
git add grader.py tests/test_grader.py
git commit -m "Implement compile check in grade_file"
```

---

## Task 3: テストケース採点を実装する

**Files:**
- Modify: `grader.py`
- Modify: `tests/test_grader.py`

- [ ] **Step 1: テストケース採点のテストを tests/test_grader.py に追加する**

`GraderTest` クラスに以下のメソッドを追加する:

```python
def make_testcase_dir(
    self,
    question_root: Path,
    assignment_name: str,
    stem: str,
) -> Path:
    """テストケースディレクトリを作成して返す。"""
    d = question_root / assignment_name / stem
    d.mkdir(parents=True)
    return d

def test_compile_ok_no_testcases(self) -> None:
    _, question_root, submission_dir = self.make_workspace()
    c_file = self.write_c_file(
        submission_dir,
        "No0108_1.c",
        "#include <stdio.h>\nint main(void){return 0;}\n",
    )
    # テストケースディレクトリを作らない
    result = MODULE.grade_file(c_file, question_root, "j2pro0108")
    self.assertEqual(result.compile, "ok")
    self.assertEqual(result.tests_passed, 0)
    self.assertEqual(result.tests_total, 0)
    self.assertEqual(result.score, 0)

def test_all_tests_pass(self) -> None:
    _, question_root, submission_dir = self.make_workspace()
    # stdin の数値を2倍して出力する C プログラム
    c_file = self.write_c_file(
        submission_dir,
        "No0108_1.c",
        "#include <stdio.h>\nint main(void){int a;scanf(\"%d\",&a);printf(\"%d\\n\",a*2);return 0;}\n",
    )
    tc_dir = self.make_testcase_dir(question_root, "j2pro0108", "No0108_1")
    (tc_dir / "sample-1.txt").write_text("5\n", encoding="utf-8")
    (tc_dir / "sample-1-out.txt").write_text("10\n", encoding="utf-8")

    result = MODULE.grade_file(c_file, question_root, "j2pro0108")
    self.assertEqual(result.compile, "ok")
    self.assertEqual(result.tests_passed, 1)
    self.assertEqual(result.tests_total, 1)
    self.assertEqual(result.score, 100)

def test_partial_tests_pass(self) -> None:
    _, question_root, submission_dir = self.make_workspace()
    # 入力を2倍するプログラム: sample-1(5→10)は通過、sample-2(3→99 expected)は失敗
    c_file = self.write_c_file(
        submission_dir,
        "No0108_1.c",
        "#include <stdio.h>\nint main(void){int a;scanf(\"%d\",&a);printf(\"%d\\n\",a*2);return 0;}\n",
    )
    tc_dir = self.make_testcase_dir(question_root, "j2pro0108", "No0108_1")
    (tc_dir / "sample-1.txt").write_text("5\n", encoding="utf-8")
    (tc_dir / "sample-1-out.txt").write_text("10\n", encoding="utf-8")
    (tc_dir / "sample-2.txt").write_text("3\n", encoding="utf-8")
    (tc_dir / "sample-2-out.txt").write_text("99\n", encoding="utf-8")  # 正解は6だが99を期待

    result = MODULE.grade_file(c_file, question_root, "j2pro0108")
    self.assertEqual(result.tests_passed, 1)
    self.assertEqual(result.tests_total, 2)
    self.assertEqual(result.score, 50)
```

- [ ] **Step 2: テストが失敗することを確認する**

```bash
python -m pytest tests/test_grader.py::GraderTest::test_compile_ok_no_testcases tests/test_grader.py::GraderTest::test_all_tests_pass tests/test_grader.py::GraderTest::test_partial_tests_pass -v
```

Expected: `test_compile_ok_no_testcases` は PASSED、`test_all_tests_pass` と `test_partial_tests_pass` は FAILED（`_run_tests` がスタブのため）

- [ ] **Step 3: _run_tests() を実装する（grader.py の既存スタブを置き換える）**

`grader.py` 内の `_run_tests` スタブを以下に置き換える:

```python
def _run_tests(exe_path: Path, testcase_dir: Path) -> tuple[int, int]:
    if not testcase_dir.is_dir():
        return 0, 0

    passed = 0
    total = 0
    n = 1
    while True:
        in_file = testcase_dir / f"sample-{n}.txt"
        out_file = testcase_dir / f"sample-{n}-out.txt"
        if not in_file.exists() or not out_file.exists():
            break
        total += 1
        try:
            proc = subprocess.run(
                [str(exe_path)],
                input=in_file.read_text(encoding="utf-8"),
                capture_output=True,
                text=True,
                timeout=10,
            )
            expected = out_file.read_text(encoding="utf-8").strip()
            if proc.stdout.strip() == expected:
                passed += 1
        except subprocess.TimeoutExpired:
            pass
        n += 1

    return passed, total
```

- [ ] **Step 4: テストが通ることを確認する**

```bash
python -m pytest tests/test_grader.py -v
```

Expected: 5 tests `PASSED`（Task 1, 2 のテストも含む）

- [ ] **Step 5: コミットする**

```bash
git add grader.py tests/test_grader.py
git commit -m "Implement test case grading in _run_tests"
```

---

## Task 4: print_result と save_result を実装する

**Files:**
- Modify: `grader.py`
- Modify: `tests/test_grader.py`

- [ ] **Step 1: print_result と save_result のテストを tests/test_grader.py に追加する**

`GraderTest` クラスに以下のメソッドを追加する:

```python
def test_print_result_compile_ok(self) -> None:
    result = MODULE.GradeResult(
        filename="No0108_1.c",
        compile="ok",
        compile_error="",
        tests_passed=2,
        tests_total=3,
        partial_score=None,
        score=66,
    )
    output = StringIO()
    with redirect_stdout(output):
        MODULE.print_result(result)
    text = output.getvalue()
    self.assertIn("--- 採点結果: No0108_1.c ---", text)
    self.assertIn("コンパイル: OK", text)
    self.assertIn("テスト: 2/3 通過", text)
    self.assertIn("スコア: 66点", text)

def test_print_result_compile_error(self) -> None:
    result = MODULE.GradeResult(
        filename="No0108_1.c",
        compile="error",
        compile_error="No0108_1.c:1:1: error: expected declaration\n",
        tests_passed=0,
        tests_total=0,
        partial_score=None,
        score=0,
    )
    output = StringIO()
    with redirect_stdout(output):
        MODULE.print_result(result)
    text = output.getvalue()
    self.assertIn("--- 採点結果: No0108_1.c ---", text)
    self.assertIn("コンパイル: エラー", text)
    self.assertIn("No0108_1.c:1:1: error:", text)
    self.assertIn("スコア: 0点", text)

def test_save_result_creates_json(self) -> None:
    _, _, submission_dir = self.make_workspace()
    result = MODULE.GradeResult(
        filename="No0108_1.c",
        compile="ok",
        compile_error="",
        tests_passed=2,
        tests_total=3,
        partial_score=None,
        score=66,
    )
    MODULE.save_result(result, submission_dir)
    json_path = submission_dir / "No0108_1_grade.json"
    self.assertTrue(json_path.exists())
    data = json.loads(json_path.read_text(encoding="utf-8"))
    self.assertEqual(data["filename"], "No0108_1.c")
    self.assertEqual(data["compile"], "ok")
    self.assertEqual(data["tests_passed"], 2)
    self.assertEqual(data["tests_total"], 3)
    self.assertIsNone(data["partial_score"])
    self.assertEqual(data["score"], 66)
```

- [ ] **Step 2: テストが失敗することを確認する**

```bash
python -m pytest tests/test_grader.py::GraderTest::test_print_result_compile_ok tests/test_grader.py::GraderTest::test_print_result_compile_error tests/test_grader.py::GraderTest::test_save_result_creates_json -v
```

Expected: 3 tests `FAILED`（`AttributeError: module 'grader' has no attribute 'print_result'`）

- [ ] **Step 3: print_result と save_result を grader.py に追加する**

`grade_file()` の定義の後に追記する:

```python
def print_result(result: GradeResult) -> None:
    print(f"--- 採点結果: {result.filename} ---")
    if result.compile == "error":
        print("コンパイル: エラー")
        if result.compile_error:
            print(result.compile_error, end="")
    else:
        print("コンパイル: OK")
        if result.tests_total > 0:
            print(f"テスト: {result.tests_passed}/{result.tests_total} 通過")
    print(f"スコア: {result.score}点")


def save_result(result: GradeResult, dest_dir: Path) -> None:
    stem = Path(result.filename).stem
    path = dest_dir / f"{stem}_grade.json"
    path.write_text(
        json.dumps(asdict(result), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
```

- [ ] **Step 4: 全テストが通ることを確認する**

```bash
python -m pytest tests/test_grader.py -v
```

Expected: 8 tests `PASSED`

- [ ] **Step 5: コミットする**

```bash
git add grader.py tests/test_grader.py
git commit -m "Add print_result and save_result to grader"
```

---

## Task 5: yorosikuonegaishima-su.py に採点を統合する

**Files:**
- Modify: `yorosikuonegaishima-su.py`
- Modify: `tests/test_submission_script.py`

- [ ] **Step 1: 統合テストを tests/test_submission_script.py に追加する**

`SubmissionScriptTest` クラスに以下のメソッドを追加する:

```python
def test_process_submission_shows_grade_result(self) -> None:
    assignment_dir, question_root, submission_root = self.make_workspace()
    submission_root.mkdir()
    (assignment_dir / "No0108_1.c").write_text(
        "#include <stdio.h>\nint main(void){return 0;}\n",
        encoding="utf-8",
    )
    (question_root / "j2pro0108.md").write_text("No0108_1.c, 100\n", encoding="utf-8")

    exit_code, output = self.run_submission(assignment_dir, question_root, submission_root)

    self.assertEqual(exit_code, 0)
    self.assertIn("採点結果", output)
    self.assertIn("コンパイル: OK", output)
    self.assertIn("スコア: 0点", output)  # テストケースなしのため 0点
    self.assertTrue((submission_root / "No0108_1_grade.json").exists())
```

- [ ] **Step 2: テストが失敗することを確認する**

```bash
python -m pytest tests/test_submission_script.py::SubmissionScriptTest::test_process_submission_shows_grade_result -v
```

Expected: `FAILED`（採点結果が出力されていないため）

- [ ] **Step 3: yorosikuonegaishima-su.py を修正してgraderを呼び出す**

`yorosikuonegaishima-su.py` の先頭 import ブロックに以下を追加する（`from pathlib import Path` の後）:

```python
_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))
import grader
```

次に、`process_submission()` 内のファイルコピー処理（`shutil.copy2` と `print` の2箇所）の後に採点呼び出しを追加する。変更後のループ全体は以下になる:

```python
    accepted_count = 0
    for source_path in c_files:
        if source_path.name not in allowed_filenames:
            print(f"{source_path.name}: 受理しません。設定ファイルに存在しないファイル名です。")
            continue

        destination_path = destination_root / source_path.name
        if destination_path.exists():
            shutil.copy2(source_path, destination_path)
            print(f"{source_path.name}: 上書きしました。")
        else:
            shutil.copy2(source_path, destination_path)
            print(f"{source_path.name}: 新規に提出しました。")
        accepted_count += 1

        result = grader.grade_file(destination_path, question_root, assignment_name)
        grader.print_result(result)
        grader.save_result(result, destination_path.parent)
```

- [ ] **Step 4: 全テストが通ることを確認する**

```bash
python -m pytest tests/ -v
```

Expected: 全テスト `PASSED`

- [ ] **Step 5: コミットする**

```bash
git add yorosikuonegaishima-su.py tests/test_submission_script.py
git commit -m "Integrate grader into process_submission"
```

---

## 完成確認

- [ ] **全テストが通ることを最終確認する**

```bash
python -m pytest tests/ -v
```

Expected output（抜粋）:
```
tests/test_grader.py::GraderTest::test_grade_result_has_expected_fields PASSED
tests/test_grader.py::GraderTest::test_compile_error_returns_error_result PASSED
tests/test_grader.py::GraderTest::test_compile_ok_returns_ok_result PASSED
tests/test_grader.py::GraderTest::test_compile_ok_no_testcases PASSED
tests/test_grader.py::GraderTest::test_all_tests_pass PASSED
tests/test_grader.py::GraderTest::test_partial_tests_pass PASSED
tests/test_grader.py::GraderTest::test_print_result_compile_ok PASSED
tests/test_grader.py::GraderTest::test_print_result_compile_error PASSED
tests/test_grader.py::GraderTest::test_save_result_creates_json PASSED
tests/test_submission_script.py::SubmissionScriptTest::test_process_submission_shows_grade_result PASSED
```
