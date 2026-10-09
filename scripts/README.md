# Profile dashboard

Run `python scripts/generate.py` with Python 3.12+. No dependencies required. Optional `GITHUB_TOKEN` increases API limits. Never commit tokens. `--from-snapshot` redraws the saved public aggregate offline; `--date YYYY-MM-DD` selects a reproducible past UTC cutoff.

Edit `profile.json` for owner, exact repository-name exclusions, fork policy, featured projects, and technology colors. Technology labels and links in README are editorial: update those alongside configuration. Astro is confirmed by the portfolio; the rest preserves the original stack. Project descriptions and primary languages are fetched from GitHub.

## Definitions

Technology entries contain `[label, icon_slug, hex_color]`, with an optional fourth field for a distinct output filename. Ubuntu and Ubuntu Server share one icon while generating separate pills.

| Metric | Definition |
| --- | --- |
| Public repos | All account-owned public repositories, including forks and excluded repos. No organizations. |
| Stars | Sum of current stars across included repositories; not unique stargazers. |
| Included repos | Public owned repos after exclusions and default fork filtering. Archived repos count. |
| Languages | Distinct languages with bytes reported in included repositories. |
| Code composition | GitHub language bytes summed across included repos, divided by total bytes. Linguist classification applies. Not proficiency, lines of code, or repo counts. Top six plus Other. |
| Commits | Distinct SHAs GitHub attributes to the account, reachable on included default branches, in the 12 calendar months ending with the current partial month. Attributed merge commits count; duplicate SHAs count once. |
| Monthly commits | UTC committer-date buckets, matching REST date filtering; author identity determines attribution. |
| Active days | Distinct UTC committer dates with a counted commit. |

Commits are not contribution-calendar squares. Other branches, organization/private repositories, deleted history, and unassociated author emails are outside scope. History rewrites can change results. This is reachable history today, not an archive. Public-only collection is enforced even with a broader token. No private opt-in is supported; no commit messages, emails, tokens, or source code are stored.

Repository and commit pagination is followed. Empty-repo HTTP 409 is handled. Transient errors retry; long rate limits fail with a clear message. API failures abort before rendering so old assets remain rather than publishing missing data as zeros. Dates show snapshot freshness. Real zero values appear only after successful API requests.

## Workflow and assets

The workflow runs daily at 05:17 UTC, manually, and on generator/config changes. Built-in `github.token` and `contents: write` suffice; no additional secret is needed. Enable Actions writes in repository settings. Protected branches may require replacing direct pushes with a PR. Scheduled workflows run on the default branch, may be delayed, and can be disabled by GitHub after public-repository inactivity. Push failures are reported; there is no force push.

Identical snapshots produce identical files; only changed assets are committed. Daily as-of date changes are intentional. SVGs embed icons, use system typography, and contain no scripts, foreignObject, remote fonts, or remote images. Markdown pills wrap individually; 360px project cards and full-width charts scale on GitHub. Titles, alt text, and `assets/generated/stats.json` provide text alternatives.

Icons are vendored from [Simple Icons 16.0.0](https://www.npmjs.com/package/simple-icons/v/16.0.0), with its CC0 license in `assets/icons`. Existing VS Code and OpenAI artwork is preserved. Trademark policies still apply. Daily generation does not fetch icons or depend on a CDN.

## Counter

Composition chart colors are keyed by language name using a local snapshot of [GitHub Linguist's language colors](https://github.com/github-linguist/linguist/blob/master/lib/linguist/languages.yml), retrieved 2026-10-09 and stored in `assets/language-colors.json`. Sorting changes do not change a language's color. Other and languages without a defined color use a neutral swatch. Edit this mapping to customize chart colors; all other components retain the dark blue theme. Generation needs no external color lookup.

The only external profile widget is [Komarev](https://github.com/antonkomarev/github-profile-views-counter), a free open-source image counter with configurable label/color and no required visible branding. It is labeled **counter requests**, with no fabricated base offset. An existing username key can include past service events; it is not an official lifetime count or a guaranteed fresh start.

GitHub provides no official lifetime README profile-view count. The service increments on image-proxy requests, not unique human visitors. GitHub caching can suppress events; bots, repeated views, and direct image requests can add events. Availability and retention depend on the external provider. GitHub normally proxies images; direct requests expose ordinary request metadata to the service. No analytics scripts or extra tracking pixels are used. The generator never fetches or snapshots the counter.

A self-hosted alternative would need persistent hosting, an atomic database increment, and an SVG endpoint. Cache-control cannot eliminate GitHub proxy caching or bots. Komarev avoids hosting maintenance at the cost of less visual customization. Remove the README counter image to remove this dependency.

Sources: [language bytes](https://docs.github.com/en/rest/repos/repos#list-repository-languages), [commit API](https://docs.github.com/en/rest/commits/commits#list-commits), [pagination](https://docs.github.com/en/rest/using-the-rest-api/using-pagination-in-the-rest-api), [rate limits](https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api).

Run tests: `python -m unittest discover -s tests -v`.
