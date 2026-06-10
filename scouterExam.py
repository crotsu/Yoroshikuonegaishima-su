#!/usr/bin/env python3

from __future__ import annotations

import getpass
import importlib.util
from datetime import datetime, timezone, timedelta
from pathlib import Path
import sys


__version__ = "1.1.0"

CONFIG_PATH = Path("/home/class/j2/prog/.send/j25/questions/config.py")

# 対象試験日を手動で編集する（例: "0601" → j2exam0601）
EXAM_DATE = "0611"


def _load_config() -> object:
    if not CONFIG_PATH.is_file():
        raise FileNotFoundError(f"{CONFIG_PATH.name}: 設定ファイルが存在しません。")
    spec = importlib.util.spec_from_file_location("config", CONFIG_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _parse_md(md_path: Path) -> list[str]:
    filenames = []
    for line in md_path.read_text(encoding="utf-8").splitlines():
        if "," not in line:
            continue
        filename = line.split(",")[0].strip()
        if filename:
            filenames.append(filename)
    return filenames


def check_exam(user: str, question_root: Path, submission_base: Path, exam_date: str) -> int:
    dir_name = f"j2exam{exam_date}"
    md_path = question_root / dir_name / f"{dir_name}.md"

    print(user)

    if not md_path.is_file():
        print(f"{dir_name}.md: 設定ファイルが存在しません。")
        return 1

    filenames = _parse_md(md_path)
    total = len(filenames)
    submitted = 0

    for filename in filenames:
        filepath = submission_base / user / dir_name / filename
        if filepath.is_file():
            mtime = datetime.fromtimestamp(filepath.stat().st_mtime, tz=timezone(timedelta(hours=9))).strftime("%Y-%m-%d %H:%M:%S")
            print(f"O.K.    : {filename} ({mtime})")
            submitted += 1
        else:
            print(f"未提出  : {filename}")

    print(f"{submitted}/{total}")
    return 0


def main(argv: list[str]) -> int:
    try:
        config = _load_config()
    except FileNotFoundError as e:
        print(e)
        return 1

    try:
        question_root = Path(config.QUESTION_ROOT)
        submission_base = Path(config.SUBMISSION_BASE)
    except AttributeError as e:
        print(f"config.py の設定が不正です: {e}")
        return 1

    user = getpass.getuser()
    return check_exam(
        user=user,
        question_root=question_root,
        submission_base=submission_base,
        exam_date=EXAM_DATE,
    )


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
