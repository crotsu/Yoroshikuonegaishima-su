#!/usr/bin/env python3

from __future__ import annotations

import getpass
import importlib.util
from pathlib import Path
import sys


__version__ = "1.0.0"

CONFIG_PATH = Path("/home/class/j2/prog/.send/j25/questions/config.py")


def _load_config() -> object:
    if not CONFIG_PATH.is_file():
        raise FileNotFoundError(f"{CONFIG_PATH.name}: 設定ファイルが存在しません。")
    spec = importlib.util.spec_from_file_location("config", CONFIG_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _parse_md(md_path: Path) -> list[tuple[str, int]]:
    entries = []
    for line in md_path.read_text(encoding="utf-8").splitlines():
        if "," not in line:
            continue
        filename, point_str = line.split(",", 1)
        filename = filename.strip()
        if not filename:
            continue
        entries.append((filename, int(point_str.strip())))
    return entries


def check_assignments(user: str, question_root: Path, submission_base: Path) -> int:
    print(user)

    md_files = sorted(question_root.glob("*.md"))

    total = 0
    submitted = 0
    battle_point = 0

    for md_path in md_files:
        dir_name = md_path.stem
        for filename, point in _parse_md(md_path):
            filepath = submission_base / user / dir_name / filename
            total += 1
            if filepath.is_file():
                print(f"O.K. : {filename}")
                submitted += 1
                battle_point += point
            else:
                print(f"     : {filename}")

    print(f"{submitted}/{total}")
    print(f"Battle Point={battle_point}")
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
    return check_assignments(user=user, question_root=question_root, submission_base=submission_base)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
