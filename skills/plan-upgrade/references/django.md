# Django upgrade hops

Facts below come from the official release notes and the "How to upgrade Django to a newer version" guide, checked in November 2026. Anything marked "verify" was not confirmed there; check it before acting on it.

## Detecting versions

- Django: in order, `poetry.lock` or `uv.lock` (`name = "django"` then `version = "..."`), `Pipfile.lock` (`"django": {"version": "==..."}`), `requirements*.txt` or `requirements/*.txt` (`Django==...` or `django>=...`), `pyproject.toml` (`dependencies` or `[tool.poetry.dependencies]`), `setup.cfg`.
- Python: `requires-python` in `pyproject.toml`, `.python-version`, `.tool-versions`, `runtime.txt`, `Dockerfile` base images, CI config.
- Database engine: the driver in the dependencies (`psycopg`/`psycopg2` for PostgreSQL, `mysqlclient` for MySQL or MariaDB, `oracledb`/`cx_Oracle` for Oracle). Never open `settings.py` sections or `.env` files that hold credentials; `DATABASES` often reads from secrets.

## Process for every hop

From https://docs.djangoproject.com/en/5.2/howto/upgrade-version/:

1. Read the release notes for each feature release between the current and target versions, and the deprecation timeline.
2. Upgrade one feature release at a time (4.2 -> 5.0 -> 5.1 -> 5.2), using the latest patch of each. This applies to LTS to LTS jumps too.
3. Upgrade Django-related dependencies to versions that support the next release.
4. Resolve deprecation warnings on the current version first: `python -Wa manage.py test`, or `PYTHONWARNINGS=always pytest tests --capture=no` with pytest. Warnings raised from inside third-party packages are not always a problem.
5. Install the new version (`python -m pip install -U Django`, or the equivalent lock file update), run the full test suite with warnings on, fix failures.
6. After deploy, clear the cache if the project uses Django's caching; pickled objects are not guaranteed compatible across versions.

## Python support

| Django | Python |
|---|---|
| 4.2 LTS | 3.8 to 3.12 (verify: 3.12 as of 4.2.8 not confirmed); last series to support 3.8 and 3.9 |
| 5.0 | 3.10, 3.11, 3.12 |
| 5.1 | 3.10 to 3.13 (3.13 as of 5.1.3) |
| 5.2 LTS | 3.10 to 3.14 (3.14 as of 5.2.8) |
| 6.0 | 3.12, 3.13, 3.14 |

5.2 is an LTS with security updates for at least three years. Support for 4.2 ended in April 2026, so 4.2 projects should plan to reach 5.2.

## Hop: Django 4.2 -> 5.0

Source: https://docs.djangoproject.com/en/5.0/releases/5.0/

Python: 3.10 or newer.

Database and library minimums: MySQL 8.0.11+, SQLite 3.27.0+, `cx_Oracle` 8.3+ (and `cx_Oracle` is deprecated in favor of `oracledb` 1.3.2+), `asgiref` 3.7.0+, `selenium` 4.8.0+. GDAL 2.2/2.3 and GEOS 3.6/3.7 support removed.

Changed defaults:
- `USE_TZ` defaults to `True`. Projects that never set it must now set `USE_TZ = False` explicitly to keep the old behavior.
- Forms and formsets render with the div-based template by default.
- PBKDF2 iterations increase from 600,000 to 720,000.
- Sitemaps built outside a request use `https`.

Backwards incompatible:
- `update_or_create()` treats `create_defaults` as a keyword; a model field named `create_defaults` must be looked up as `create_defaults__exact`.
- On MariaDB 10.7+, new `UUIDField` columns are `UUID` instead of `CHAR(32)` (the release notes show a `CHAR(32)` subclass to keep existing columns).
- `ping_google()`, the `ping_google` command and `SitemapNotFound` were removed.
- `AlreadyRegistered` and `NotRegistered` moved from `django.contrib.admin.sites` to `django.contrib.admin.exceptions`.
- SQL queries before the app registry is ready raise `RuntimeWarning`.

Removed (end of deprecation cycle):
- Settings: `USE_L10N`, `USE_DEPRECATED_PYTZ`, `CSRF_COOKIE_MASKED`, the `SERIALIZE` test setting.
- `pytz` time zone support; `django.utils.timezone.utc`; the `is_dst` argument of `make_aware()`, `QuerySet.datetimes()` and `Trunc*`.
- `PickleSerializer` for sessions; `CryptPasswordHasher`.
- `django.utils.baseconv`, `django.utils.datetime_safe`.
- Logging out via `GET` in `LogoutView` and `logout_then_login()`.
- `GeoModelAdmin`, `OSMGeoAdmin`, `OpenLayersWidget`.
- `django/forms/default.html` and `django/forms/formsets/default.html` templates.
- `nulls_first=False` / `nulls_last=False` on `asc()`, `desc()` and `OrderBy`.

Deprecated in 5.0 (removed in 6.0): `DjangoDivFormRenderer`, `Jinja2DivFormRenderer`, `cx_Oracle`, the `http` default scheme of `forms.URLField` (`FORMS_URLFIELD_ASSUME_HTTPS` transitional setting), positional arguments to `BaseConstraint`, `format_html()` without args, `ChoicesMeta`, `Prefetch.get_current_queryset()`, `get_joining_columns()`.

Search patterns:
- `USE_L10N`
- `USE_DEPRECATED_PYTZ`
- `CSRF_COOKIE_MASKED`
- `pytz`
- `timezone.utc` imported from `django.utils`
- `is_dst`
- `PickleSerializer`
- `CryptPasswordHasher`
- `baseconv`, `datetime_safe`
- `LogoutView` and links or forms that log out with GET
- `GeoModelAdmin`, `OSMGeoAdmin`, `OpenLayersWidget`
- `forms/default.html`, `formsets/default.html`
- `nulls_first=False`, `nulls_last=False`
- `ping_google`, `SitemapNotFound`
- `admin.sites import AlreadyRegistered`, `admin.sites import NotRegistered`
- `create_defaults`
- `USE_TZ` (confirm it is set explicitly)
- `"SERIALIZE"` inside `TEST` settings

## Hop: Django 5.0 -> 5.1

Source: https://docs.djangoproject.com/en/5.1/releases/5.1/

Python: 3.10 or newer.

Database and library minimums: PostgreSQL 13+, MariaDB 10.5+, SQLite 3.31.0+, `asgiref` 3.8.1+. PostGIS 2.5, PROJ below 6 and GDAL 2.4 support removed.

Backwards incompatible:
- `FileField` raises `FieldError` when saving a file without a `name`.
- `ImageField.update_dimension_fields(force=True)` is no longer called after saving to storage.
- `delete_selected` creates `LogEntry` rows with `bulk_create()`, so `pre_save`/`post_save` for `LogEntry` are not sent.
- `truncatechars_html` and `truncatewords_html` output may differ slightly.
- The undocumented `django.urls.converters.get_converter()` was removed.

Removed (end of deprecation cycle):
- `Meta.index_together` (use `Meta.indexes`; historical migrations still need care).
- `DEFAULT_FILE_STORAGE` and `STATICFILES_STORAGE` settings (use `STORAGES`); `get_storage_class()`.
- `BaseUserManager.make_random_password()`.
- The `length_is` template filter.
- `SHA1PasswordHasher`, `UnsaltedSHA1PasswordHasher`, `UnsaltedMD5PasswordHasher`.
- `CICharField`, `CIEmailField`, `CITextField` and the `CIText` mixin (except in historical migrations).
- `SimpleTestCase.assertFormsetError()`, `TransactionTestCase.assertQuerysetEqual()`.
- Passing encoded JSON string literals to `JSONField` and its lookups.
- Positional arguments to `Signer` and `TimestampSigner`.
- `map_width` and `map_height` on `BaseGeometryWidget`.

Deprecated in 5.1 (removed in 6.0): positional arguments to `Model.save()` and `Model.asave()`, the `check` keyword of `CheckConstraint` (use `condition`), `ModelAdmin.log_deletion()` and `LogEntryManager.log_action()`, `django.utils.itercompat`, `GeoIP2.coords()` and `GeoIP2.open()`, overriding converters with `register_converter()`, `FileSystemStorage.OS_OPEN_FLAGS`, `FieldCacheMixin.get_cache_name()`.

Search patterns:
- `index_together`
- `DEFAULT_FILE_STORAGE`, `STATICFILES_STORAGE`
- `get_storage_class`
- `make_random_password`
- `length_is`
- `SHA1PasswordHasher`, `UnsaltedMD5PasswordHasher`
- `CICharField`, `CIEmailField`, `CITextField`, `CIText`
- `assertFormsetError`, `assertQuerysetEqual`
- `Signer(` and `TimestampSigner(` with positional arguments
- `map_width`, `map_height`
- `get_converter`

## Hop: Django 5.1 -> 5.2

Source: https://docs.djangoproject.com/en/5.2/releases/5.2/

Python: 3.10 or newer. 5.2 is an LTS.

Database and library minimums: PostgreSQL 14+, `oracledb` 2.3.0+, `gettext` 0.19+. PostGIS 3.0 and GDAL 3.0 support removed.

Changed defaults:
- MySQL connections default to `utf8mb4` instead of `utf8` (`utf8mb3`). Set the charset in the `DATABASES` `OPTIONS` if a legacy database needs `utf8mb3`.
- PBKDF2 iterations increase from 870,000 to 1,000,000.
- The `debug()` context processor is no longer in the default project template (existing settings are not changed).

Backwards incompatible:
- `EmailMultiAlternatives.alternatives` can only be added with `attach_alternative()`.
- `HttpRequest.accepted_types` is sorted by client preference.
- `UniqueConstraint.violation_error_code` and `violation_error_message` are always used when provided.
- `Avg`, `Count`, `Max`, `Min`, `StdDev`, `Sum`, `Variance` raise `TypeError` for the wrong number of arguments.
- `create_user()`, `create_superuser()`, `QuerySet.create()`, `bulk_create()`, `get_or_create()`, `update_or_create()` and their async variants set `alters_data=True`, so templates cannot call them.

No features reach the end of their deprecation cycle in 5.2.

Deprecated in 5.2: the `all` argument of `staticfiles.finders.find()` (use `find_all`), the `request.user` fallback in `login()`/`alogin()` when `user` is `None`, the `ordering` argument of `ArrayAgg`, `JSONBAgg`, `StringAgg` (use `order_by`), `RemoteUserMiddleware` subclasses that override `process_request()` without `aprocess_request()`.

Search patterns:
- `.alternatives` on email messages (assignment or append)
- `accepted_types`
- `violation_error_code`, `violation_error_message`
- `ArrayAgg(`, `JSONBAgg(`, `StringAgg(` with `ordering=`
- `finders.find(` with `all=`
- `login(request, None)` or `login(` without a user
- `RemoteUserMiddleware` subclasses
- `create_user`, `bulk_create`, `get_or_create` called from templates

## Hop: Django 5.2 -> 6.0

Source: https://docs.djangoproject.com/en/6.0/releases/6.0/

Python: 3.12 or newer. Optional dependencies must support Python 3.12 (for example `psycopg` 3.1.12, `psycopg2` 2.9.9, `mysqlclient` 2.2.1, `Pillow` 10.1.0, `redis-py` 5.1.0).

Database and library minimums: MariaDB 10.6+, `asgiref` 3.9.1+. `cx_Oracle` support removed; use `oracledb`.

Changed defaults:
- `DEFAULT_AUTO_FIELD` defaults to `django.db.models.BigAutoField`. Projects that never set it (and silenced check `models.W042`) would get new migrations for every implicit primary key; set `DEFAULT_AUTO_FIELD = "django.db.models.AutoField"` to keep the old type.
- `forms.URLField` assumes `https` when no scheme is given; `FORMS_URLFIELD_ASSUME_HTTPS` was removed.

Backwards incompatible:
- `EmailMessage` and `EmailMultiAlternatives` internals changed; undocumented `mixed_subtype`, `alternative_subtype` and legacy `Charset` `encoding` are not supported. Review custom subclasses.
- The JSON serializer writes a trailing newline.
- `Field.pre_save()` may run more than once per save; keep custom implementations idempotent.
- Custom expressions: the second element returned by `as_sql()` should be a tuple.

Removed (end of deprecation cycle):
- `DjangoDivFormRenderer`, `Jinja2DivFormRenderer`.
- Positional arguments to `Model.save()`, `Model.asave()` and `BaseConstraint`.
- The `check` keyword of `CheckConstraint` (use `condition`).
- `format_html()` without args or kwargs.
- `ChoicesMeta` (use `ChoicesType`).
- `Prefetch.get_current_queryset()`; `get_prefetch_queryset()` on related managers and descriptors.
- `get_joining_columns()` and `get_reverse_joining_columns()` on `ForeignObject`.
- `ModelAdmin.lookup_allowed()` overrides must accept `request`.
- `ModelAdmin.log_deletion()`, `LogEntryManager.log_action()`.
- `django.utils.itercompat`, `GeoIP2.coords()`, `GeoIP2.open()`, `FieldCacheMixin.get_cache_name()`, `FileSystemStorage.OS_OPEN_FLAGS`.
- Overriding existing converters with `register_converter()`.

Search patterns:
- `DEFAULT_AUTO_FIELD` (confirm it is set) and `W042` in `SILENCED_SYSTEM_CHECKS`
- `DjangoDivFormRenderer`, `Jinja2DivFormRenderer`
- `FORMS_URLFIELD_ASSUME_HTTPS`
- `cx_Oracle`
- `CheckConstraint(check=`
- `.save(` with positional arguments such as `save(False` or `save(True`
- `format_html(` called with a single argument
- `ChoicesMeta`
- `get_current_queryset`, `get_prefetch_queryset`
- `get_joining_columns`
- `def lookup_allowed(` without `request`
- `log_deletion(`, `log_action(`
- `itercompat`
- `get_cache_name`
- `OS_OPEN_FLAGS`
- `mixed_subtype`, `alternative_subtype`
- `register_converter(`
