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
