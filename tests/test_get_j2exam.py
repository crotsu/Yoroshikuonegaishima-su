from __future__ import annotations

from contextlib import redirect_stdout
from io import StringIO
import importlib.util
from pathlib import Path
import tempfile
import unittest


SCRIPT_PATH = Path(__file__).resolve().parent.parent / "get_j2exam.py"
SPEC = importlib.util.spec_from_file_location("get_j2exam", SCRIPT_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class GetJ2examTest(unittest.TestCase):
    def make_workspace(self) -> tuple[Path, Path]:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        root = Path(temp_dir.name)
        student_home = root / "home"
        dest = root / "dest"
        student_home.mkdir()
        dest.mkdir()
        return student_home, dest

    def put_exam(self, student_home: Path, user: str, date: str, files: dict[str, str]) -> None:
        d = student_home / user / "J2program" / f"j2exam{date}"
        d.mkdir(parents=True)
        for name, content in files.items():
            (d / name).write_text(content, encoding="utf-8")

    def run_collect(self, date, roster, student_home, dest) -> tuple[int, str]:
        output = StringIO()
        with redirect_stdout(output):
            code = MODULE.collect_exam(
                date=date,
                roster=roster,
                student_home_base=student_home,
                dest_base=dest,
            )
        return code, output.getvalue()

    def test_student_to_user_strips_hyphen(self) -> None:
        self.assertEqual(MODULE._student_to_user("25-401"), "j25401")

    def test_copies_existing_and_reports_missing(self) -> None:
        student_home, dest = self.make_workspace()
        self.put_exam(student_home, "j25401", "0611", {"No1.c": "a", "No2.c": "b"})
        self.put_exam(student_home, "j25402", "0611", {"No1.c": "c"})
        # j25403 は j2exam0611 を持たない
        roster = [("25-401", ""), ("25-402", ""), ("25-403", "")]

        code, out = self.run_collect("0611", roster, student_home, dest)

        self.assertEqual(code, 0)
        self.assertIn("j25401 コピー完了", out)
        self.assertIn("j25402 コピー完了", out)
        self.assertIn("j25403 j2exam0611がない", out)

    def test_copied_files_land_in_correct_path_with_content(self) -> None:
        student_home, dest = self.make_workspace()
        self.put_exam(student_home, "j25401", "0611", {"No1.c": "hello", "No2.c": "world"})
        roster = [("25-401", "")]

        self.run_collect("0611", roster, student_home, dest)

        copied = dest / "j2exam0611" / "j25401"
        self.assertTrue((copied / "No1.c").is_file())
        self.assertTrue((copied / "No2.c").is_file())
        self.assertEqual((copied / "No1.c").read_text(encoding="utf-8"), "hello")
        self.assertEqual((copied / "No2.c").read_text(encoding="utf-8"), "world")

    def test_rerun_does_not_error(self) -> None:
        student_home, dest = self.make_workspace()
        self.put_exam(student_home, "j25401", "0611", {"No1.c": "a"})
        roster = [("25-401", "")]

        self.run_collect("0611", roster, student_home, dest)
        code, out = self.run_collect("0611", roster, student_home, dest)  # 2回目

        self.assertEqual(code, 0)
        self.assertIn("j25401 コピー完了", out)

    def test_inaccessible_dir_does_not_crash(self) -> None:
        # 権限で読めない学生がいても、クラッシュせず次に進む
        student_home, dest = self.make_workspace()
        # アクセスできる学生（コピーされる）
        self.put_exam(student_home, "j25402", "0611", {"No1.c": "ok"})
        # 読めない学生（J2program を 000 にして権限拒否を作る）
        blocked = student_home / "j25401" / "J2program"
        blocked.mkdir(parents=True)
        (blocked / "j2exam0611").mkdir()
        blocked.chmod(0o000)
        self.addCleanup(lambda: blocked.chmod(0o755))
        roster = [("25-401", ""), ("25-402", "")]

        code, out = self.run_collect("0611", roster, student_home, dest)

        self.assertEqual(code, 0)  # クラッシュしない
        self.assertIn("j25401", out)  # 読めない学生も何か知らせる
        self.assertIn("j25402 コピー完了", out)  # 後続の学生は処理される
        self.assertTrue((dest / "j2exam0611" / "j25402" / "No1.c").is_file())

    def test_dangling_symlink_does_not_fail_copy(self) -> None:
        # Emacs のロックファイル(.#xxx)のような壊れたシンボリックリンクがあっても
        # コピー失敗にならず、実体ファイルはコピーされる
        student_home, dest = self.make_workspace()
        d = student_home / "j25401" / "J2program" / "j2exam0611"
        d.mkdir(parents=True)
        (d / "No1.c").write_text("real", encoding="utf-8")
        (d / ".#No1.c").symlink_to("user@host.12345:678901234")  # 壊れたリンク
        roster = [("25-401", "")]

        code, out = self.run_collect("0611", roster, student_home, dest)

        self.assertEqual(code, 0)
        self.assertIn("j25401 コピー完了", out)
        self.assertNotIn("コピー失敗", out)
        self.assertTrue((dest / "j2exam0611" / "j25401" / "No1.c").is_file())

    def test_missing_message_uses_exam_dir_name(self) -> None:
        student_home, dest = self.make_workspace()
        roster = [("25-403", "")]

        _, out = self.run_collect("0611", roster, student_home, dest)

        self.assertIn("j25403 j2exam0611がない", out)


if __name__ == "__main__":
    unittest.main()
