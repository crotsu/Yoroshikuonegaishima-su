#!/usr/bin/env python3

from __future__ import annotations

import getpass
import importlib.util
from pathlib import Path
import shutil
import sys

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))
import grader


__version__ = "1.1.0"

CONFIG_PATH = Path("/home/class/j2/prog/.send/j25/questions/config.py")


def _load_config() -> object:
    if not CONFIG_PATH.is_file():
        raise FileNotFoundError(f"{CONFIG_PATH}: 設定ファイル config.py が見つかりません。")
    spec = importlib.util.spec_from_file_location("config", CONFIG_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_allowed_filenames(question_root: Path, assignment_name: str) -> tuple[set[str], Path]:
    config_path = question_root / f"{assignment_name}.md"
    if not config_path.is_file():
        raise FileNotFoundError(f"{config_path.name}: 設定ファイルが存在しません。")

    allowed = {
        line.split(",")[0].strip()
        for line in config_path.read_text(encoding="utf-8").splitlines()
        if "," in line
    }
    return allowed, config_path


def process_submission(
    assignment_dir: Path,
    question_root: Path,
    submission_root: Path,
) -> int:
    if not assignment_dir.is_dir():
        print(f"{assignment_dir}: 課題ディレクトリが存在しません。")
        print("使い方: yorosikuonegaishima-su <課題ディレクトリ>")
        return 1

    assignment_name = assignment_dir.name
    try:
        allowed_filenames, _ = load_allowed_filenames(question_root, assignment_name)
    except FileNotFoundError as error:
        print(error)
        print("使い方: yorosikuonegaishima-su <課題ディレクトリ>")
        return 1

    c_files = sorted(
        path for path in assignment_dir.iterdir() if path.is_file() and path.suffix == ".c"
    )
    if not c_files:
        print(f"{assignment_dir}: 送信対象の .c ファイルがありません。")
        return 0

    destination_root = submission_root
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

        result = grader.grade_file(destination_path, question_root, assignment_name)
        grader.print_result(result)
        grader.save_result(result, destination_path.parent)

    if accepted_count == 0:
        print("受理されたファイルはありませんでした。")

    return 0


def main(argv: list[str]) -> int:
    if len(argv) == 2 and argv[1] in ("--version", "-v"):
        print(__version__)
        return 0

    if len(argv) != 2:
        print("使い方: yorosikuonegaishima-su <課題ディレクトリ>")
        return 1

    assignment_dir = Path(argv[1])
    config = _load_config()
    try:
        question_root = Path(config.QUESTION_ROOT)
        submission_root = Path(config.SUBMISSION_BASE) / getpass.getuser() / assignment_dir.name
    except AttributeError as e:
        print(f"config.py の設定が不正です: {e}")
        return 1
    return process_submission(assignment_dir, question_root=question_root, submission_root=submission_root)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
