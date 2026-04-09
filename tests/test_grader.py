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
assert SPEC.loader is not None
sys.modules["grader"] = MODULE
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


if __name__ == "__main__":
    unittest.main()
