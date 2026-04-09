from __future__ import annotations

import json
import subprocess
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal


@dataclass
class GradeResult:
    filename: str
    compile: Literal["ok", "error"]
    compile_error: str
    tests_passed: int
    tests_total: int
    partial_score: int | None
    score: int


def _run_tests(exe_path: Path, testcase_dir: Path) -> tuple[int, int]:
    """テストケースを実行して (passed, total) を返す。"""
    if not testcase_dir.is_dir():
        return 0, 0

    passed = 0
    total = 0
    n = 1
    while True:
        in_file = testcase_dir / f"sample-{n}.txt"
        out_file = testcase_dir / f"sample-{n}-out.txt"
        if not in_file.exists() or not out_file.exists():
            break
        total += 1
        try:
            proc = subprocess.run(
                [str(exe_path)],
                input=in_file.read_text(encoding="utf-8"),
                capture_output=True,
                text=True,
                timeout=10,
            )
            expected = out_file.read_text(encoding="utf-8").strip()
            if proc.stdout.strip() == expected:
                passed += 1
        except subprocess.TimeoutExpired:
            pass
        n += 1

    return passed, total


def grade_file(
    source_path: Path,
    question_root: Path,
    assignment_name: str,
) -> GradeResult:
    filename = source_path.name
    stem = source_path.stem

    with tempfile.TemporaryDirectory() as tmpdir:
        exe_path = Path(tmpdir) / "a.out"
        proc = subprocess.run(
            ["gcc", str(source_path), "-o", str(exe_path)],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if proc.returncode != 0:
            return GradeResult(
                filename=filename,
                compile="error",
                compile_error=proc.stderr,
                tests_passed=0,
                tests_total=0,
                partial_score=None,
                score=0,
            )

        testcase_dir = question_root / assignment_name / stem
        tests_passed, tests_total = _run_tests(exe_path, testcase_dir)

    score = (tests_passed * 100 // tests_total) if tests_total > 0 else 0
    return GradeResult(
        filename=filename,
        compile="ok",
        compile_error="",
        tests_passed=tests_passed,
        tests_total=tests_total,
        partial_score=None,
        score=score,
    )
