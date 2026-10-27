# Vue template reference

Template: https://github.com/TomGreener91/Vue_Template_Project (public, use `main`).
Stack: Vue 3, Vite, TypeScript (strict), Pinia, Vue Router, Tailwind 4, ESLint, Stylelint, Prettier, Husky + lint-staged, commitlint (conventional commits), semantic-release.
Requires Node 20+ and npm 10+.

## Setup flags (`node .templateScripts/setup.cjs …`)

Every prompt has a flag. A missing flag in a non-interactive shell stops setup with `Non-interactive shell detected. Pass --<flag>=<values> to answer this prompt.`

| Flag | Values | Applies to |
| --- | --- | --- |
| `--type` | `project`, `plugin`, `electron`, `extension` | All |
| `--hosting` | `github-pages`, `firebase`, `azure`, `none` | `project` |
| `--name` | kebab-case name | `plugin` |
| `--plugin-type` | `component-library`, `vue-plugin`, `utils-library`, `vite-plugin` | `plugin` |
| `--docs` | `y`, `n` (VitePress docs site for the plugin) | `plugin` |
| `--add-to-main` | `y`, `n` (register the plugin in `main.ts`) | `component-library`, `vue-plugin` |
| `--cleanup` | `y`, `n`: always `y` | All |
| `--debug` | dry run, no files written | All |

## Choosing the type

| Request says… | Flags |
| --- | --- |
| web app, site, SPA, dashboard (default) | `--type=project --hosting=<none\|github-pages\|firebase\|azure>` |
| component library, UI kit | `--type=plugin --name=<name> --plugin-type=component-library --docs=n --add-to-main=n` |
| Vue plugin (`app.use()`) | `--type=plugin --name=<name> --plugin-type=vue-plugin --docs=n --add-to-main=n` |
| utility / TS library (no Vue) | `--type=plugin --name=<name> --plugin-type=utils-library --docs=n` |
| Vite plugin | `--type=plugin --name=<name> --plugin-type=vite-plugin --docs=n` |
| desktop app, Electron | `--type=electron` |
| Chrome / Firefox / Edge extension | `--type=extension` |

For plugins, `--name` is the plugin package name. Use the project name unless the user gives a separate one.

## What setup generates

- **All types:** `.github/workflows/ci-cd.yml` (GitHub Actions: health check, semantic-release, deploy) plus composite actions in `.github/actions/`. These only run on GitHub.
- **Hosting secrets** the user must add to their pipeline (never write them into files):

  | Hosting | Secrets |
  | --- | --- |
  | Firebase | `FIREBASE_SERVICE_ACCOUNT`, `FIREBASE_PROJECT_ID` |
  | Azure Static Web Apps | `AZURE_STATIC_WEB_APPS_API_TOKEN` |
  | GitHub Pages | none (enable Pages in repo settings) |

- **Web app:** replaces `README.md` with a short web-app README (personalise it).
- **Plugin:** a workspace package folder, optional `docs/` (VitePress), an npm publishing pipeline.
- **Electron / extension:** their own source folders and a release pipeline.

## Scripts in the generated project

| Script | Use |
| --- | --- |
| `npm run dev` | dev server |
| `npm run build` | type-check + production build |
| `npm run lint` / `lint:fix` | ESLint, Stylelint, Prettier, vue-tsc |
| `npm run health-check` | writes `health-report.md`/`.json` (git-ignored); fails below grade C |
| `npm run deps:all` | audit + outdated |

## Known quirks

- A fresh scaffold usually gets health grade **C**, because of `npm audit` and `npm outdated` warnings in the template's pinned dependencies. That passes. Report the counts and don't upgrade dependencies unless asked.
- The web-app README mentions `.github/workflows/deploy-webapp.yml`; the actual file is `ci-cd.yml`. Fix that line when personalising the README.
- Husky's `prepare` script needs a git repo, so `git init` must come before `npm install`.
- The project's `AGENTS.md` (imported by `CLAUDE.md` and `GEMINI.md`) tells agents not to run builds or linters unless asked. This skill's verify step is that request, so running them is expected.
