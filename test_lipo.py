# SPDX-FileCopyrightText: 2026 Takumi Yamawaki
# SPDX-License-Identifier: BSD-3-Clause
"""lipo コマンドのテスト.

単体テスト (セル数判定・残量推定) と, 実際にサブプロセスで起動して
標準入力→標準出力を確認するテストを含む.
"""

import subprocess
import sys  # noqa: F401
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parent / "lipo"

# 拡張子のないコマンドファイルをモジュールとして読み込む
import importlib.util  # noqa: E402
from importlib.machinery import SourceFileLoader  # noqa: E402

_loader = SourceFileLoader("lipo", str(SCRIPT))
_spec = importlib.util.spec_from_loader("lipo", _loader)
lipo = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(lipo)


def run_lipo(stdin_text, *args):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        input=stdin_text, capture_output=True, text=True)


# --- セル数判定 ---

@pytest.mark.parametrize("voltage,cells", [
    (3.7, 1), (4.2, 1),
    (7.4, 2), (8.4, 2),
    (11.1, 3), (12.6, 3),
    (14.8, 4), (16.8, 4),
    (22.2, 6), (25.2, 6),
])
def test_detect_cells(voltage, cells):
    assert lipo.detect_cells(voltage) == cells


def test_detect_cells_rejects_non_positive():
    with pytest.raises(ValueError):
        lipo.detect_cells(0)


# --- 残量推定 ---

@pytest.mark.parametrize("voltage,percent", [
    (4.20, 100.0), (4.00, 80.0), (3.85, 60.0),
    (3.70, 30.0), (3.30, 0.0),
])
def test_estimate_percent_table_points(voltage, percent):
    assert lipo.estimate_percent(voltage) == pytest.approx(percent)


def test_estimate_percent_interpolates():
    # テーブル点 3.70 V (30%) と 3.75 V (45%) の中間は 37.5%
    assert lipo.estimate_percent(3.725) == pytest.approx(37.5)


def test_estimate_percent_clamps():
    assert lipo.estimate_percent(4.50) == 100.0
    assert lipo.estimate_percent(3.00) == 0.0


def test_estimate_percent_monotonic():
    voltages = [3.3 + 0.05 * i for i in range(19)]
    percents = [lipo.estimate_percent(v) for v in voltages]
    assert percents == sorted(percents)


# --- 状態判定 ---

def test_status():
    assert "過放電" in lipo.status_of(3.20)
    assert "過充電" in lipo.status_of(4.30)
    assert "保管" in lipo.status_of(3.83)
    assert lipo.status_of(3.95) == ""


# --- コマンドとして (標準入出力) ---

def test_command_single_line():
    proc = run_lipo("11.1\n")
    assert proc.returncode == 0
    assert "3セル" in proc.stdout
    assert "約30%" in proc.stdout


def test_command_summary_for_multiple_lines():
    proc = run_lipo("11.1\n7.4\n22.95\n")
    assert proc.returncode == 0
    assert "まとめ" in proc.stdout
    assert "3件" in proc.stdout


def test_command_accepts_v_suffix_and_comments():
    proc = run_lipo("# メモ\n11.1V\n\n")
    assert proc.returncode == 0
    assert "3セル" in proc.stdout


def test_command_warns_on_bad_line_but_continues():
    proc = run_lipo("abc\n11.1\n")
    assert proc.returncode == 0
    assert "3セル" in proc.stdout
    assert "abc" in proc.stderr


def test_command_fails_without_valid_input():
    proc = run_lipo("abc\n")
    assert proc.returncode == 1
    assert proc.stdout == ""


def test_command_cells_option_overrides_detection():
    proc = run_lipo("12.6\n", "--cells", "4")
    assert proc.returncode == 0
    assert "4セル" in proc.stdout


def test_command_over_discharge_warning():
    proc = run_lipo("3.2\n")
    assert proc.returncode == 0
    assert "過放電" in proc.stdout
