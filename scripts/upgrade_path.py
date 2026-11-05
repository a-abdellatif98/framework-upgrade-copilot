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
    "nextjs": ["13", "14", "15", "16"],
    "nestjs": ["9", "10", "11", "12"],
}
LABEL = {"rails": "Rails", "laravel": "Laravel", "django": "Django", "nextjs": "Next.js", "nestjs": "NestJS"}
LANGUAGE = {
    "rails": ("Ruby", {"6.1": "2.5.0+", "7.0": "2.7.0+", "7.1": "2.7.0+", "7.2": "3.1.0+", "8.0": "3.2.0+", "8.1": "3.2.0+"}),
    "laravel": ("PHP", {"10": "8.1 to 8.3", "11": "8.2 to 8.4", "12": "8.2 to 8.5", "13": "8.3 to 8.5"}),
    "django": ("Python", {"4.2": "3.8 to 3.12", "5.0": "3.10 to 3.12", "5.1": "3.10 to 3.13", "5.2": "3.10 to 3.14", "6.0": "3.12 to 3.14"}),
    "nextjs": ("Node", {"13": "16.14+", "14": "18.17+", "15": "18.18+", "16": "20.9+"}),
    "nestjs": ("Node", {"9": "12+", "10": "16+", "11": "20+", "12": "20.19+"}),
}
DEPTH = {"rails": 2, "laravel": 1, "django": 2, "nextjs": 1, "nestjs": 1}
VERSION = r"(\d+(?:\.\d+)+)"
LOCK_PATTERNS = {
    "Gemfile.lock": [("rails", r"^\s+rails \(" + VERSION + r"[\w.]*\)")],
    "composer.lock": [("laravel", r'"name":\s*"laravel/framework",\s*"version":\s*"v?' + VERSION + '"')],
    "poetry.lock": [("django", r'name = "django"\s+version = "' + VERSION + '"')],
    "uv.lock": [("django", r'name = "django"\s+version = "' + VERSION + '"')],
    "package-lock.json": [
        ("nextjs", r'"(?:node_modules/)?next":\s*\{\s*"version":\s*"' + VERSION),
        ("nestjs", r'"(?:node_modules/)?@nestjs/core":\s*\{\s*"version":\s*"' + VERSION),
    ],
    "pnpm-lock.yaml": [
        ("nextjs", r"^\s*['\"]?/?next[@/]" + VERSION),
        ("nestjs", r"^\s*['\"]?/?@nestjs/core[@/]" + VERSION),
    ],
    "yarn.lock": [
        ("nextjs", r'^"?next@[^\n]*:\n\s+version:? "?' + VERSION),
        ("nestjs", r'^"?@nestjs/core@[^\n]*:\n\s+version:? "?' + VERSION),
    ],
}
REQUIREMENTS = ("django", r"^django(?:\[[^\]]*\])?\s*(?:==|>=|~=)\s*(\d+(?:\.\d+)*)")
SECRET_NAMES = ("database.yml", "database.php", "settings.py", ".npmrc", ".yarnrc", ".yarnrc.yml")


def normalize(framework, version):
    parts = version.lstrip("v").split(".")[: DEPTH[framework]]
    return ".".join(parts)


def upgrade_path(framework, current, target):
    series = SERIES[framework]
    start, end = normalize(framework, current), normalize(framework, target)
    for value in (start, end):
        if value not in series and any(item.startswith(f"{value}.") for item in series):
            raise ValueError(f"{framework} {value} is a bare major; give the minor version, e.g. {value}.0")
        if value not in series:
            raise ValueError(f"{framework} {value} is not covered; supported: {', '.join(series)}")
    first, last = series.index(start), series.index(end)
    if first >= last:
        raise ValueError(f"target {end} must be newer than current {start}")
    return list(zip(series[first:last], series[first + 1 : last + 1]))


def read_lockfile(path, framework=None):
    path = Path(path)
    name = path.name
    if name.startswith(".env") or name in SECRET_NAMES:
        raise ValueError(f"refusing to read {name}: it can hold credentials")
    if name in LOCK_PATTERNS:
        candidates = LOCK_PATTERNS[name]
    elif re.fullmatch(r"requirements.*\.txt", name):
        candidates = [REQUIREMENTS]
    else:
        raise ValueError(f"unsupported file {name}; use Gemfile.lock, composer.lock, poetry.lock, uv.lock, requirements*.txt, package-lock.json, pnpm-lock.yaml or yarn.lock")
    if framework:
        candidates = [item for item in candidates if item[0] == framework]
        if not candidates:
            raise ValueError(f"{name} cannot hold a {framework} version")
    text = path.read_text()
    found = []
    for candidate, pattern in candidates:
        match = re.search(pattern, text, re.MULTILINE | re.IGNORECASE)
        if match:
            found.append((candidate, match.group(1)))
    if not found:
        raise ValueError(f"no {' or '.join(item[0] for item in candidates)} version found in {name}")
    if len(found) > 1:
        raise ValueError(f"{name} holds {' and '.join(item[0] for item in found)}; pick one with --framework")
    return found[0]


def format_path(framework, hops):
    label, versions = LANGUAGE[framework]
    lines = [f"{LABEL[framework]} upgrade path ({len(hops)} hop{'s' if len(hops) != 1 else ''})"]
    for number, (src, dst) in enumerate(hops, 1):
        lines.append(f"  {number}. {src} -> {dst}   {label}: {versions[dst]}")
    lines.append("  Run the tests and deploy after each hop. Details: skills/plan-upgrade/references/")
    return "\n".join(lines)


def parse_args(argv):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", required=True, help="target version, e.g. 8.1, 13, 5.2 or 16")
    parser.add_argument("--lockfile", help="Gemfile.lock, composer.lock, poetry.lock, uv.lock, requirements*.txt, package-lock.json, pnpm-lock.yaml or yarn.lock")
    parser.add_argument("--framework", choices=sorted(SERIES), help="required with --current; with --lockfile, picks one when the file holds several")
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
        framework, current = read_lockfile(args.lockfile, args.framework) if args.lockfile else (args.framework, args.current)
        print(format_path(framework, upgrade_path(framework, current, args.target)))
    except (ValueError, OSError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
