# NestJS upgrade hops

Facts below come from the official NestJS migration guides (current page for 11 to 12, versioned pages for 10 to 11 and 9 to 10), checked in November 2026. Anything marked "verify" was not confirmed there; check it before acting on it.

## Detecting versions

- NestJS: in order, `package-lock.json` (`node_modules/@nestjs/core` then `version`), `pnpm-lock.yaml` (`@nestjs/core@X.Y.Z`), `yarn.lock` (`"@nestjs/core@...":` then `version`), then `package.json`. Lock files only; `scripts/upgrade_path.py --lockfile` reads the first three. `@nestjs/core` is the version that defines the major.
- Companion packages move on their own versions (`@nestjs/config`, `@nestjs/cache-manager`, `@nestjs/terminus`, `@nestjs/swagger`, `@nestjs/graphql`, `@nestjs/schematics`, `@nestjs/cli`). Read each one's version in the same lock file.
- HTTP adapter: `@nestjs/platform-express` or `@nestjs/platform-fastify`. The adapter decides which breaking changes apply.
- Test runner and build: `jest` or other config in `package.json`, `nest-cli.json` (look for `webpack` options), `tsconfig*.json`.
- Node: `.nvmrc`, `.node-version`, `.tool-versions`, `engines` in `package.json`, Dockerfile base images, CI config.

## Process for every hop

From https://docs.nestjs.com/migration-guide (current) and https://docs.nestjs.com/v11/migration-guide, https://docs.nestjs.com/v10/migration-guide (older hops):

1. Read the migration guide for the hop. The unversioned page covers only the newest hop; use the versioned pages for older ones.
2. Upgrade one major at a time (9 -> 10 -> 11 -> 12), on the latest patch of each.
3. Upgrade every `@nestjs/*` package that your app uses to the line that matches the hop, including the CLI and schematics. The 12 guide mentions `nest upgrade` (verify what it changes and run it with its dry-run option first, if the CLI offers one).
4. Raise Node first if the hop needs it, as its own step.
5. Run the build, the type check, the unit and e2e tests, then boot the app and hit the routes that use wildcards, middleware, guards and caching.
6. Deploy before starting the next hop.

Support window: the release-schedule FAQ page did not state a support policy when checked. Verify which majors still receive fixes on the official site before telling a team that a line is unsupported.

## Node.js support

| NestJS | Node.js | Source |
|---|---|---|
| 9 | 12 and newer (verify: inferred from the 10 guide, which drops Node 12) | 10 guide |
| 10 | 16 or higher | 10 guide |
| 11 | 20 or higher (16 and 18 dropped) | 11 guide |
| 12 | 20.19+ or 22.12+ (21.x unsupported); `@nestjs/schematics` needs 22.22.3+, 24.15+ or 26+; Jest needs 24.9+ to load the ESM-only packages | 12 guide |

## Hop: NestJS 9 -> 10

Source: https://docs.nestjs.com/v10/migration-guide

Node.js: 16 or higher.

Breaking:
- `CacheModule` is removed from `@nestjs/common`. Install the standalone `@nestjs/cache-manager` and import from it.
- Log levels: the `verbose` and `debug` values are swapped (`debug` is 1, `verbose` is 0). Check custom loggers and any code that compares numeric levels.
- All deprecated methods and modules are removed. Fix the deprecation notices in 9 first.
- The `@nestjs/swagger` and `@nestjs/graphql` CLI plugins require TypeScript 4.8 or newer.
- Official packages compile to `ES2021`; Node 12 is not supported.

Search patterns:
- `CacheModule` imported from `@nestjs/common`
- `CACHE_MANAGER` imports
- `LogLevel` comparisons and custom `LoggerService` implementations
- `typescript` version in `package.json`

## Hop: NestJS 10 -> 11

Source: https://docs.nestjs.com/v11/migration-guide

Node.js: 20 or higher.

Breaking:
- Express 5 is the default in `@nestjs/platform-express`. Wildcards must be named (`/*splat` or `/{*splat}`, not `/*`), `?` optional syntax is unsupported (use braces, for example `/:file{.:ext}`), regexp characters are unsupported, and the characters `(()[]?+!)` are reserved and need `\` escaping.
- Query parsing: with Express 5 the `simple` parser is the default. Restore nested parsing with `app.set('query parser', 'extended')`.
- Fastify 5 in `@nestjs/platform-fastify`: Fastify 5 breaking changes apply. CORS allows only CORS-safelisted methods by default; pass `methods` to `enableCors` for `PUT`, `PATCH` or `DELETE`. Middleware paths use the new path-to-regexp, so `(.*)` is unsupported; use `*splat`.
- Dynamic modules are no longer deduplicated by a generated hash; object references decide equivalence. This affects tests that select dynamic modules (guide options: `moduleIdGeneratorAlgorithm: 'deep-hash'`, `module.select(ParentModule).get(Target)`, `module.get(Target, { each: true })`).
- `Reflector`: `getAllAndMerge` returns an object instead of a one-element array for single object metadata, and `getAllAndOverride` returns `T | undefined`.
- Termination hooks (`OnModuleDestroy`, `BeforeApplicationShutdown`, `OnApplicationShutdown`) run in the reverse of initialization order.
- Middleware registered by global modules runs first.
- `@nestjs/cache-manager` moves to Keyv: the `store` option becomes `stores` (for example `new KeyvRedis(...)` from `@keyv/redis`), and cached data is stored as `{ value, expires }`.
- `@nestjs/config` 4.0.0: `ConfigService#get` lookup order changed (internal config before environment variables), `ignoreEnvVars` is deprecated in favor of `validatePredefined`, and `skipProcessEnv` is new.
- Terminus: `HealthIndicatorService` is the new API; `HealthIndicator` and `HealthCheckError` are deprecated.

Search patterns:
- `forRoutes('*')`, `@Get('*')`, `'/*'` and any route or middleware path with `?`, `(`, `+` or `(.*)`
- `req.query` consumers that rely on nested objects
- `enableCors(` and fastify `cors` options
- `getAllAndMerge`, `getAllAndOverride`
- `store:` in `CacheModule.register`
- `ConfigService` use with `ignoreEnvVars`
- `HealthIndicator`, `HealthCheckError`

Data and rollout risk: cached values written by the old store are not read in the new `{ value, expires }` shape, so values written by the old store may not be readable. Plan for a cold cache after deploy and flush or version the keys on purpose (verify the behavior for your cache backend).

## Hop: NestJS 11 -> 12

Source: https://docs.nestjs.com/migration-guide

Node.js: 20.19+, or 22.12+ on the 22.x line. Node 21 is unsupported. Jest needs Node 24.9+ to load the ESM-only packages (otherwise `ERR_REQUIRE_ASYNC_MODULE`).

Breaking or required:
- Core packages ship as ESM. CommonJS apps consume them through `require(esm)`; migrating your own code to ESM is not required (verify against your toolchain).
- NATS transport moves to v3: replace `nats` with `@nats-io/transport-node` (and `@nats-io/nats-core` for helpers). `StringCodec` and `JSONCodec` are removed, and custom deserializers receive the full message object (read the payload with `msg.json()`).
- GraphQL: `subscriptions-transport-ws` is removed; use `subscriptions: { 'graphql-ws': true }`. GraphiQL is the default IDE and takes a `graphiql` options object instead of `graphiql: true`.
- `@nestjs/config`: `validationSchema` accepts Standard Schema, Joi schemas need Joi 18+, and Joi-specific `validationOptions` move under `validationOptions.libraryOptions`.
- Terminus: legacy `HealthIndicator` and `HealthCheckError` are removed; use `HealthIndicatorService`. The `timeout` option on database, microservice and gRPC indicators is deprecated in favor of `.withTimeout()`.
- Lifecycle hooks (`onModuleInit`, `onApplicationBootstrap`, shutdown hooks) run by component hierarchy level, so execution order can change.
- `@Optional()` is not inherited by a redeclared constructor; Nest throws `UnknownDependenciesException` where 11 returned `undefined`. Redeclare the marker.
- Webpack options `--webpack` and `--webpackPath` (and `webpack` and `webpackConfigPath` in `nest-cli.json`) are deprecated; the guide points to `--builder rspack`.
- The Angular schematic is removed. Pipe transform signatures are refined (`ArgumentMetadata` takes a generic parameter).
- `ConsoleLogger`: trailing plain objects become structured params by default; set `structuredParams: false` to keep the old output.

Opt-in additions (not breaking): `schema` option on `@Body()`, `@Query()`, `@Param()` and `@RawBody()`, `StandardSchemaValidationPipe`, `routeConflictPolicy`, `routeResolutionStrategy`, `errorCode` on `HttpExceptionOptions`, the `@nestjs/observe` package, and the `ValidationPipe` `errorFormat` option.

Search patterns:
- `from 'nats'`, `StringCodec`, `JSONCodec`
- `subscriptions-transport-ws`, `graphiql: true`
- `validationSchema`, `validationOptions`
- `HealthIndicator`, `HealthCheckError`, `timeout:` on health indicators
- constructors that redeclare parameters of a base class that uses `@Optional()`
- `onModuleInit`, `onApplicationBootstrap` with ordering assumptions
- `webpack` in `nest-cli.json`
- `jest` config and the Node version CI uses

Data and rollout risk: logging output changes with `ConsoleLogger` structured params; check log parsers and alerts on staging.
