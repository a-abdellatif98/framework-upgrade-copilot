---
description: Plan a framework upgrade for Rails, Laravel or Django one hop at a time, with breaking changes, affected code and a test-gated checklist
argument-hint: [target version, e.g. rails 8.1]
allowed-tools: [Read, Glob, Grep]
---

# Plan a Framework Upgrade

Turn a major version upgrade into a chain of safe hops, following the `plan-upgrade` skill.

## Arguments

The user invoked this command with: $ARGUMENTS

Treat the argument as a framework and target version (for example `rails 8.1`, `laravel 12`, `django 5.2`). If it is empty or has no framework, detect the framework from the project and ask the user for the target version.

## Instructions

1. **Detect the framework and current version** with Glob and Read:
   - Rails: `Gemfile.lock` (`rails (X.Y.Z)`), `.ruby-version`, `config/application.rb` (`config.load_defaults`), `config/initializers/new_framework_defaults_*.rb`
   - Laravel: `composer.lock` (`laravel/framework`), `composer.json`, `bootstrap/app.php` or `app/Http/Kernel.php`
   - Django: `poetry.lock`, `uv.lock`, `requirements*.txt` or `pyproject.toml`, `.python-version`

   Never open `.env`, `.env.*`, `config/database.yml`, `settings.py` `DATABASES`, `config/database.php`, credential files, or anything holding tokens or database URLs.

2. **List the hops** from the current version to the target. If the version is outside the covered range, say so and link the official upgrade guide.

3. **Read the reference** for the framework in `skills/plan-upgrade/references/` (`rails.md`, `laravel.md`, `django.md`): the process section, the language minimums, and one `## Hop` section per hop.

4. **Find affected code.** Grep for each removed or changed API in the hop, and for the third-party packages that pin the framework in the lock file. Record file:line for every hit you saw.

## Output format

### Upgrade plan: `framework current -> target`

**Detected:** framework, current version, language version, target, `load_defaults` gap (Rails) and first-party packages.

**Hops:** the ordered list, each with the language minimum.

**Per hop** (repeat):
- Prerequisites: language and dependency changes to make first
- Checklist from high to low impact, each item with the file:line hits found, or "no hits"
- Config and defaults changes
- Data-affecting risks (sessions, cache, hashing, serialization) and the rollout around them
- Gate: the commands to run, tests passing, deprecation warnings reviewed, deploy

**Blocked by:** dependencies with no release supporting the target, and anything marked "verify" in the reference.

**Hop helper (for the user to run, not you):** `python3 scripts/upgrade_path.py --lockfile Gemfile.lock --target 8.1` (run from the plugin directory) prints the hop list and language minimums.

Do not run anything. Produce the plan, commands and hits only.
