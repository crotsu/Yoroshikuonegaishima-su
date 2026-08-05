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
EXAM_DATE = "0730"


def _load_config() -> object:
    if not CONFIG_PATH.is_file():
        raise FileNotFoundError(f"{CONFIG_PATH.name}: 設定ファイルが存在しません。")
    spec = importlib.util.spec_from_file_location("config", CONFIG_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _is_readable_file(path: Path) -> bool:
    """権限などでアクセスできない場合はクラッシュせず False を返す。"""
    try:
        return path.is_file()
    except OSError:
        return False


def _parse_md(md_path: Path) -> list[str]:
    """試験定義ファイルからファイル名一覧を返す。

    ``No1.c`` のようにファイル名だけの行も、``No1.c, 100`` のように
    点数付きの行も受け付ける（点数は使わない）。空行と # で始まる行は無視する。
    """
    filenames = []
    for line in md_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        filename = stripped.split(",")[0].strip()
        if filename:
            filenames.append(filename)
    return filenames


def check_exam(user: str, question_root: Path, submission_base: Path, exam_date: str) -> int:
    dir_name = f"j2exam{exam_date}"
    md_path = question_root / dir_name / f"{dir_name}.md"

    print(user)

    if not _is_readable_file(md_path):
        print(f"{dir_name}.md: 設定ファイルが存在しません。")
        return 1

    try:
        filenames = _parse_md(md_path)
    except OSError:
        print(f"{dir_name}.md: 設定ファイルにアクセスできません（権限）。担当教員に連絡してください。")
        return 1
    total = len(filenames)
    submitted = 0

    for filename in filenames:
        filepath = submission_base / user / dir_name / filename
        if _is_readable_file(filepath):
            try:
                mtime = datetime.fromtimestamp(filepath.stat().st_mtime, tz=timezone(timedelta(hours=9))).strftime("%Y-%m-%d %H:%M:%S")
            except OSError:
                print(f"未提出  : {filename}")
                continue
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
    except OSError:
        print(f"{CONFIG_PATH.name}: 設定ファイルにアクセスできません（権限）。担当教員に連絡してください。")
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
