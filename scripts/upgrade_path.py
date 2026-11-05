#!/usr/bin/env python3
"""List the one-hop-at-a-time upgrade path between two framework versions."""
import argparse
import re
import sys
from pathlib import Path

SERIES = {
    "rails": ["6.1", "7.0", "7.1", "7.2", "8.0", "8.1"],
    "laravel": ["10", "11", "12", "13"],
    "django": ["4.2", "5.0", "5.1", "5.2", "6.0"],
}
LANGUAGE = {
    "rails": ("Ruby", {"6.1": "2.5.0+", "7.0": "2.7.0+", "7.1": "2.7.0+", "7.2": "3.1.0+", "8.0": "3.2.0+", "8.1": "3.2.0+"}),
    "laravel": ("PHP", {"10": "8.1 to 8.3", "11": "8.2 to 8.4", "12": "8.2 to 8.5", "13": "8.3 to 8.5"}),
    "django": ("Python", {"4.2": "3.8 to 3.12", "5.0": "3.10 to 3.12", "5.1": "3.10 to 3.13", "5.2": "3.10 to 3.14", "6.0": "3.12 to 3.14"}),
}
DEPTH = {"rails": 2, "laravel": 1, "django": 2}
LOCK_PATTERNS = {
    "Gemfile.lock": ("rails", r"^\s+rails \((\d+(?:\.\d+)+)\)"),
    "composer.lock": ("laravel", r'"name":\s*"laravel/framework",\s*"version":\s*"v?(\d+(?:\.\d+)+)"'),
    "poetry.lock": ("django", r'name = "django"\s+version = "(\d+(?:\.\d+)+)"'),
    "uv.lock": ("django", r'name = "django"\s+version = "(\d+(?:\.\d+)+)"'),
}
REQUIREMENTS = ("django", r"^django==(\d+(?:\.\d+)+)")
SECRET_NAMES = ("database.yml", "database.php", "settings.py")


def normalize(framework, version):
    parts = version.lstrip("v").split(".")[: DEPTH[framework]]
    return ".".join(parts)


def upgrade_path(framework, current, target):
    series = SERIES[framework]
    start, end = normalize(framework, current), normalize(framework, target)
    for value in (start, end):
        if value not in series:
            raise ValueError(f"{framework} {value} is not covered; supported: {', '.join(series)}")
    first, last = series.index(start), series.index(end)
    if first >= last:
        raise ValueError(f"target {end} must be newer than current {start}")
    return list(zip(series[first:last], series[first + 1 : last + 1]))


def read_lockfile(path):
    path = Path(path)
    name = path.name
    if name.startswith(".env") or name in SECRET_NAMES:
        raise ValueError(f"refusing to read {name}: it can hold credentials")
    if name in LOCK_PATTERNS:
        framework, pattern = LOCK_PATTERNS[name]
    elif re.fullmatch(r"requirements.*\.txt", name):
        framework, pattern = REQUIREMENTS
    else:
        raise ValueError(f"unsupported file {name}; use Gemfile.lock, composer.lock, poetry.lock, uv.lock or requirements*.txt")
    match = re.search(pattern, path.read_text(), re.MULTILINE | re.IGNORECASE)
    if not match:
        raise ValueError(f"no {framework} version found in {name}")
    return framework, match.group(1)


def format_path(framework, hops):
    label, versions = LANGUAGE[framework]
    lines = [f"{framework} upgrade path ({len(hops)} hop{'s' if len(hops) != 1 else ''})"]
    for number, (src, dst) in enumerate(hops, 1):
        lines.append(f"  {number}. {src} -> {dst}   {label}: {versions[dst]}")
    lines.append("  Run the tests and deploy after each hop. Details: skills/plan-upgrade/references/")
    return "\n".join(lines)


def parse_args(argv):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", required=True, help="target version, e.g. 8.1, 13 or 5.2")
    parser.add_argument("--lockfile", help="Gemfile.lock, composer.lock, poetry.lock, uv.lock or requirements*.txt")
    parser.add_argument("--framework", choices=sorted(SERIES), help="required with --current")
    parser.add_argument("--current", help="current version, e.g. 6.1.7.8")
    args = parser.parse_args(argv)
    if bool(args.lockfile) == bool(args.current):
        parser.error("give exactly one of --lockfile or --framework with --current")
    if args.current and not args.framework:
        parser.error("--current needs --framework")
    return args


def main(argv=None):
    args = parse_args(argv)
    try:
        framework, current = read_lockfile(args.lockfile) if args.lockfile else (args.framework, args.current)
        print(format_path(framework, upgrade_path(framework, current, args.target)))
    except (ValueError, OSError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
