from __future__ import annotations

from contextlib import redirect_stdout
from io import StringIO
import getpass
import importlib.util
import os
from pathlib import Path
import tempfile
import unittest


SCRIPT_PATH = Path(__file__).resolve().parent.parent / "yoroshikuonegaishima-su.py"
SPEC = importlib.util.spec_from_file_location("submission_script", SCRIPT_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def _write_md(question_root: Path, name: str, data: str, encoding: str = "utf-8") -> None:
    d = question_root / name
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{name}.md").write_text(data, encoding=encoding)


class SubmissionScriptTest(unittest.TestCase):
    def make_workspace(self) -> tuple[Path, Path, Path]:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        root = Path(temp_dir.name)
        assignment_dir = root / "j2pro0108"
        question_root = root / "question"
        submission_root = root / "submissions"
        assignment_dir.mkdir()
        question_root.mkdir()
        return assignment_dir, question_root, submission_root

    def run_submission(
        self, assignment_dir: Path, question_root: Path, submission_root: Path
    ) -> tuple[int, str]:
        output = StringIO()
        with redirect_stdout(output):
            exit_code = MODULE.process_submission(
                assignment_dir,
                question_root=question_root,
                submission_root=submission_root,
            )
        return exit_code, output.getvalue()

    def test_main_prints_version(self) -> None:
        output = StringIO()
        with redirect_stdout(output):
            exit_code = MODULE.main(["yoroshikuonegaishima-su", "--version"])

        self.assertEqual(exit_code, 0)
        self.assertIn(MODULE.__version__, output.getvalue())

    def test_main_returns_usage_error_for_too_many_arguments(self) -> None:
        output = StringIO()
        with redirect_stdout(output):
            exit_code = MODULE.main(["yoroshikuonegaishima-su.py", "dir1", "dir2"])

        self.assertEqual(exit_code, 1)
        self.assertIn("使い方: yoroshikuonegaishima-su [課題ディレクトリ]", output.getvalue())

    def test_main_uses_current_directory_when_no_argument(self) -> None:
        assignment_dir, question_root, _ = self.make_workspace()
        root = assignment_dir.parent
        submission_base = root / "sub"
        submission_root = submission_base / getpass.getuser() / assignment_dir.name
        submission_root.mkdir(parents=True)
        (assignment_dir / "No0108_1.c").write_text(
            "#include <stdio.h>\nint main(void){return 0;}\n", encoding="utf-8"
        )
        _write_md(question_root, "j2pro0108", "No0108_1.c, 100\n", encoding="utf-8")

        class FakeConfig:
            QUESTION_ROOT = str(question_root)
            SUBMISSION_BASE = str(submission_base)

        original_load = MODULE._load_config
        original_cwd = Path.cwd()
        MODULE._load_config = lambda: FakeConfig
        try:
            os.chdir(assignment_dir)
            output = StringIO()
            with redirect_stdout(output):
                exit_code = MODULE.main(["yoroshikuonegaishima-su.py"])
        finally:
            os.chdir(original_cwd)
            MODULE._load_config = original_load

        self.assertEqual(exit_code, 0)
        self.assertIn("No0108_1.c: 新規に提出しました。", output.getvalue())
        self.assertTrue((submission_root / "No0108_1.c").is_file())

    def test_process_submission_reports_missing_assignment_directory(self) -> None:
        _, question_root, submission_root = self.make_workspace()
        output = StringIO()
        with redirect_stdout(output):
            exit_code = MODULE.process_submission(
                Path("does-not-exist"), question_root=question_root, submission_root=submission_root
            )

        self.assertEqual(exit_code, 1)
        self.assertIn("課題ディレクトリが存在しません。", output.getvalue())
        self.assertIn("使い方: yoroshikuonegaishima-su [課題ディレクトリ]", output.getvalue())

    def test_process_submission_reports_missing_config_file(self) -> None:
        assignment_dir, question_root, submission_root = self.make_workspace()

        exit_code, output = self.run_submission(assignment_dir, question_root, submission_root)

        self.assertEqual(exit_code, 1)
        self.assertIn("設定ファイルが存在しません。", output)
        self.assertIn("使い方: yoroshikuonegaishima-su [課題ディレクトリ]", output)

    def test_process_submission_reports_when_no_c_files_exist(self) -> None:
        assignment_dir, question_root, submission_root = self.make_workspace()
        (assignment_dir / "memo.txt").write_text("ignore\n", encoding="utf-8")
        _write_md(question_root, "j2pro0108", "No0108_1.c, 100\n", encoding="utf-8")

        exit_code, output = self.run_submission(assignment_dir, question_root, submission_root)

        self.assertEqual(exit_code, 0)
        self.assertIn("送信対象の .c ファイルがありません。", output)
        self.assertFalse(submission_root.exists())

    def test_process_submission_reports_missing_submission_directory(self) -> None:
        assignment_dir, question_root, submission_root = self.make_workspace()
        (assignment_dir / "No0108_1.c").write_text("int main(void){return 0;}\n", encoding="utf-8")
        _write_md(question_root, "j2pro0108", "No0108_1.c, 100\n", encoding="utf-8")

        exit_code, output = self.run_submission(assignment_dir, question_root, submission_root)

        self.assertEqual(exit_code, 1)
        self.assertIn("提出先ディレクトリが存在しません。", output)

    def test_process_submission_accepts_only_matching_c_files(self) -> None:
        assignment_dir, question_root, submission_root = self.make_workspace()
        submission_root.mkdir()
        (assignment_dir / "No0108_1.c").write_text("int main(void){return 0;}\n", encoding="utf-8")
        (assignment_dir / "No0108_2.c").write_text("int main(void){return 1;}\n", encoding="utf-8")
        (assignment_dir / "No0108_3.c").write_text("int main(void){return 2;}\n", encoding="utf-8")
        (assignment_dir / "note.txt").write_text("ignored\n", encoding="utf-8")
        _write_md(question_root, "j2pro0108", 
            "No0108_1.c, 100\nNo0108_2.c, 200\n", encoding="utf-8"
        )

        exit_code, output = self.run_submission(assignment_dir, question_root, submission_root)

        self.assertEqual(exit_code, 0)
        self.assertIn("No0108_1.c: 新規に提出しました。", output)
        self.assertIn("No0108_2.c: 新規に提出しました。", output)
        self.assertNotIn("No0108_3.c", output)
        self.assertTrue((submission_root / "No0108_1.c").is_file())
        self.assertTrue((submission_root / "No0108_2.c").is_file())
        self.assertFalse((submission_root / "No0108_3.c").exists())

    def test_process_submission_shows_grade_result(self) -> None:
        assignment_dir, question_root, submission_root = self.make_workspace()
        submission_root.mkdir()
        (assignment_dir / "No0108_1.c").write_text(
            "#include <stdio.h>\nint main(void){return 0;}\n",
            encoding="utf-8",
        )
        _write_md(question_root, "j2pro0108", "No0108_1.c, 100\n", encoding="utf-8")

        exit_code, output = self.run_submission(assignment_dir, question_root, submission_root)

        self.assertEqual(exit_code, 0)
        self.assertIn("採点結果", output)
        self.assertIn("コンパイル: OK", output)
        self.assertNotIn("スコア", output)  # テストケースなしのときはスコアを表示しない
        self.assertTrue((submission_root / "No0108_1_grade.json").exists())

    def test_process_submission_handles_permission_error(self) -> None:
        # 設問ディレクトリが権限で読めなくても、クラッシュせず分かりやすく終了する
        if os.geteuid() == 0:
            self.skipTest("root はパーミッションを無視するため")
        assignment_dir, question_root, submission_root = self.make_workspace()
        submission_root.mkdir()
        (assignment_dir / "No0108_1.c").write_text("int main(void){return 0;}\n", encoding="utf-8")
        md_dir = question_root / "j2pro0108"
        md_dir.mkdir(parents=True)
        (md_dir / "j2pro0108.md").write_text("No0108_1.c\n", encoding="utf-8")
        md_dir.chmod(0o000)  # 学生から見えない状態を再現
        self.addCleanup(lambda: md_dir.chmod(0o755))

        exit_code, output = self.run_submission(assignment_dir, question_root, submission_root)

        self.assertEqual(exit_code, 1)
        self.assertIn("権限", output)  # PermissionError ではなくメッセージ

    def test_process_submission_accepts_filename_only_md(self) -> None:
        # 点数なし・ファイル名だけの .md（試験で使う形式）でも受理できる
        assignment_dir, question_root, submission_root = self.make_workspace()
        submission_root.mkdir()
        (assignment_dir / "No0108_1.c").write_text(
            "#include <stdio.h>\nint main(void){return 0;}\n", encoding="utf-8"
        )
        _write_md(question_root, "j2pro0108", "No0108_1.c\nNo0108_2.c\n", encoding="utf-8")

        exit_code, output = self.run_submission(assignment_dir, question_root, submission_root)

        self.assertEqual(exit_code, 0)
        self.assertIn("No0108_1.c: 新規に提出しました。", output)
        self.assertNotIn("受理されたファイルはありませんでした。", output)
        self.assertTrue((submission_root / "No0108_1.c").is_file())

    def test_process_submission_exam_mode_hides_grade_result(self) -> None:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        root = Path(temp_dir.name)
        assignment_dir = root / "j2exam0611"
        question_root = root / "question"
        submission_root = root / "submissions"
        assignment_dir.mkdir()
        question_root.mkdir()
        submission_root.mkdir()
        (assignment_dir / "No0611_1.c").write_text(
            "#include <stdio.h>\nint main(void){return 0;}\n", encoding="utf-8"
        )
        _write_md(question_root, "j2exam0611", "No0611_1.c, 100\n", encoding="utf-8")

        exit_code, output = self.run_submission(assignment_dir, question_root, submission_root)

        self.assertEqual(exit_code, 0)
        self.assertIn("No0611_1.c: 新規に提出しました。", output)  # 受領の確認は表示する
        self.assertNotIn("採点結果", output)  # 試験では採点結果を見せない
        self.assertNotIn("コンパイル", output)
        self.assertTrue((submission_root / "No0611_1.c").is_file())  # ファイルは受領
        self.assertFalse((submission_root / "No0611_1_grade.json").exists())  # 採点しない

    def test_process_submission_overwrites_existing_submission(self) -> None:
        assignment_dir, question_root, submission_root = self.make_workspace()
        submission_root.mkdir()
        source_file = assignment_dir / "No0108_1.c"
        source_file.write_text("first\n", encoding="utf-8")
        _write_md(question_root, "j2pro0108", "No0108_1.c, 100\n", encoding="utf-8")

        first_exit_code, first_output = self.run_submission(
            assignment_dir, question_root, submission_root
        )
        source_file.write_text("second\n", encoding="utf-8")
        second_exit_code, second_output = self.run_submission(
            assignment_dir, question_root, submission_root
        )

        self.assertEqual(first_exit_code, 0)
        self.assertIn("No0108_1.c: 新規に提出しました。", first_output)
        self.assertEqual(second_exit_code, 0)
        self.assertIn("No0108_1.c: 上書きしました。", second_output)
        self.assertEqual((submission_root / "No0108_1.c").read_text(encoding="utf-8"), "second\n")


if __name__ == "__main__":
    unittest.main()
