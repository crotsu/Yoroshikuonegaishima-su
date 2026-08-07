#!/usr/bin/env python3

from __future__ import annotations

import csv
import importlib.util
from importlib.machinery import SourceFileLoader
from pathlib import Path
import sys


__version__ = "1.1.0"

CONFIG_PATH = Path("/home/class/j2/prog/.send/j25/questions/config.py")
ROSTER_PATH = Path("/home/jstaff/oeda/tools/config/j25.csv")

_SCRIPT_DIR = Path(__file__).resolve().parent


def _load_scouterExam():
    for candidate in (_SCRIPT_DIR / "scouterExam.py", _SCRIPT_DIR / "scouterExam"):
        if candidate.is_file():
            loader = SourceFileLoader("scouterExam", str(candidate))
            spec = importlib.util.spec_from_loader("scouterExam", loader)
            module = importlib.util.module_from_spec(spec)
            loader.exec_module(module)
            return module
    raise FileNotFoundError("scouterExam スクリプトが見つかりません。")


scouterExam = _load_scouterExam()


def _load_config() -> object:
    if not CONFIG_PATH.is_file():
        raise FileNotFoundError(f"{CONFIG_PATH.name}: 設定ファイルが存在しません。")
    spec = importlib.util.spec_from_file_location("config", CONFIG_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _student_to_user(student_id: str) -> str:
    return "j" + student_id.replace("-", "")


def _load_roster(path: Path) -> list[tuple[str, str]]:
    try:
        exists = path.is_file()
    except OSError:
        exists = False
    if not exists:
        raise FileNotFoundError(f"{path}: 学生名簿が存在しません。")
    students = []
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            sid = (row.get("学籍番号") or "").strip()
            name = (row.get("氏名") or "").strip()
            if sid:
                students.append((sid, name))
    return students


def _count_submitted(user: str, question_root: Path, submission_base: Path, exam_date: str) -> tuple[int, int]:
    """(提出数, 課題数) を返す。定義ファイルが読めない場合は (0, 0)。"""
    dir_name = f"j2exam{exam_date}"
    md_path = question_root / dir_name / f"{dir_name}.md"

    if not scouterExam._is_readable_file(md_path):
        return 0, 0
    try:
        filenames = scouterExam._parse_md(md_path)
    except OSError:
        return 0, 0

    submitted = 0
    for filename in filenames:
        filepath = submission_base / user / dir_name / filename
        if scouterExam._is_readable_file(filepath):
            try:
                filepath.stat()
            except OSError:
                continue
            submitted += 1
    return submitted, len(filenames)


def main(argv: list[str]) -> int:
    try:
        config = _load_config()
        roster = _load_roster(ROSTER_PATH)
    except FileNotFoundError as e:
        print(e)
        return 1

    try:
        question_root = Path(config.QUESTION_ROOT)
        submission_base = Path(config.SUBMISSION_BASE)
    except AttributeError as e:
        print(f"config.py の設定が不正です: {e}")
        return 1

    for sid, name in roster:
        print(f"{sid},{name}")
        scouterExam.check_exam(
            user=_student_to_user(sid),
            question_root=question_root,
            submission_base=submission_base,
            exam_date=scouterExam.EXAM_DATE,
        )
        print()

    print(f"===== 提出状況一覧（j2exam{scouterExam.EXAM_DATE}） =====")
    for sid, name in roster:
        submitted, total = _count_submitted(
            user=_student_to_user(sid),
            question_root=question_root,
            submission_base=submission_base,
            exam_date=scouterExam.EXAM_DATE,
        )
        print(f"{sid},{name},{submitted}/{total}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
