#!/usr/bin/env python3

from __future__ import annotations

import getpass
from pathlib import Path
import shutil
import sys


QUESTION_ROOT = Path("/home/class/j2/prog/.send/j25/questions")
SUBMISSION_BASE = Path("/home/class/j2/prog/.send/j25")


def load_allowed_filenames(question_root: Path, assignment_name: str) -> tuple[set[str], Path]:
    config_path = question_root / f"{assignment_name}.md"
    if not config_path.is_file():
        raise FileNotFoundError(f"{config_path}: 設定ファイルが存在しません。")

    allowed = {
        line.strip()
        for line in config_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    }
    return allowed, config_path


def process_submission(
    assignment_dir: Path,
    question_root: Path = QUESTION_ROOT,
    submission_root: Path | None = None,
) -> int:
    if not assignment_dir.is_dir():
        print(f"{assignment_dir}: 課題ディレクトリが存在しません。")
        return 1

    assignment_name = assignment_dir.name
    try:
        allowed_filenames, _ = load_allowed_filenames(question_root, assignment_name)
    except FileNotFoundError as error:
        print(error)
        return 1

    c_files = sorted(
        path for path in assignment_dir.iterdir() if path.is_file() and path.suffix == ".c"
    )
    if not c_files:
        print(f"{assignment_dir}: 送信対象の .c ファイルがありません。")
        return 0

    destination_root = submission_root if submission_root is not None else SUBMISSION_BASE / getpass.getuser() / assignment_name
    if not destination_root.is_dir():
        print(f"{destination_root}: 提出先ディレクトリが存在しません。")
        return 1

    accepted_count = 0
    for source_path in c_files:
        if source_path.name not in allowed_filenames:
            print(f"{source_path.name}: 受理しません。設定ファイルに存在しないファイル名です。")
            continue

        destination_path = destination_root / source_path.name
        if destination_path.exists():
            shutil.copy2(source_path, destination_path)
            print(f"{source_path.name}: 上書きしました。")
        else:
            shutil.copy2(source_path, destination_path)
            print(f"{source_path.name}: 新規に提出しました。")
        accepted_count += 1

    if accepted_count == 0:
        print("受理されたファイルはありませんでした。")

    return 0


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("使い方: yorosikuonegaishima-su.py <課題ディレクトリ>")
        return 1

    assignment_dir = Path(argv[1])
    submission_root = SUBMISSION_BASE / getpass.getuser() / assignment_dir.name
    return process_submission(assignment_dir, submission_root=submission_root)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
