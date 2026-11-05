# framework-upgrade-copilot

A plugin that plans major framework upgrades one hop at a time, with the breaking changes, removed APIs, config defaults and language minimums for each hop, and a test-gated checklist.

Covered ranges: Rails 6.1 to 8.1, Laravel 10 to 13, Django 4.2 LTS to 6.0. Facts come from the official upgrade guides and release notes; items that could not be confirmed are marked "verify" in the references.

## What a planned upgrade looks like

- **One hop at a time**: never 6.1 straight to 8.1; each hop is tested and deployed before the next
- **Tests first**: green suite on the latest patch of the current version before starting
- **Deprecations before versions**: warnings fixed on the old version
- **Runtime first**: Ruby, PHP or Python raised in its own step when the next hop needs it
- **Affected code found**: Grep hits (file:line) for every removed or changed API in the hop
- **Data risks called out**: sessions, cache format, digests and serialized data

## Installation

```
/plugin install framework-upgrade-copilot@claude-plugins-official
```

## Usage

### Slash command

```
/plan-upgrade rails 8.1
/plan-upgrade laravel 12
/plan-upgrade django 5.2
```

It reads your lock and dependency files (read-only tools only), detects the current version, and outputs the hop list, per-hop checklist with the code affected, and the gate for each hop.

### Skill

The `plan-upgrade` skill activates when you talk about upgrading Rails, Laravel or Django, on Claude.ai as well as in Claude Code. References:

| Reference | Covers |
|---|---|
| `rails.md` | Ruby minimums, `app:update`, `load_defaults` and `new_framework_defaults`, hops 6.1 to 8.1 |
| `laravel.md` | PHP support, hops 10 to 13, skeleton comparison |
| `django.md` | Python support, deprecation warnings workflow, hops 4.2 to 6.0 |

### Hop planner

```
python3 scripts/upgrade_path.py --lockfile Gemfile.lock --target 8.1
python3 scripts/upgrade_path.py --framework django --current 4.2.16 --target 5.2
```

Reads `Gemfile.lock`, `composer.lock`, `poetry.lock`, `uv.lock` or `requirements*.txt` and prints the hops with the language minimum for each. It refuses `.env`, `database.yml`, `database.php` and `settings.py`.

## Safety

The plugin ships no hooks. The command only has Read, Glob and Grep. Nothing reads `.env`, database URLs or other credentials, and nothing runs the upgrade: you review and run the generated plan yourself.

## Development

```
python3 -m pytest -q tests
python3 -m pyflakes scripts tests
```

## License

MIT
