from __future__ import annotations

from contextlib import redirect_stdout
from io import StringIO
import importlib.util
import os
from pathlib import Path
import tempfile
import unittest


SCRIPT_PATH = Path(__file__).resolve().parent.parent / "scouterExam.py"
SPEC = importlib.util.spec_from_file_location("scouterExam", SCRIPT_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)

EXAM_DATE = "0611"
EXAM_DIR = f"j2exam{EXAM_DATE}"


class ScouterExamTest(unittest.TestCase):
    def make_workspace(self) -> tuple[Path, Path]:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        root = Path(temp_dir.name)
        question_root = root / "questions"
        submission_base = root / "submissions"
        question_root.mkdir()
        submission_base.mkdir()
        return question_root, submission_base

    def write_md(self, question_root: Path, data: str) -> None:
        d = question_root / EXAM_DIR
        d.mkdir(parents=True, exist_ok=True)
        (d / f"{EXAM_DIR}.md").write_text(data, encoding="utf-8")

    def submit(self, submission_base: Path, user: str, name: str, content: str = "x") -> None:
        d = submission_base / user / EXAM_DIR
        d.mkdir(parents=True, exist_ok=True)
        (d / name).write_text(content, encoding="utf-8")

    def run_exam(self, user: str, question_root: Path, submission_base: Path) -> tuple[int, str]:
        output = StringIO()
        with redirect_stdout(output):
            code = MODULE.check_exam(
                user=user,
                question_root=question_root,
                submission_base=submission_base,
                exam_date=EXAM_DATE,
            )
        return code, output.getvalue()

    def test_shows_ok_and_unsubmitted(self) -> None:
        question_root, submission_base = self.make_workspace()
        self.write_md(question_root, "No1.c, 100\nNo2.c, 100\nNo3.c, 100\n")
        self.submit(submission_base, "j25442", "No1.c")
        self.submit(submission_base, "j25442", "No2.c")

        code, out = self.run_exam("j25442", question_root, submission_base)

        self.assertEqual(code, 0)
        self.assertIn("j25442", out)
        self.assertIn("O.K.    : No1.c", out)
        self.assertIn("O.K.    : No2.c", out)
        self.assertIn("未提出  : No3.c", out)
        self.assertIn("2/3", out)

    def test_md_filename_only(self) -> None:
        # 点数なし・ファイル名だけの .md でも動作する
        question_root, submission_base = self.make_workspace()
        self.write_md(question_root, "No1.c\nNo2.c\nNo3.c\n")
        self.submit(submission_base, "j25442", "No1.c")

        code, out = self.run_exam("j25442", question_root, submission_base)

        self.assertEqual(code, 0)
        self.assertIn("O.K.    : No1.c", out)
        self.assertIn("未提出  : No2.c", out)
        self.assertIn("未提出  : No3.c", out)
        self.assertIn("1/3", out)

    def test_does_not_compile_or_grade(self) -> None:
        # 不正な C でも、コンパイルせず受領のみ → O.K.
        question_root, submission_base = self.make_workspace()
        self.write_md(question_root, "No1.c\n")
        self.submit(submission_base, "j25442", "No1.c", content="this is not valid C")

        code, out = self.run_exam("j25442", question_root, submission_base)

        self.assertEqual(code, 0)
        self.assertIn("O.K.    : No1.c", out)
        self.assertNotIn("コンパイル", out)
        self.assertNotIn("スコア", out)

    def test_blank_and_comment_lines_ignored(self) -> None:
        question_root, submission_base = self.make_workspace()
        self.write_md(question_root, "# 試験0611\n\nNo1.c\n\n")
        self.submit(submission_base, "j25442", "No1.c")

        code, out = self.run_exam("j25442", question_root, submission_base)

        self.assertEqual(code, 0)
        self.assertIn("O.K.    : No1.c", out)
        self.assertNotIn("試験0611", out)  # コメント行はファイル名扱いしない
        self.assertIn("1/1", out)

    def test_missing_md_returns_error(self) -> None:
        question_root, submission_base = self.make_workspace()

        code, out = self.run_exam("j25442", question_root, submission_base)

        self.assertEqual(code, 1)
        self.assertIn(f"{EXAM_DIR}.md: 設定ファイルが存在しません。", out)

    def test_unreadable_md_dir_returns_error(self) -> None:
        # 権限で読めない試験ディレクトリでもトレースバックを出さずに終了する
        if os.geteuid() == 0:
            self.skipTest("root はパーミッションを無視するため")
        question_root, submission_base = self.make_workspace()
        self.write_md(question_root, "No1.c\n")
        hidden = question_root / EXAM_DIR
        hidden.chmod(0o000)
        self.addCleanup(lambda: hidden.chmod(0o755))

        code, out = self.run_exam("j25442", question_root, submission_base)

        self.assertEqual(code, 1)
        self.assertIn(f"{EXAM_DIR}.md", out)


if __name__ == "__main__":
    unittest.main()
