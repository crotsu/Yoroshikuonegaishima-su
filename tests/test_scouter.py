from __future__ import annotations

from contextlib import redirect_stdout
from io import StringIO
import importlib.util
from pathlib import Path
import tempfile
import unittest


SCRIPT_PATH = Path(__file__).resolve().parent.parent / "scouter.py"
SPEC = importlib.util.spec_from_file_location("scouter", SCRIPT_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class ScouterTest(unittest.TestCase):
    def make_workspace(self) -> tuple[Path, Path, Path]:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        root = Path(temp_dir.name)
        question_root = root / "questions"
        submission_base = root / "submissions"
        question_root.mkdir()
        submission_base.mkdir()
        return root, question_root, submission_base

    def run_scouter(
        self, user: str, question_root: Path, submission_base: Path
    ) -> tuple[int, str]:
        output = StringIO()
        with redirect_stdout(output):
            exit_code = MODULE.check_assignments(
                user=user,
                question_root=question_root,
                submission_base=submission_base,
            )
        return exit_code, output.getvalue()

    def test_prints_userid(self) -> None:
        _, question_root, submission_base = self.make_workspace()
        _, output = self.run_scouter("j24001", question_root, submission_base)

        self.assertIn("j24001", output)

    def test_no_md_files_shows_zero_totals(self) -> None:
        _, question_root, submission_base = self.make_workspace()
        _, output = self.run_scouter("j24001", question_root, submission_base)

        self.assertIn("0/0", output)
        self.assertIn("Battle Point=0", output)

    def test_all_unsubmitted(self) -> None:
        _, question_root, submission_base = self.make_workspace()
        (question_root / "j2pro0408.md").write_text(
            "No0408_1.c, 123\nNo0408_2.c, 1251\n", encoding="utf-8"
        )

        exit_code, output = self.run_scouter("j24001", question_root, submission_base)

        self.assertEqual(exit_code, 0)
        self.assertIn("     : No0408_1.c", output)
        self.assertIn("     : No0408_2.c", output)
        self.assertIn("0/2", output)
        self.assertIn("Battle Point=0", output)

    def test_some_submitted(self) -> None:
        _, question_root, submission_base = self.make_workspace()
        (question_root / "j2pro0408.md").write_text(
            "No0408_1.c, 123\nNo0408_2.c, 1251\n", encoding="utf-8"
        )
        submitted_dir = submission_base / "j24001" / "j2pro0408"
        submitted_dir.mkdir(parents=True)
        (submitted_dir / "No0408_1.c").write_text("int main(){}", encoding="utf-8")

        exit_code, output = self.run_scouter("j24001", question_root, submission_base)

        self.assertEqual(exit_code, 0)
        self.assertIn("O.K. : No0408_1.c", output)
        self.assertIn("     : No0408_2.c", output)
        self.assertIn("1/2", output)
        self.assertIn("Battle Point=123", output)

    def test_all_submitted(self) -> None:
        _, question_root, submission_base = self.make_workspace()
        (question_root / "j2pro0408.md").write_text(
            "No0408_1.c, 123\nNo0408_2.c, 1251\n", encoding="utf-8"
        )
        submitted_dir = submission_base / "j24001" / "j2pro0408"
        submitted_dir.mkdir(parents=True)
        (submitted_dir / "No0408_1.c").write_text("int main(){}", encoding="utf-8")
        (submitted_dir / "No0408_2.c").write_text("int main(){}", encoding="utf-8")

        exit_code, output = self.run_scouter("j24001", question_root, submission_base)

        self.assertEqual(exit_code, 0)
        self.assertIn("O.K. : No0408_1.c", output)
        self.assertIn("O.K. : No0408_2.c", output)
        self.assertIn("2/2", output)
        self.assertIn("Battle Point=1374", output)

    def test_multiple_md_files_processed_in_order(self) -> None:
        _, question_root, submission_base = self.make_workspace()
        (question_root / "j2pro0408.md").write_text(
            "No0408_1.c, 100\n", encoding="utf-8"
        )
        (question_root / "j2pro0415.md").write_text(
            "No0415_1.c, 200\n", encoding="utf-8"
        )
        submitted_dir = submission_base / "j24001" / "j2pro0415"
        submitted_dir.mkdir(parents=True)
        (submitted_dir / "No0415_1.c").write_text("int main(){}", encoding="utf-8")

        exit_code, output = self.run_scouter("j24001", question_root, submission_base)

        self.assertEqual(exit_code, 0)
        self.assertIn("     : No0408_1.c", output)
        self.assertIn("O.K. : No0415_1.c", output)
        self.assertIn("1/2", output)
        self.assertIn("Battle Point=200", output)
        # j2pro0408 が j2pro0415 より前に出力される
        self.assertLess(output.index("No0408_1.c"), output.index("No0415_1.c"))

    def test_md_file_ignores_blank_lines(self) -> None:
        _, question_root, submission_base = self.make_workspace()
        (question_root / "j2pro0408.md").write_text(
            "\nNo0408_1.c, 123\n\nNo0408_2.c, 1251\n\n", encoding="utf-8"
        )

        _, output = self.run_scouter("j24001", question_root, submission_base)

        self.assertIn("0/2", output)

    def test_md_file_ignores_lines_without_comma(self) -> None:
        _, question_root, submission_base = self.make_workspace()
        (question_root / "j2pro0408.md").write_text(
            "# comment\nNo0408_1.c, 123\nNo0408_2.c, 1251\n", encoding="utf-8"
        )

        _, output = self.run_scouter("j24001", question_root, submission_base)

        self.assertIn("0/2", output)

    def test_missing_config_returns_error(self) -> None:
        original = MODULE.CONFIG_PATH
        MODULE.CONFIG_PATH = Path("/nonexistent/config.py")
        try:
            output = StringIO()
            with redirect_stdout(output):
                exit_code = MODULE.main(["scouter"])
            self.assertEqual(exit_code, 1)
            self.assertIn("設定ファイルが存在しません。", output.getvalue())
        finally:
            MODULE.CONFIG_PATH = original

    def test_user_submission_does_not_affect_other_user(self) -> None:
        _, question_root, submission_base = self.make_workspace()
        (question_root / "j2pro0408.md").write_text(
            "No0408_1.c, 123\n", encoding="utf-8"
        )
        # 別ユーザーの提出ファイルを作成
        other_dir = submission_base / "j24999" / "j2pro0408"
        other_dir.mkdir(parents=True)
        (other_dir / "No0408_1.c").write_text("int main(){}", encoding="utf-8")

        exit_code, output = self.run_scouter("j24001", question_root, submission_base)

        self.assertEqual(exit_code, 0)
        self.assertIn("     : No0408_1.c", output)
        self.assertIn("0/1", output)
        self.assertIn("Battle Point=0", output)


if __name__ == "__main__":
    unittest.main()
