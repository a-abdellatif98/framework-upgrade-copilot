import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "upgrade_path.py"
spec = importlib.util.spec_from_file_location("upgrade_path", SCRIPT)
upgrade_path = importlib.util.module_from_spec(spec)
spec.loader.exec_module(upgrade_path)


def run(*args):
    return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True)


@pytest.mark.parametrize(
    "framework,current,target,expected",
    [
        ("rails", "6.1.7.8", "7.0", [("6.1", "7.0")]),
        ("rails", "7.0.8", "8.1", [("7.0", "7.1"), ("7.1", "7.2"), ("7.2", "8.0"), ("8.0", "8.1")]),
        ("laravel", "v10.48.1", "12", [("10", "11"), ("11", "12")]),
        ("django", "4.2.16", "5.1", [("4.2", "5.0"), ("5.0", "5.1")]),
    ],
)
def test_path_goes_one_hop_at_a_time(framework, current, target, expected):
    assert upgrade_path.upgrade_path(framework, current, target) == expected


@pytest.mark.parametrize(
    "framework,current,target",
    [("rails", "7.1", "7.1"), ("rails", "8.0", "7.0"), ("rails", "5.2", "7.0"), ("laravel", "10", "99"), ("django", "3.2", "5.2")],
)
def test_path_rejects_same_older_or_unknown(framework, current, target):
    with pytest.raises(ValueError):
        upgrade_path.upgrade_path(framework, current, target)


def test_every_series_has_language_minimum():
    for framework, series in upgrade_path.SERIES.items():
        assert set(series) == set(upgrade_path.LANGUAGE[framework][1])


def test_series_match_reference_hops():
    root = SCRIPT.parent.parent / "skills" / "plan-upgrade" / "references"
    for framework, series in upgrade_path.SERIES.items():
        text = (root / f"{framework}.md").read_text()
        for src, dst in zip(series, series[1:]):
            assert f"## Hop: {framework.capitalize()} {src} -> {dst}" in text


@pytest.mark.parametrize(
    "name,content,expected",
    [
        ("Gemfile.lock", "GEM\n  specs:\n    rails (7.1.3)\n      actioncable (= 7.1.3)\n", ("rails", "7.1.3")),
        ("composer.lock", '{"packages":[{"name": "laravel/framework",\n "version": "v11.44.2"}]}', ("laravel", "11.44.2")),
        ("poetry.lock", '[[package]]\nname = "django"\nversion = "5.0.6"\n', ("django", "5.0.6")),
        ("requirements-dev.txt", "pytest==8\nDjango==4.2.11\n", ("django", "4.2.11")),
    ],
)
def test_read_lockfile(tmp_path, name, content, expected):
    path = tmp_path / name
    path.write_text(content)
    assert upgrade_path.read_lockfile(path) == expected


@pytest.mark.parametrize("name", [".env", ".env.production", "database.yml", "settings.py", "package.json"])
def test_read_lockfile_refuses_secrets_and_unknown_files(tmp_path, name):
    path = tmp_path / name
    path.write_text("SECRET=1")
    with pytest.raises(ValueError):
        upgrade_path.read_lockfile(path)


def test_read_lockfile_without_framework_entry(tmp_path):
    path = tmp_path / "Gemfile.lock"
    path.write_text("GEM\n  specs:\n    rack (3.0.0)\n")
    with pytest.raises(ValueError, match="no rails version"):
        upgrade_path.read_lockfile(path)


def test_cli_prints_hops_with_language_minimum():
    result = run("--framework", "rails", "--current", "7.1.2", "--target", "7.2")
    assert result.returncode == 0
    assert "1. 7.1 -> 7.2   Ruby: 3.1.0+" in result.stdout


def test_cli_reads_lockfile(tmp_path):
    lock = tmp_path / "composer.lock"
    lock.write_text('"name": "laravel/framework",\n"version": "v12.1.0"')
    result = run("--lockfile", str(lock), "--target", "13")
    assert result.returncode == 0
    assert "12 -> 13   PHP: 8.3 to 8.5" in result.stdout


def test_cli_reports_errors_without_traceback():
    result = run("--framework", "rails", "--current", "8.1", "--target", "7.0")
    assert result.returncode == 2
    assert "error:" in result.stderr and "Traceback" not in result.stderr


def test_cli_requires_one_source():
    assert run("--target", "8.1").returncode == 2
    assert run("--framework", "rails", "--target", "8.1").returncode == 2
