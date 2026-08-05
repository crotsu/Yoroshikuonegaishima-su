#!/usr/bin/env python3

from __future__ import annotations

import getpass
import importlib.util
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
import re
import sys


__version__ = "1.1.0"

CONFIG_PATH = Path("/home/class/j2/prog/.send/j25/questions/config.py")


def _load_config() -> object:
    if not CONFIG_PATH.is_file():
        raise FileNotFoundError(f"{CONFIG_PATH.name}: 設定ファイルが存在しません。")
    spec = importlib.util.spec_from_file_location("config", CONFIG_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def current_term() -> str:
    """現在月から前期(zenki)・後期(kouki)を返す。"""
    month = datetime.now().month
    if 4 <= month <= 8:
        return "zenki"
    return "kouki"


def _is_readable_file(path: Path) -> bool:
    """権限などでアクセスできない場合はクラッシュせず False を返す。"""
    try:
        return path.is_file()
    except OSError:
        return False


def _is_readable_dir(path: Path) -> bool:
    """権限などでアクセスできない場合はクラッシュせず False を返す。"""
    try:
        return path.is_dir()
    except OSError:
        return False


def _parse_md(md_path: Path) -> list[tuple[str, int]]:
    entries = []
    try:
        text = md_path.read_text(encoding="utf-8")
    except OSError:
        return []
    for line in text.splitlines():
        if "," not in line:
            continue
        filename, point_str = line.split(",", 1)
        filename = filename.strip()
        if not filename:
            continue
        entries.append((filename, int(point_str.strip())))
    return entries


def _j2pro_term(dir_name: str) -> str:
    """j2pro0410 → 月を取り出して前期/後期を判定する。"""
    m = re.match(r"j2pro(\d{2})\d{2}$", dir_name)
    if not m:
        return ""
    month = int(m.group(1))
    if 4 <= month <= 8:
        return "zenki"
    return "kouki"


def check_assignments(
    user: str,
    question_root: Path,
    submission_base: Path,
    md_dirs: list[Path],
) -> int:
    print(user)

    total = 0
    submitted = 0
    battle_point = 0

    for assignment_dir in sorted(md_dirs):
        dir_name = assignment_dir.name
        md_path = assignment_dir / f"{dir_name}.md"
        if not _is_readable_file(md_path):
            continue
        for filename, point in _parse_md(md_path):
            filepath = submission_base / user / dir_name / filename
            total += 1
            if _is_readable_file(filepath):
                try:
                    mtime = datetime.fromtimestamp(filepath.stat().st_mtime, tz=timezone(timedelta(hours=9))).strftime("%Y-%m-%d %H:%M:%S")
                except OSError:
                    print(f"未提出  : {filename}")
                    continue
                stem = Path(filename).stem
                grade_json = filepath.parent / f"{stem}_grade.json"
                score = None
                if _is_readable_file(grade_json):
                    try:
                        score = json.loads(grade_json.read_text(encoding="utf-8")).get("score", 100)
                    except (OSError, ValueError):
                        score = None  # 読めない・壊れている → 採点情報なし扱い
                if score is not None:
                    if score > 0:
                        print(f"O.K.    : {filename} ({mtime})")
                        submitted += 1
                        battle_point += point * score // 100
                    else:
                        print(f"[error] : {filename} ({mtime})")
                else:
                    print(f"O.K.    : {filename} ({mtime})")
                    submitted += 1
                    battle_point += point
            else:
                print(f"未提出  : {filename}")

    print(f"{submitted}/{total}")
    print(f"Battle Point = {battle_point}")
    return 0


def j2pro_dirs(question_root: Path, term: str) -> list[Path]:
    """前期/後期に対応する j2pro* ディレクトリ一覧を返す。"""
    try:
        candidates = list(question_root.glob("j2pro????"))
    except OSError:
        return []
    return [d for d in candidates if _is_readable_dir(d) and _j2pro_term(d.name) == term]


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

    term = current_term()
    dirs = j2pro_dirs(question_root, term)
    user = getpass.getuser()
    return check_assignments(
        user=user,
        question_root=question_root,
        submission_base=submission_base,
        md_dirs=dirs,
    )


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
