#!/usr/bin/env python3

from __future__ import annotations

import getpass
import importlib.util
from importlib.machinery import SourceFileLoader
from pathlib import Path
import sys


__version__ = "1.1.0"

CONFIG_PATH = Path("/home/class/j2/prog/.send/j25/questions/config.py")

_SCRIPT_DIR = Path(__file__).resolve().parent


def _load_scouter():
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


def chohatten_dirs(question_root: Path, term: str) -> list[Path]:
    """前期/後期に対応する chohatten_* ディレクトリ一覧を返す。"""
    prefix = "chohatten_zenki" if term == "zenki" else "chohatten_kouki"
    return [d for d in question_root.glob(f"{prefix}*") if d.is_dir()]


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

    term = scouter.current_term()
    dirs = chohatten_dirs(question_root, term)
    user = getpass.getuser()
    return scouter.check_assignments(
        user=user,
        question_root=question_root,
        submission_base=submission_base,
        md_dirs=dirs,
    )


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
