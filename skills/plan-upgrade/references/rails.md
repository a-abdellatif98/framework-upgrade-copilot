# Rails upgrade hops

Facts below come from the official upgrading guide and release notes, checked in November 2026. Anything marked "verify" was not confirmed there; check it before acting on it.

## Detecting versions

- Rails: `Gemfile.lock`, the `rails (X.Y.Z)` entry under `specs:` (or `railties (X.Y.Z)` if the app requires individual frameworks).
- Ruby: the `RUBY VERSION` section of `Gemfile.lock`, then `.ruby-version`, `.tool-versions`, or the `ruby` line in `Gemfile`.
- Current defaults: `config.load_defaults X.Y` in `config/application.rb`. It often lags the installed Rails version; note the gap.
- Pending defaults: any `config/initializers/new_framework_defaults_X_Y.rb` left over from an earlier hop.

## Process for every hop

From the general advice section of the upgrading guide:

1. Make sure test coverage is good before starting.
2. Move one minor version at a time, to make use of the deprecation warnings.
3. Go to the latest patch of the current version, fix tests and deprecations, then change the `rails` version in `Gemfile` and run `bundle update rails`.
4. Run `bin/rails app:update`. Review every diff it proposes. It creates `config/initializers/new_framework_defaults_X_Y.rb`.
5. Keep `config.load_defaults` at the old value. Enable the new defaults by uncommenting lines in the new initializer, possibly across several deploys.
6. When every default is on, delete the initializer and set `config.load_defaults` to the new version.
7. Update gems that pin Rails (`bundle outdated` lists them); check each gem's changelog for support of the target version.

## Ruby minimums

From the "Ruby Versions" section of the upgrading guide:

| Rails | Minimum Ruby |
|---|---|
| 6.x | 2.5.0 |
| 7.0, 7.1 | 2.7.0 |
| 7.2 | 3.1.0 |
| 8.0, 8.1 | 3.2.0 |

The 7.0 release notes also say "Ruby 3.0+ preferred".

## Hop: Rails 6.1 -> 7.0

Source: https://guides.rubyonrails.org/upgrading_ruby_on_rails.html#upgrading-from-rails-6-1-to-rails-7-0
Release notes: https://guides.rubyonrails.org/7_0_release_notes.html

Ruby: 2.7.0 or newer.

Breaking changes and config:
- Applications must run in `zeitwerk` mode. Classic mode is gone; follow the Classic to Zeitwerk guide first, on 6.1.
- Delete any `config.autoloader = ...` line; the setter was removed.
- The `ActiveSupport::Dependencies` private API was removed. Use `String#constantize` instead of `ActiveSupport::Dependencies.constantize`, and `Rails.autoloaders.log!` for tracing.
- Autoloading reloadable constants during initialization (outside `to_prepare`) now raises `NameError`.
- `button_to` with a persisted Active Record object now uses PATCH. Pass `method: :post` to keep POST.
- Spring must be at least 3.0.0, and `config.cache_classes` must be `false` in `config/environments/test.rb` when using Spring.
- The `rails` gem no longer depends on `sprockets-rails`. Add `sprockets-rails` to `Gemfile` if the app still uses Sprockets.
- `ActionDispatch::Request#content_type` returns the full header including charset. Use `media_type` for the MIME type alone.
- The key generator digest changed from SHA1 to SHA256. Add a cookie rotator through `config.action_dispatch.cookies_rotations` before enabling it, or users lose sessions.
- `ActiveSupport::Digest` moves to SHA256, so ETags and cache keys change (expect a drop in cache hit rate).
- Cache format 7.0 (`config.active_support.cache_format_version = 7.0`): deploy with the 6.1 format first, since 6.1 cannot read 7.0 entries.
- Active Storage default variant processor becomes `:vips` (`config.active_storage.variant_processor`). Variant options may need changes, and cached variant URLs need invalidating.
- Active Storage video previews need FFmpeg 3.4 or newer.
- `schema.rb` now records the version, e.g. `ActiveRecord::Schema[7.0]`. Run `bin/rails app:update` before the first dump.

Removed APIs (7.0 release notes):
- `ActiveRecord::Base.connection_config`, `ActiveRecord::Base.allow_unsafe_raw_sql`, `ActiveRecord::Base.arel_attribute`, `ActiveRecord::Base#remove_connection`.
- `ActiveRecord::Result#map!` and `#collect!`.
- `database` kwarg of `connected_to`, `:spec_name` option of `configs_for`.
- `ActiveModel::Errors#to_h`, `#slice!`, `#values`, `#keys`, `#to_xml`.
- `ActionMailer::DeliveryJob` and `ActionMailer::Parameterized::DeliveryJob` (use `ActionMailer::MailDeliveryJob`).
- `config.active_support.use_sha1_digests`, `URI.parser`.
- `Rails.config.action_view.raise_on_missing_translations`.

Deprecated in 7.0 (removed later): passing a format to `to_s` on `Date`, `Time`, `Integer` and friends; use `to_fs`.

Search patterns:
- `config.autoloader`
- `ActiveSupport::Dependencies`
- `connection_config`
- `allow_unsafe_raw_sql`
- `arel_attribute`
- `errors.keys`, `errors.values`, `errors.to_h`, `errors.slice!`
- `DeliveryJob`
- `use_sha1_digests`
- `URI.parser`
- `\.to_s\(:\w+` (to_s with a format symbol)
- `request.content_type`
- `button_to` (review each call that passes a model)
- `spec_name:`

## Hop: Rails 7.0 -> 7.1

Source: https://guides.rubyonrails.org/upgrading_ruby_on_rails.html#upgrading-from-rails-7-0-to-rails-7-1
Release notes: https://guides.rubyonrails.org/7_1_release_notes.html

Ruby: 2.7.0 or newer.

Breaking changes and config:
- The development and test secret moved from `tmp/development_secret.txt` to `tmp/local_secret.txt`. Rename the file to keep existing sessions.
- Cache format 7.1 (`config.active_support.cache_format_version = 7.1`): switch in a separate deploy so old servers can still read the cache.
- Autoloaded paths are no longer added to `$LOAD_PATH` (`config.add_autoload_paths_to_load_path = true` restores it, discouraged).
- Use `config.autoload_lib(ignore: ...)` and `config.autoload_lib_once` instead of hand-adding `lib` to autoload paths.
- Controllers inheriting from `ActiveStorage::BaseController` that stream files must `include ActiveStorage::Streaming`.
- `MemCacheStore` and `RedisCacheStore` use connection pooling by default (`pool: false` opts out).
- `SQLite3Adapter` uses strict strings mode (`config.active_record.sqlite3_adapter_strict_strings_by_default = false` disables it).
- `config.i18n.raise_on_missing_translations = true` now raises for every missing `I18n.t` key.
- `bin/rails test` runs `test:prepare` first.
- Named imports from `@rails/ujs` are no longer supported; import the default `Rails` object.
- `Rails.logger` is an `ActiveSupport::BroadcastLogger`. `ActiveSupport::Logger.broadcast` was removed; use `Rails.logger.broadcast_to(logger)`.
- Active Record Encryption hash digest defaults to SHA256. Set `config.active_record.encryption.hash_digest_class` to match existing data, and consider `config.active_record.encryption.support_sha1_for_non_deterministic_encryption`.
- `config.action_dispatch.show_exceptions` takes `:all`, `:rescuable` or `:none` instead of `true`/`false`.
- New apps get a generated Dockerfile; existing apps are not required to adopt it.

Removed APIs (7.1 release notes):
- `ActiveRecord.legacy_connection_handling`, `config.active_record.partial_writes`, `:include_replicas` on `configs_for` (use `:include_hidden`).
- `ActiveSupport::PerThreadRegistry`, `active_support/core_ext/uri`.
- `ActionView::Path`; passing instance variables as locals to partials.
- `poltergeist` and `webkit` system test driver registrations.
- `bin/rails secrets:setup`.
- Active Job `QueAdapter` (the `que` gem's own adapter is the replacement: verify in the que docs).

Deprecated in 7.1 (removed in 7.2): `Rails.application.secrets`, `config.action_mailer.preview_path`, `check_pending!` (use `check_all_pending!`), `deferrable: true` on `add_foreign_key` (use `:immediate`), `fixture_path` (use `fixture_paths`), boolean `show_exceptions`, singleton `ActiveSupport::Deprecation`, `config.active_support.disable_to_s_conversion`, `config.active_support.use_rfc4122_namespaced_uuids`.

Search patterns:
- `development_secret.txt`
- `ActiveSupport::Logger.broadcast`
- `legacy_connection_handling`
- `partial_writes`
- `include_replicas`
- `PerThreadRegistry`
- `core_ext/uri`
- `poltergeist`, `:webkit`
- `from "@rails/ujs"` with braces (named import)
- `show_exceptions = true`, `show_exceptions = false`
- `autoload_paths` together with `lib`
- `ActiveStorage::BaseController`
- `Rails.application.secrets`
- `ActiveSupport::Deprecation.warn`

## Hop: Rails 7.1 -> 7.2

Source: https://guides.rubyonrails.org/upgrading_ruby_on_rails.html#upgrading-from-rails-7-1-to-rails-7-2
Release notes: https://guides.rubyonrails.org/7_2_release_notes.html

Ruby: 3.1.0 or newer.

Breaking changes and config:
- All tests respect `config.active_job.queue_adapter` when set. Tests that relied on `TestAdapter` may fail if the adapter is something other than `:test`.
- `alias_attribute` bypasses custom methods defined on the original attribute. Replace with an explicit method or `alias_method` where the custom reader matters.
- YJIT is enabled by default on Ruby 3.3+ (`Rails.application.config.yjit = false` disables it).
- New apps get `allow_browser` in `ApplicationController`, PWA files in `app/views/pwa`, and Puma defaults to 3 threads instead of 5. Existing apps may adopt these through `bin/rails app:update`.

Removed APIs (7.2 release notes):
- `Rails.application.secrets`, `Rails::Generators::Testing::Behaviour`.
- `ActionDispatch::IllegalStateError`, `AbstractController::Helpers::MissingHelperError`.
- Comparison between `ActionController::Parameters` and `Hash`.
- `config.action_dispatch.return_only_request_media_type_on_content_type`.
- `ActiveRecord::Migration.check_pending`, `ActiveRecord::Base.clear_all_connections!`, `ActiveRecord::Base.flush_idle_connections!`, `ActiveRecord::ActiveJobRequiredError`.
- `deferrable: true` on `add_foreign_key`; `rewhere` passed to `Relation#merge`.
- Rolling back a transaction block exited with `return`, `break` or `throw`.
- `ActiveSupport::Notifications::Event#children` and `#parent_of?`, `config.active_support.disable_to_s_conversion`, `config.active_support.use_rfc4122_namespaced_uuids`, passing `Dalli::Client` to `MemCacheStore`.
- Active Job: the `BigDecimal` primitive serializer, numeric `scheduled_at`, `:exponentially_longer` for `retry_on wait:`.
- `config.action_mailer.preview_path`; `:args` for `assert_enqueued_email_with`.

Deprecated in 7.2: `config.active_record.allow_deprecated_singular_associations_name`, `config.active_record.commit_transaction_on_non_local_return`, `config.action_controller.allow_deprecated_parameters_hash_equality`.

Search patterns:
- `Rails.application.secrets`
- `check_pending`
- `clear_all_connections!`
- `flush_idle_connections!`
- `deferrable: true`
- `exponentially_longer`
- `preview_path =`
- `disable_to_s_conversion`
- `use_rfc4122_namespaced_uuids`
- `return_only_request_media_type_on_content_type`
- `alias_attribute` (review each one with a custom reader)
- `Testing::Behaviour`
- `assert_enqueued_email_with` with `args:`

## Hop: Rails 7.2 -> 8.0

Source: https://guides.rubyonrails.org/upgrading_ruby_on_rails.html#upgrading-from-rails-7-2-to-rails-8-0
Release notes: https://guides.rubyonrails.org/8_0_release_notes.html

Ruby: 3.2.0 or newer.

The upgrading guide has no hop-specific steps for 8.0; it points to the release notes. New apps default to Propshaft, Solid Cache, Solid Queue, Solid Cable, Kamal 2 and Thruster, and there is an authentication generator. Existing apps do not have to adopt any of these.

Removed APIs (8.0 release notes):
- `config.read_encrypted_secrets`; console extension through `Rails::ConsoleMethods`; the `rails/console/app` and `rails/console/helpers` files.
- `config.active_record.commit_transaction_on_non_local_return`, `config.active_record.allow_deprecated_singular_associations_name`, `config.active_record.warn_on_records_fetched_greater_than`, `config.active_record.sqlite3_deprecated_warning`.
- `ActiveRecord::ConnectionAdapters::ConnectionPool#connection` (replacement: verify in the 7.2 or 8.0 API docs).
- Defining `enum` with keyword arguments (`enum status: {...}`); use `enum :status, {...}`.
- Passing a database name to `cache_dump_filename`; setting `ENV["SCHEMA_CACHE"]`.
- `config.action_controller.allow_deprecated_parameters_hash_equality`.
- Passing `nil` to `model:` in `form_with`; passing content to void elements in the `tag` builder.
- `ActiveSupport::ProxyObject`; `attr_internal_naming_format` with an `@` prefix; passing an array of strings to `ActiveSupport::Deprecation#warn`.
- `config.active_job.use_big_decimal_serializer`.

Search patterns:
- `read_encrypted_secrets`
- `Rails::ConsoleMethods`
- `commit_transaction_on_non_local_return`
- `allow_deprecated_singular_associations_name`
- `warn_on_records_fetched_greater_than`
- `sqlite3_deprecated_warning`
- `allow_deprecated_parameters_hash_equality`
- `ProxyObject`
- `use_big_decimal_serializer`
- `SCHEMA_CACHE`
- `enum \w+:` (keyword-style enum)
- `form_with model: nil`
- `connection_pool.connection`

## Hop: Rails 8.0 -> 8.1

Source: https://guides.rubyonrails.org/upgrading_ruby_on_rails.html#upgrading-from-rails-8-0-to-rails-8-1
Release notes: https://guides.rubyonrails.org/8_1_release_notes.html

Ruby: 3.2.0 or newer.

Breaking changes and config:
- `schema.rb` columns are sorted alphabetically. Expect a one-time diff; use `structure.sql` if exact column order matters.

Removed APIs (8.1 release notes):
- `rails/console/methods.rb`, the `bin/rake stats` command and `STATS_DIRECTORIES`.
- Semicolons as a query string separator; skipping leading brackets in parameter names; routing to multiple paths.
- SQLite3 adapter `:retries` option; MySQL `:unsigned_float` and `:unsigned_decimal` column methods.
- The `:azure` Active Storage service.
- Passing a `Time` object to `Time#since`; `Benchmark.ms`; adding `ActiveSupport::TimeWithZone` to `Time` instances.
- `enqueue_after_transaction_commit` values `:never`, `:always`, `:default`; `config.active_job.enqueue_after_transaction_commit`; the built-in `SuckerPunch` adapter.

Deprecated in 8.1: `config.action_dispatch.ignore_leading_brackets`, `ActiveRecord::Base.signed_id_verifier_secret`, `config.active_support.to_time_preserves_timezone`, `String#mb_chars` and `ActiveSupport::Multibyte::Chars`, `ActiveSupport::Configurable`, the built-in `sidekiq` adapter (use the adapter shipped by the `sidekiq` gem), custom Active Job serializers without a public `klass` method.

Search patterns:
- `STATS_DIRECTORIES`
- `rake stats`
- `unsigned_float`, `unsigned_decimal`
- `service: AzureStorage`
- `Benchmark.ms`
- `enqueue_after_transaction_commit`
- `sucker_punch`
- `mb_chars`
- `ActiveSupport::Configurable`
- `to_time_preserves_timezone`
- `signed_id_verifier_secret`

The SQLite `retries:` option lives in `config/database.yml`, which can hold credentials. Do not open it; ask the user to check it.
