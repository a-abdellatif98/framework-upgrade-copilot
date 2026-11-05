# Laravel upgrade hops

Facts below come from the official upgrade guides and the release notes support table, checked in November 2026. Anything marked "verify" was not confirmed there; check it before acting on it.

## Detecting versions

- Laravel: `composer.lock`, the package entry with `"name": "laravel/framework"` and its `"version"` (e.g. `v11.44.2`). Fall back to the `laravel/framework` constraint in `composer.json`.
- PHP: the `"php"` constraint under `require` in `composer.json`, then `config.platform.php` in `composer.json`, then `platform` in `composer.lock`. Also check `.tool-versions`, `Dockerfile` base images and CI config for the PHP actually used.
- First-party packages: `laravel/sanctum`, `laravel/passport`, `laravel/cashier`, `laravel/telescope`, `laravel/horizon`, `livewire/livewire`, `inertiajs/inertia-laravel` versions in `composer.lock`.
- Skeleton shape: Laravel 10 style apps have `app/Http/Kernel.php` and `app/Console/Kernel.php`; Laravel 11 style apps configure middleware and routing in `bootstrap/app.php`.

## Process for every hop

1. Make sure the test suite passes on the latest patch of the current major.
2. Upgrade one major at a time.
3. Raise PHP first if the next major needs it (see the table).
4. Update `composer.json` constraints listed in the hop, then run `composer update`.
5. Work through the hop's items from High to Low impact, running tests after each group.
6. Compare the `laravel/laravel` skeleton between the two branches on GitHub for optional config changes.

## PHP support

From the support policy table in the release notes (https://laravel.com/docs/12.x/releases):

| Laravel | Supported PHP |
|---|---|
| 10 | 8.1 to 8.3 |
| 11 | 8.2 to 8.4 |
| 12 | 8.2 to 8.5 |
| 13 | 8.3 to 8.5 |

## Hop: Laravel 10 -> 11

Source: https://laravel.com/docs/11.x/upgrade

PHP: 8.2.0 or newer. The HTTP client needs curl 7.34.0 or newer.

Dependencies (`composer.json`):
- `laravel/framework` `^11.0`, `nunomaduro/collision` `^8.1`.
- If installed: `laravel/breeze` `^2.0`, `laravel/cashier` `^15.0`, `laravel/dusk` `^8.0`, `laravel/jetstream` `^5.0`, `laravel/octane` `^2.3`, `laravel/passport` `^12.0`, `laravel/sanctum` `^4.0`, `laravel/scout` `^10.0`, `laravel/spark-stripe` `^5.0`, `laravel/telescope` `^5.0`, `livewire/livewire` `^3.4`, `inertiajs/inertia-laravel` `^1.0`.
- `doctrine/dbal` can be removed; Laravel no longer depends on it.
- Remove `spatie/once` if present; Laravel 11 ships its own `once` function.

Application structure: Laravel 11 has a slimmer skeleton (fewer service providers, middleware and config files, configuration in `bootstrap/app.php`). The guide does not recommend migrating an existing Laravel 10 structure; Laravel 11 supports the old structure. Treat the slim skeleton as optional.

High impact:
- Modifying a column with `->change()` drops every modifier not restated. Restate `unsigned()`, `default()`, `comment()`, `nullable()` and so on in every `change()` call.
- `double` creates a `DOUBLE` without total and places; `float` takes an optional `precision`. `unsignedDecimal`, `unsignedDouble` and `unsignedFloat` were removed; chain `->unsigned()` instead.
- SQLite 3.26.0 or newer is required.
- Sanctum 4, Passport 12, Cashier Stripe 15, Spark Stripe 5 and Telescope 5 no longer load their migrations automatically. Publish them: `php artisan vendor:publish --tag=sanctum-migrations` (and `passport-migrations`, `cashier-migrations`, `spark-migrations`, `telescope-migrations`).
- Sanctum: update the `middleware` array in `config/sanctum.php` to the new `authenticate_session`, `encrypt_cookies` and `validate_csrf_token` keys shown in the guide.
- Passport: the password grant is disabled by default; call `Passport::enablePasswordGrant()` in `AppServiceProvider::boot` if used.

Medium impact:
- Carbon 3 is supported alongside Carbon 2. In Carbon 3, `diffIn*` methods return floats and can be negative.
- Rate limiting is per second: `Limit`, `GlobalLimit`, `ThrottlesExceptions` and `ThrottlesExceptionsWithRedis` take seconds, and `Limit::$decayMinutes` became `decaySeconds`.

Low impact:
- Passwords are rehashed on login when the work factor changes. If the hash column has another name, declare it on the user model (see "Password Rehashing" in the 11.x upgrade guide), or set `'rehash_on_login' => false` in `config/hashing.php`.
- Doctrine DBAL methods removed, including `Connection::getDoctrineConnection()`, `getDoctrineSchemaManager()`, `getDoctrineColumn()`, `registerDoctrineType()`, and `Schema\Builder::useNativeSchemaOperationsIfPossible()`. Use `Schema::getTables()`, `getColumns()`, `getIndexes()`, `getForeignKeys()`.
- Spatial column types `point`, `lineString`, `polygon`, `geometryCollection`, `multiPoint`, `multiLineString`, `multiPolygon`, `multiPolygonZ` were removed; use `geometry` or `geography`.
- The base model defines a `casts()` method, so a relationship named `casts` conflicts.
- `UserProvider` contract gains `rehashPasswordIfRequired`; `Authenticatable` gains a method returning the hash column name. Custom implementations must add both.

Very low impact:
- `Schema::getAllTables()`, `getAllViews()`, `getAllTypes()` removed (use `getTables()`, `getViews()`, `getTypes()`).
- `AuthenticationException::redirectTo()` needs the `Request`.
- Cache key prefixes for Redis, Memcached and DynamoDB no longer get an automatic `:` suffix.
- A dedicated `mariadb` driver exists; its `uuid()` creates native UUID columns.

Search patterns:
- `->change()` (review modifiers on each)
- `unsignedDecimal`, `unsignedDouble`, `unsignedFloat`
- `getDoctrine`
- `registerDoctrineType`
- `useNativeSchemaOperationsIfPossible`
- `getAllTables`, `getAllViews`, `getAllTypes`
- `->point(`, `->lineString(`, `->polygon(`, `->multiPolygon(`, `->geometryCollection(`
- `decayMinutes`
- `new Limit(`, `new GlobalLimit(`, `ThrottlesExceptions`
- `diffIn` (Carbon 3 return type)
- `function casts(` on a model that also has a `casts` relationship
- `spatie/once`, `doctrine/dbal` in `composer.json`
- `redirectTo(` on `AuthenticationException`

## Hop: Laravel 11 -> 12

Source: https://laravel.com/docs/12.x/upgrade

PHP: 8.2 to 8.5 per the support table; the upgrade guide itself states no new minimum.

Dependencies (`composer.json`): `laravel/framework` `^12.0`, `phpunit/phpunit` `^11.0`, `pestphp/pest` `^3.0`. Update the Laravel installer (`composer global update laravel/installer`).

Medium impact:
- `HasUuids` now generates UUIDv7. Use `HasVersion4Uuids` (aliased as `HasUuids`) to keep ordered UUIDv4. `HasVersion7Uuids` was removed.

Low impact:
- Carbon 2 support removed; Carbon 3 is required.
- The `image` validation rule excludes SVG by default; use `image:allow_svg` or `File::image(allowSvg: true)`.
- If no `local` disk is defined, its root defaults to `storage/app/private` instead of `storage/app`.
- `$request->mergeIfMissing()` merges dot-notation keys into nested arrays.
- `Concurrency::run` with an associative array returns results under their keys.
- The container respects property default values when resolving classes (`?Carbon $date = null` stays `null`).
- `Schema::getTables()`, `getViews()`, `getTypes()` include all schemas by default; `Schema::getTableListing()` returns schema-qualified names unless `schemaQualified: false`.
- Duplicate route names: uncached routing now matches the first registered route.

Very low impact:
- `DatabaseTokenRepository` takes `$expires` in seconds.
- `Blueprint` and `Grammar` constructors need a `Connection`; `Grammar::setConnection()` was removed.

Search patterns:
- `HasUuids`
- `HasVersion7Uuids`
- `nesbot/carbon` constraint `^2` in `composer.json`
- `'image'` and `image|` validation rules, `File::image(`
- `Storage::disk('local')` and `Storage::` calls without a disk when `config/filesystems.php` lacks a `local` disk
- `mergeIfMissing`
- `Concurrency::run`
- `getTableListing`
- `DatabaseTokenRepository`
- `setConnection(` on a grammar
- `new Blueprint(`

## Hop: Laravel 12 -> 13

Source: https://laravel.com/docs/13.x/upgrade

PHP: 8.3 to 8.5 per the support table (https://laravel.com/docs/12.x/releases). Laravel 13 depends on `symfony/polyfill-php85`.

Dependencies (`composer.json`): `laravel/framework` `^13.0`, `laravel/tinker` `^3.0`, `phpunit/phpunit` `^12.0`, `pestphp/pest` `^4.0`, and `laravel/boost` `^2.0` if installed.

High impact:
- `VerifyCsrfToken` is renamed `PreventRequestForgery` and also checks request origin with the `Sec-Fetch-Site` header. `VerifyCsrfToken` and `ValidateCsrfToken` remain as deprecated aliases.

Medium impact:
- The default cache config adds `'serializable_classes' => false`. Apps that cache objects must list those classes.
- `upsert` on MySQL or MariaDB throws `InvalidArgumentException` when `uniqueBy` is empty.

Low impact:
- Default cache prefixes and session cookie names change; set `CACHE_PREFIX`, `REDIS_PREFIX` and `SESSION_COOKIE` to keep the old values (otherwise caches miss and users are logged out).
- Domain routes are matched before non-domain routes.
- `JobAttempted::$exceptionOccurred` is replaced by `$exception`; `QueueBusy::$connection` becomes `$connectionName`.
- `Manager::extend` closures are bound to the manager.
- MySQL `DELETE` with `JOIN`, `ORDER BY` and `LIMIT` compiles those clauses and may throw on engines without support.
- Pagination views `pagination::default` and `pagination::simple-default` become `pagination::bootstrap-3` and `pagination::simple-bootstrap-3`.
- Inferred pivot table names for custom polymorphic pivot classes are pluralized.
- Changing session `serialization` from `php` to `json` invalidates all sessions.
- On PHP below 8.5 the polyfill defines global `array_first()` and `array_last()`, which can clash with app helpers of the same name.

Very low impact: custom cache stores need `touch()`, custom queue drivers need `pendingSize`, `delayedSize`, `reservedSize` and `creationTimeOfOldestPendingJob`, and creating a model while it boots throws `LogicException`.

Search patterns:
- `VerifyCsrfToken`, `ValidateCsrfToken`
- `->upsert(` with an empty unique-by argument
- `exceptionOccurred`
- `QueueBusy`
- `pagination::default`, `pagination::simple-default`
- `function array_first`, `function array_last`
- `->extend(` on managers using `$this`
- `MorphPivot` subclasses without `$table`
- `serialization` in `config/session.php`
