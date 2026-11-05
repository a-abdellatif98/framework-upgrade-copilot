---
name: plan-upgrade
description: This skill should be used when the user wants to upgrade a major framework version, for example "upgrade Rails", "Rails 7 to 8", "bundle update rails", "load_defaults", "upgrade Laravel", "Laravel 11", "composer update laravel/framework", "upgrade Django", "Django 5.2", "upgrade Next.js", "Next.js 15", "next codemod", "upgrade NestJS", "NestJS 11", "LTS upgrade", "breaking changes", "removed APIs", or "deprecation warnings before upgrading". Plans the upgrade one hop at a time for Rails 6.1 to 8.1, Laravel 10 to 13, Django 4.2 to 6.0, Next.js 13 to 16 and NestJS 9 to 12, with a test-gated checklist per hop.
version: 1.1.0
---

# Plan a Framework Upgrade

Major upgrades fail when they skip versions, mix a framework bump with feature work, or start without a green suite. Plan them as a chain of small hops, each ending in passing tests and a deploy.

## Principles

1. **One hop at a time.** Rails minor to minor (6.1 -> 7.0 -> 7.1), Laravel, Next.js and NestJS major to major, Django feature release to feature release (LTS to LTS included). Each hop is its own branch or MR.
2. **Tests first.** The suite must pass on the latest patch of the current version before the first hop. If coverage is thin, add characterization tests for the risky areas first.
3. **Deprecations before versions.** Fix the warnings on the current version, then bump. Warnings from inside third-party gems or packages are not always a problem.
4. **Language runtime first.** If the next hop needs a newer Ruby, PHP, Python or Node.js, raise it as a separate step before the framework bump.
5. **Dependencies next.** Check that every gem, composer package, pip package or npm package that touches the framework supports the target. Replace or upgrade the ones that do not before the hop.
6. **No feature work in a hop.** Keep the diff to what the upgrade requires.

## Workflow

1. **Detect** the framework, current version, language version and target (see "Detecting versions" in the reference). `scripts/upgrade_path.py` reads a lock file (including `package-lock.json`, `pnpm-lock.yaml` and `yarn.lock` for Next.js and NestJS) and prints the hop list with language minimums.
2. **List the hops** from current to target. Ask for the target if it is missing; default to the newest supported version and say so.
3. **For each hop**, read the matching `## Hop` section in the reference and turn it into a checklist ordered from high impact to low: language minimum, dependency changes, config and defaults, removed APIs, behaviour changes.
4. **Find the code affected.** Use Grep for each removed or changed API named in the hop and list file:line hits. Do not claim a hit you did not see.
5. **Gate each hop** on: the suite passing, no new deprecation warnings left unexplained, a staging check, then deploy before starting the next hop.
6. **Report risk** the references flag as data-affecting (session or cookie invalidation, cache format changes, digest or hash changes, serialized data) and how to roll out around it.

## References

- `references/rails.md`: Rails 6.1 to 8.1, Ruby minimums, `app:update`, `load_defaults` and `new_framework_defaults` workflow
- `references/laravel.md`: Laravel 10 to 13, PHP support, per-hop impact lists, skeleton comparison
- `references/django.md`: Django 4.2 LTS to 6.0, Python support, deprecation warnings workflow, per-hop removals
- `references/nextjs.md`: Next.js 13 to 16, Node.js minimums, `@next/codemod` names per hop, async request APIs, Turbopack and caching changes
- `references/nestjs.md`: NestJS 9 to 12, Node.js minimums, Express 5 and Fastify 5 changes, per-hop package migrations

## Rules

- Never read credentials. Do not open `.env`, `config/database.yml`, `config/database.php`, `settings.py` `DATABASES`, npm and yarn configuration files, credential files or anything holding tokens or database URLs. Detect versions from lock and dependency files only.
- Never run the upgrade yourself. Produce the plan, the commands and the file:line hits; the user runs them.
- Facts in the references come from the official guides and carry a check date. Anything marked "verify" must be confirmed against the official guide for the user's exact patch version before it is stated as fact.
- If the current or target version is outside the covered range, say so and point to the official upgrade guide instead of guessing.
- Plan hops in order. Do not merge two hops into one checklist even when the user asks for a jump; explain that the intermediate deprecation warnings are the safety net.
