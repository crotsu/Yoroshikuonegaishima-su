#!/usr/bin/env python3

from __future__ import annotations

import csv
import importlib.util
from pathlib import Path
import sys


__version__ = "1.1.0"

CONFIG_PATH = Path("/home/class/j2/prog/.send/j25/questions/config.py")
ROSTER_PATH = Path(__file__).resolve().parent / "j25.csv"

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))
import scouter


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
    if not path.is_file():
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
        scouter.check_assignments(
            user=_student_to_user(sid),
            question_root=question_root,
            submission_base=submission_base,
        )
        print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
