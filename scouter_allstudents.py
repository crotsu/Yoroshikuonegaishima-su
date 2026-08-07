#!/usr/bin/env python3

from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path
import sys


__version__ = "1.1.0"

CONFIG_PATH = Path("/home/class/j2/prog/.send/j25/questions/config.py")
ROSTER_PATH = Path("/home/jstaff/oeda/tools/config/j25.csv")

_SCRIPT_DIR = Path(__file__).resolve().parent


def _load_scouter():
    from importlib.machinery import SourceFileLoader
    for candidate in (_SCRIPT_DIR / "scouter.py", _SCRIPT_DIR / "scouter"):
        if candidate.is_file():
            loader = SourceFileLoader("scouter", str(candidate))
            spec = importlib.util.spec_from_loader("scouter", loader)
            module = importlib.util.module_from_spec(spec)
            loader.exec_module(module)
            return module
    raise FileNotFoundError("scouter スクリプトが見つかりません。")


scouter = _load_scouter()


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


def _count_submitted(
    user: str,
    submission_base: Path,
    md_dirs: list[Path],
) -> tuple[int, int]:
    """(提出数, 課題数) を返す。check_assignments と同じ判定を出力せずに行う。"""
    total = 0
    submitted = 0

    for assignment_dir in sorted(md_dirs):
        dir_name = assignment_dir.name
        md_path = assignment_dir / f"{dir_name}.md"
        if not scouter._is_readable_file(md_path):
            continue
        for filename, _point in scouter._parse_md(md_path):
            filepath = submission_base / user / dir_name / filename
            total += 1
            if not scouter._is_readable_file(filepath):
                continue
            try:
                filepath.stat()
            except OSError:
                continue
            stem = Path(filename).stem
            grade_json = filepath.parent / f"{stem}_grade.json"
            score = None
            if scouter._is_readable_file(grade_json):
                try:
                    score = json.loads(grade_json.read_text(encoding="utf-8")).get("score", 100)
                except (OSError, ValueError):
                    score = None  # 読めない・壊れている → 採点情報なし扱い
            if score is not None and score <= 0:
                continue  # [error] 扱い
            submitted += 1

    return submitted, total


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

    term = scouter.current_term()
    md_dirs = scouter.j2pro_dirs(question_root, term)

    for sid, name in roster:
        print(f"{sid},{name}")
        scouter.check_assignments(
            user=_student_to_user(sid),
            question_root=question_root,
            submission_base=submission_base,
            md_dirs=md_dirs,
        )
        print()

    print(f"===== 提出状況一覧（{term}） =====")
    for sid, name in roster:
        submitted, total = _count_submitted(
            user=_student_to_user(sid),
            submission_base=submission_base,
            md_dirs=md_dirs,
        )
        print(f"{sid},{name},{submitted}/{total}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
