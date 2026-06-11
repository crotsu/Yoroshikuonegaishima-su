#!/usr/bin/env python3

from __future__ import annotations

import csv
import shutil
import sys
from pathlib import Path


__version__ = "1.0.0"

# 名簿（学籍番号などを記載した CSV）
ROSTER_PATH = Path("/home/jstaff/oeda/tools/config/j25.csv")
# 学生ホームのベース（/home/jstudent/<j学籍>/J2program/j2exam<日付>）
STUDENT_HOME_BASE = Path("/home/jstudent")
PROGRAM_SUBDIR = "J2program"


def _student_to_user(student_id: str) -> str:
    """学籍番号 25-401 → ディレクトリ名 j25401 に変換する。"""
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


def collect_exam(
    date: str,
    roster: list[tuple[str, str]],
    student_home_base: Path,
    dest_base: Path,
) -> int:
    """各学生のホームにある j2exam<date> を dest_base/j2exam<date>/<j学籍>/ へコピーする。"""
    exam_dir = f"j2exam{date}"
    for sid, _name in roster:
        user = _student_to_user(sid)
        src = student_home_base / user / PROGRAM_SUBDIR / exam_dir
        dst = dest_base / exam_dir / user
        # is_dir() は権限拒否(EACCES)を例外として投げる。1人で止まらないよう捕捉する。
        try:
            exists = src.is_dir()
        except OSError as e:
            print(f"{user} アクセスできません: {e}")
            continue
        if not exists:
            print(f"{user} {exam_dir}がない")
            continue
        try:
            shutil.copytree(src, dst, dirs_exist_ok=True)
        except OSError as e:
            print(f"{user} コピー失敗: {e}")
            continue
        print(f"{user} コピー完了")
    return 0


def main(argv: list[str]) -> int:
    if len(argv) == 2 and argv[1] in ("--version", "-v"):
        print(__version__)
        return 0

    if len(argv) != 2:
        print("使い方: get_j2exam.py <日付>   例: get_j2exam.py 0611")
        return 1

    date = argv[1]
    try:
        roster = _load_roster(ROSTER_PATH)
    except FileNotFoundError as e:
        print(e)
        return 1

    return collect_exam(
        date=date,
        roster=roster,
        student_home_base=STUDENT_HOME_BASE,
        dest_base=Path.cwd(),
    )


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
