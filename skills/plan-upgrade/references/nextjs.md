# Next.js upgrade hops

Facts below come from the official Next.js upgrade guides, the codemods page, the support policy and the Next.js 15 release post, checked in November 2026. Anything marked "verify" was not confirmed there; check it before acting on it.

## Detecting versions

- Next.js: in order, `package-lock.json` (`node_modules/next` then `version`), `pnpm-lock.yaml` (`next@X.Y.Z`), `yarn.lock` (`next@...:` then `version`), then `package.json` for the range. Lock files only; `scripts/upgrade_path.py --lockfile` reads the first three.
- Router: `app/` means the App Router, `pages/` the Pages Router. Many apps have both; plan for each.
- React: `react` and `react-dom` in the lock file. Next.js 15 needs React 19 for the App Router; the Pages Router also runs on React 18 in 15 (release post).
- Node: `.nvmrc`, `.node-version`, `.tool-versions`, `engines` in `package.json`, Dockerfile base images, CI config.
- Bundler: `--turbopack` or `--turbo` in `package.json` scripts and a `webpack` function in `next.config.*`.

## Process for every hop

From https://nextjs.org/docs/app/guides/upgrading:

1. Read the version guide for the hop and the codemod list for that release.
2. Upgrade one major at a time (13 -> 14 -> 15 -> 16), on the latest patch of each.
3. Run the automated upgrade for the hop: `npx @next/codemod upgrade <revision>` where the revision is `patch`, `minor`, `major`, a dist tag such as `latest` or an exact version such as `15.0.0`. The official 15 and 16 guides write it as `npx @next/codemod@canary upgrade latest`. It updates Next.js, React and React DOM and offers the codemods. Pass the hop's major (the docs show `npx @next/codemod upgrade 16`) so it stops at the hop, and review the diff before committing.
4. Run individual codemods as `npx @next/codemod <transform> <path>`; `--dry` makes no edits and `--print` shows the changed output.
5. If `npm install` fails on peer dependencies after React moves, the guides document `--skip-react-upgrade` and `--skip-eslint-upgrade` on the upgrade codemod to keep those packages as they were.
6. Run the build, the type check and the tests, then check the dev server for deprecation warnings. Deploy before starting the next hop.

The codemod CLI also has an agent mode: `npx next@canary upgrade --agent=latest` (guide for 16). This plugin does not run it; mention it as an option.

## Node.js and platform support

| Next.js | Node.js minimum | Notes |
|---|---|---|
| 13 | 16.14 (verify: inferred from the 14 guide, "bumped from 16.14 to 18.17") | End of life per the support policy |
| 14 | 18.17 | End of life per the support policy |
| 15 | 18.18.0 (release post) | Maintenance LTS, security releases through Jan. 31, 2027 |
| 16 | 20.9.0 (LTS) | Active LTS; also TypeScript 5.1.0+, Chrome/Edge/Firefox 111+, Safari 16.4+ |

Source for status: https://nextjs.org/support-policy (16.x Active LTS, 15.x Maintenance LTS, 14.x and older EOL). Projects on 13 or 14 should plan to reach 16.

## Hop: Next.js 13 -> 14

Source: https://nextjs.org/docs/app/guides/upgrading/version-14

Node.js: 18.17 or newer (16.x reached end of life).

Install (guide): `npm i next@next-14 react@18 react-dom@18 && npm i eslint-config-next@next-14 -D`, and update `@types/react` and `@types/react-dom` for TypeScript.

Changes:
- `next export` is removed. Use `output: 'export'` in the config and `next build`.
- `ImageResponse` moves from `next/server` to `next/og`.
- `@next/font` is removed in favor of the built-in `next/font`.
- The WASM target for `next-swc` is removed.

Codemods:
- `npx @next/codemod@latest next-og-import .`
- `npx @next/codemod@latest built-in-next-font .`
- `npx @next/codemod@latest metadata-to-viewport-export .` (moves `themeColor`, `viewport` and related metadata to the `viewport` export; listed under 14.0 on the codemods page)

Search patterns:
- `next export`
- `from 'next/server'` next to `ImageResponse`
- `@next/font`
- `themeColor` in `metadata`

## Hop: Next.js 14 -> 15

Source: https://nextjs.org/docs/app/guides/upgrading/version-15 and https://nextjs.org/blog/next-15

Node.js: 18.18.0 or newer (release post). React: 19 minimum for the App Router.

Upgrade: `npx @next/codemod@canary upgrade latest`, or install `next@latest react@latest react-dom@latest eslint-config-next@latest` by hand and upgrade `@types/react` and `@types/react-dom`.

Breaking:
- Async request APIs: `cookies`, `headers`, `draftMode`, `params` (layout, page, route, default, image and icon files) and `searchParams` (page) are asynchronous. Synchronous access still works in 15 with a warning, through `UnsafeUnwrappedCookies`, `UnsafeUnwrappedHeaders` and `UnsafeUnwrappedDraftMode` casts. It is removed in 16, so finish this in 15.
- Caching defaults: `fetch` requests are no longer cached by default (opt in with `cache: 'force-cache'` or `export const fetchCache = 'default-cache'`), `GET` Route Handlers are no longer cached (opt in with `export const dynamic = 'force-static'`), and page segments are no longer reused from the client cache on navigation (restore with `experimental.staleTimes`).
- `runtime = 'experimental-edge'` now errors. Use `'edge'`.
- `@next/font` package removed (if still present from 13).
- `experimental.bundlePagesExternals` is now `bundlePagesRouterDependencies`; `experimental.serverComponentsExternalPackages` is now `serverExternalPackages`.
- `NextRequest` `geo` and `ip` removed; the host provides them.
- Speed Insights auto-instrumentation removed; use the dedicated Vercel package.
- `useFormState` is replaced by `useActionState` (React 19; `useFormState` is deprecated, not removed).
- Release post, other breaking items: `next/image` drops `squoosh` for optional `sharp`, default `Content-Disposition` is `attachment`, `.xml` extension removed from dynamic sitemap routes, `revalidateTag` and `revalidatePath` during render throw, `ssr: false` with `next/dynamic` is disallowed in Server Components, `next/font` drops `font-family` hashing.

Codemods:
- `npx @next/codemod@latest next-async-request-api .` (adds `@next-codemod-error` comments and `UnsafeUnwrapped*` casts where it cannot finish; resolve them all)
- `npx @next/codemod@latest app-dir-runtime-config-experimental-edge .`
- `npx @next/codemod@latest next-request-geo-ip .`
- `npx @next/codemod@latest built-in-next-font .`

Search patterns:
- `cookies()`, `headers()`, `draftMode()` without `await`
- `params` and `searchParams` used without `await` or `use(`
- `experimental-edge`
- `req.geo`, `request.ip`
- `useFormState`
- `staleTimes`, `force-static`, `force-cache` (decide caching explicitly)

Data and rollout risk: the caching default changes alter what is served from cache. Compare response behavior of data-heavy routes on staging before deploy.

## Hop: Next.js 15 -> 16

Source: https://nextjs.org/docs/app/guides/upgrading/version-16

Node.js: 20.9.0 or newer (Node 18 dropped). TypeScript 5.1.0 or newer. Browsers: Chrome 111+, Edge 111+, Firefox 111+, Safari 16.4+. React 19.2 in the App Router.

Upgrade: `npx @next/codemod@canary upgrade latest`. It updates `next.config` for the new `turbopack` option, migrates `next lint` to the ESLint CLI, migrates `middleware` to `proxy`, drops the `unstable_` prefix on stabilized APIs and removes `experimental_ppr`. It does not run every migration: run the async request codemod separately if you still have synchronous access.

Breaking and removed:
- Turbopack is the default for `next dev` and `next build`. A custom `webpack` config makes `next build` fail unless you pass `--webpack` (keep webpack) or `--turbopack` (ignore the webpack config), or port it. `experimental.turbopack` moves to top-level `turbopack`. Sass imports with the `~` prefix do not work in Turbopack.
- Synchronous access to `cookies`, `headers`, `draftMode`, `params` and `searchParams` is removed. The `id` of `generateSitemaps` and the `params` and `id` of the image-generating functions are promises.
- `middleware` is deprecated in favor of `proxy` (file and export names; `skipMiddlewareUrlNormalize` becomes `skipProxyUrlNormalize`). `proxy` runs on the Node.js runtime only; edge runtime users keep `middleware`.
- `next lint` and the `eslint` config option are removed; `@next/eslint-plugin-next` defaults to flat config.
- `revalidateTag` takes a second `cacheLife` profile argument (`revalidateTag('posts', 'max')`); the one-argument form is deprecated and a TypeScript error. `updateTag` and `refresh` are new.
- `cacheLife` and `cacheTag` are stable (drop `unstable_`). PPR flags (`experimental.ppr`, `experimental_ppr`) are removed in favor of `cacheComponents`; `experimental.dynamicIO` and `experimental.useCache` are removed.
- Parallel route slots need an explicit `default.js`; builds fail without it.
- `next/image` defaults: `minimumCacheTTL` 4 hours (was 60 seconds), `16` removed from `imageSizes`, `qualities` limited to `[75]`, local IP optimization blocked (`dangerouslyAllowLocalIP`), `maximumRedirects` 3, and local images with query strings need `images.localPatterns.search`. `next/legacy/image` and `images.domains` are deprecated.
- Removed: AMP support, `serverRuntimeConfig` and `publicRuntimeConfig`, `devIndicators` options `appIsrStatus`, `buildActivity` and `buildActivityPosition`, `unstable_rootParams` (use `next/root-params`), `size` and `First Load JS` in build output.
- `next dev` outputs to `.next/dev`, so `next dev` and `next build` can run at the same time.
- `scroll-behavior: smooth` is no longer overridden during navigation; add `data-scroll-behavior="smooth"` on `<html>` to keep the old behavior.

Codemods (all `npx @next/codemod@latest <name> .` unless noted):
- `next-async-request-api`
- `middleware-to-proxy`
- `remove-unstable-prefix`
- `remove-experimental-ppr`
- `npx @next/codemod@canary next-lint-to-eslint-cli .`

Search patterns:
- `next lint`
- `serverRuntimeConfig`, `publicRuntimeConfig`, `getConfig(`
- `middleware.ts`, `middleware.js`, `export function middleware`
- `revalidateTag(` with one argument
- `unstable_cacheLife`, `unstable_cacheTag`
- `experimental_ppr`, `dynamicIO`, `useCache`
- `webpack(` in `next.config.*`
- `from 'next/amp'`, `useAmp`
- `domains:` in the `images` config
- `@modal`-style parallel route folders without `default.js`

Data and rollout risk: the image cache TTL and quality defaults change CDN and cache behavior; Turbopack changes the bundler for production builds, so check bundle output and any webpack-only plugins on staging first.

## After 16: verify

Codemods listed for 16.3 (`cache-components-instant-false`, `remove-partial-prefetch`) are for adopting Cache Components and Partial Prefetching and are optional. Verify whether a newer major than 16 exists before planning past it; this plugin covers 13 to 16.
