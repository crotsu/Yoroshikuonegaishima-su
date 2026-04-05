from __future__ import annotations

from contextlib import redirect_stdout
from io import StringIO
import importlib.util
from pathlib import Path
import tempfile
import unittest


SCRIPT_PATH = Path(__file__).resolve().parent.parent / "yorosikuonegaishima-su.py"
SPEC = importlib.util.spec_from_file_location("submission_script", SCRIPT_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


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

    def test_main_returns_usage_error_for_invalid_arguments(self) -> None:
        output = StringIO()
        with redirect_stdout(output):
            exit_code = MODULE.main(["yorosikuonegaishima-su.py"])

        self.assertEqual(exit_code, 1)
        self.assertIn("使い方: yorosikuonegaishima-su <課題ディレクトリ>", output.getvalue())

    def test_process_submission_reports_missing_assignment_directory(self) -> None:
        _, question_root, submission_root = self.make_workspace()
        output = StringIO()
        with redirect_stdout(output):
            exit_code = MODULE.process_submission(
                Path("does-not-exist"), question_root=question_root, submission_root=submission_root
            )

        self.assertEqual(exit_code, 1)
        self.assertIn("課題ディレクトリが存在しません。", output.getvalue())
        self.assertIn("使い方: yorosikuonegaishima-su <課題ディレクトリ>", output.getvalue())

    def test_process_submission_reports_missing_config_file(self) -> None:
        assignment_dir, question_root, submission_root = self.make_workspace()

        exit_code, output = self.run_submission(assignment_dir, question_root, submission_root)

        self.assertEqual(exit_code, 1)
        self.assertIn("設定ファイルが存在しません。", output)
        self.assertIn("使い方: yorosikuonegaishima-su <課題ディレクトリ>", output)

    def test_process_submission_reports_when_no_c_files_exist(self) -> None:
        assignment_dir, question_root, submission_root = self.make_workspace()
        (assignment_dir / "memo.txt").write_text("ignore\n", encoding="utf-8")
        (question_root / "j2pro0108.md").write_text("No0108_1.c\n", encoding="utf-8")

        exit_code, output = self.run_submission(assignment_dir, question_root, submission_root)

        self.assertEqual(exit_code, 0)
        self.assertIn("送信対象の .c ファイルがありません。", output)
        self.assertFalse(submission_root.exists())

    def test_process_submission_reports_missing_submission_directory(self) -> None:
        assignment_dir, question_root, submission_root = self.make_workspace()
        (assignment_dir / "No0108_1.c").write_text("int main(void){return 0;}\n", encoding="utf-8")
        (question_root / "j2pro0108.md").write_text("No0108_1.c\n", encoding="utf-8")

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
        (question_root / "j2pro0108.md").write_text(
            "No0108_1.c\nNo0108_2.c\n", encoding="utf-8"
        )

        exit_code, output = self.run_submission(assignment_dir, question_root, submission_root)

        self.assertEqual(exit_code, 0)
        self.assertIn("No0108_1.c: 新規に提出しました。", output)
        self.assertIn("No0108_2.c: 新規に提出しました。", output)
        self.assertIn("No0108_3.c: 受理しません。設定ファイルに存在しないファイル名です。", output)
        self.assertTrue((submission_root / "No0108_1.c").is_file())
        self.assertTrue((submission_root / "No0108_2.c").is_file())
        self.assertFalse((submission_root / "No0108_3.c").exists())

    def test_process_submission_overwrites_existing_submission(self) -> None:
        assignment_dir, question_root, submission_root = self.make_workspace()
        submission_root.mkdir()
        source_file = assignment_dir / "No0108_1.c"
        source_file.write_text("first\n", encoding="utf-8")
        (question_root / "j2pro0108.md").write_text("No0108_1.c\n", encoding="utf-8")

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
