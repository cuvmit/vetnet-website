# VETNET website

The website for **VETNET**, an open initiative connecting veterinary medicine and data science. VETNET is building live benchmarks for AI in veterinary medicine ("any animal, any disease, any responsible task") and is sponsored by the Cornell AI Initiative.

This repository holds the source of the site. It is a static site built with [Pelican](https://getpelican.com), which turns Markdown files, YAML data and templates into plain HTML.

Live site: _coming soon_

> **Status: first draft.** All pages exist and the site builds, but sign-in, forms and downloads are **visual only** (nothing is sent anywhere), and photos, logos and some copy are placeholders. See [Content to fill in](#content-to-fill-in).

## Quick start

You need:

- [Git](https://git-scm.com/downloads)
- [uv](https://docs.astral.sh/uv/getting-started/installation/), which installs the right Python version and all dependencies for you
- [Node.js](https://nodejs.org/) and [Yarn](https://classic.yarnpkg.com/), which run the project commands
- [AWS CLI](https://aws.amazon.com/cli/), only needed to deploy

Then:

```bash
git clone git@github.com:cuvmit/vetnet-website.git
cd vetnet-website
yarn install
yarn start
```

Open <http://localhost:8000>. Leave `yarn start` running: when you save a file, the site rebuilds automatically (refresh the browser to see the change). Press `Ctrl+C` to stop it.

No Yarn? Run the commands behind each script directly:

```bash
uv sync
uv run pelican content -s pelicanconf.py --autoreload --listen
```

(`yarn build`, `yarn test` and the deploy scripts are defined in `package.json`.)

## Common commands

| Command | What it does |
|---|---|
| `yarn install` | Installs dependencies (creates `.venv/` via `uv sync`) |
| `yarn start` | Builds, serves at <http://localhost:8000>, and rebuilds when files change |
| `yarn build` | Builds with production settings (full `https://` URLs) into `output/` |
| `yarn test` | Builds with development settings, then checks every link, page title, placeholder and count in `output/` |
| `yarn clean` | Deletes `output/` and `cache/` |
| `yarn deploy:sb` | Builds, then syncs `output/` to the `vetnet-sb.vmit.cucloud.net` S3 bucket |
| `yarn deploy:prod` | Builds, then syncs `output/` to the `vetnet-prod.vmit.cucloud.net` S3 bucket |

Run `yarn test` before you open a pull request. It fails with a list of problems if a link is broken, a page is missing a title, or the counts on the home page don't match the data.

## Deploying

Deploys upload the built site to S3 with the AWS CLI, using the AWS credentials in your terminal.

| Environment | Command | S3 bucket | Site URL used in links |
|---|---|---|---|
| Sandbox | `yarn deploy:sb` | `vetnet-sb.vmit.cucloud.net` | `https://vetnet-sb.vmit.cucloud.net` |
| Production | `yarn deploy:prod` | `vetnet-prod.vmit.cucloud.net` | `https://vetnet.vmit.cucloud.net` (set in `yarn deploy:prod`; switch to `https://vetnet.org` once that domain points at CloudFront) |

Steps:

```bash
aws sso login                  # if your credentials have expired
aws sts get-caller-identity    # optional: confirm you are in the right account
yarn test                      # optional: check the site first
yarn deploy:sb                 # deploy to the sandbox and look it over
yarn deploy:prod               # then deploy to production
```

Each deploy script rebuilds the site first, so you don't need to run `yarn build` yourself.

Things to know:

- The upload uses `aws s3 sync --delete`, so files in the bucket that are not in `output/` are removed.
- `publishconf.py` reads the `SITEURL` environment variable (default `https://vetnet.org`). `yarn deploy:sb` sets it so sandbox pages link to the sandbox rather than production.
- After the upload, each deploy runs `aws cloudfront create-invalidation --paths '/*'` against that environment's CloudFront distribution (sandbox `E2VKLN32FGP0K3`, production `E191HYOQDGRN3L`), so changes show up without waiting for the cache to expire.

## Pages

| Page | URL | Where its content lives |
|---|---|---|
| Home | `/` | `templates/home.html` + `data/` (counts, partners) + featured news |
| About | `/about/` | `templates/about.html`, `data/timeline.yml`, `data/faq.yml` |
| People | `/people/` | `data/people.yml`, `data/teams.yml` |
| Research | `/research/` | `templates/research.html`, `data/publications.yml` |
| Databases | `/databases/` | `data/datasets.yml` |
| News & Events | `/news/` | `content/news/*.md` |
| Join Us | `/join/` | `data/join_options.yml` |
| Sponsors | `/sponsors/` | `templates/sponsors.html` |
| Portal, For Members | `/portal/`, `/members/` | **Preview only.** `data/member_preview.yml` holds the sample data |
| Privacy policy, Accessibility | `/privacy/`, `/accessibility/` | `content/pages/*.md` (placeholders) |

Templates are in `themes/vetnet/templates/`.

## Project layout

```
.
├── package.json         Shortcut commands (see above)
├── pyproject.toml       Python dependencies
├── uv.lock              Exact dependency versions (commit changes to this)
├── pelicanconf.py       Site settings for development
├── publishconf.py       Site settings for production (builds on pelicanconf.py)
├── data/                YAML data that drives the site (people, partners, datasets, ...)
├── plugins/
│   └── vetnet_data.py   Loads data/*.yml, checks it, and computes the live counts
├── scripts/
│   └── check_site.py    The checker behind `yarn test`
├── content/
│   ├── pages/           One Markdown file per page (title, URL, template, summary)
│   ├── news/            News and events articles, one Markdown file each
│   ├── images/          Images used by pages
│   └── extra/           robots.txt and favicon
└── themes/vetnet/
    ├── templates/       HTML templates
    └── static/          CSS, JavaScript, fonts and images
```

`output/` and `.venv/` are generated and are not committed.

## How to make a change

### Add a person

Open `data/people.yml` and add an entry at the end of the list:

```yaml
- name: Jane Doe
  role: collaborator          # or: pi
  title: Associate Professor, Veterinary Imaging
  org: University of Example
  sector: Academia            # Academia, Industry, or Clinical & public
  expertise: Veterinary imaging.
  linkedin: https://www.linkedin.com/in/jane-doe   # optional; the icon only shows if set
  data_donor: true            # optional; adds the Data donor badge
```

People are sorted A–Z by last name automatically. If the last word of the name isn't the sort name (for example "Chris De Sa"), add `sort_name: De Sa`. Every count on the site updates the next time it builds.

### Add a partner organization

Add a line to `data/partners.yml`:

```yaml
- {name: University of Example, type: University, country: USA}
```

`type` is one of `University`, `Industry`, `Clinical`, `Nonprofit` or `Government`.

### Add a news article

Create `content/news/my-article.md`:

```markdown
Title: Our first datasets are live
Date: 2026-12-01
Category: Publication
Summary: One or two sentences shown on the news list and the home page.
Featured: 1

The full article text goes here, in Markdown.
```

`Category` is `Publication`, `Event` or `Talks`. Optional lines: `Date_label` (text to show instead of the date, such as `June 9–11, 2026`), `Location`, `Link` and `Link_label` (a button to an outside page). `Featured: 1`, `2` or `3` puts the article on the home page: `1` is the large card.

### Add or edit a dataset

Add an entry to `data/datasets.yml`. Remove `example: true` so it counts toward the Datasets number on the home page. Entries with `example: true` are demonstration records from the design and don't count.

### Add or edit a page

Pages are Markdown files in `content/pages/`. Most pages take their layout from a template in `themes/vetnet/templates/` named in the `Template:` line. Privacy policy and Accessibility use the simple `page` template, so their text lives in the Markdown file.

### Site-wide links and contact addresses

`data/site.yml` holds the survey, LinkedIn, GitHub, AWS bucket, sponsor packet, form links and contact emails, plus the announcement banner on/off switch. A value of `null` means "not available yet": the button or link is shown greyed out. Fill in the value and it becomes a live link everywhere it is used.

### Change the look of the site

Colors, fonts and spacing are CSS variables in `themes/vetnet/static/css/tokens.css`. Component styles are in `components.css` and page styles in `pages.css`. Preview changes with `yarn start`.

## Content to fill in

Placeholders are visible on the site with a dotted underline so they're easy to find. Still needed:

- Final logo, and the full expansion of "VETNET" if there is one
- Hero photo and news images
- Number of datasets and citations for the home page stats
- Partner and sponsor logos (20 partners plus the Cornell AI Initiative)
- Whitepaper abstract (2–3 sentences) and confirmed author order
- Contact emails: general, sponsorship, contact PI and data access
- Each team's one-line focus and leaders, and each person's team (`data/teams.yml`, `data/people.yml`)
- Photos, LinkedIn links and fuller bios for each person
- Real dataset names, descriptions, S3 paths and documentation links
- Links: survey, LinkedIn, GitHub, open-access AWS bucket, access request form, feedback form, sponsor packet (`data/site.yml`)
- Privacy policy, accessibility statement and data use terms
- Wording of each automatic response email for the Join Us options

## What is and isn't connected

This draft is a pure static site. These parts are **visual only** and do not send or store anything:

- Join VETNET, e-list subscribe, sign-in, register, and the contact, access-request and feedback forms. Submitting one shows "This form isn't connected yet".
- Download and Request access buttons on datasets.
- The Portal and For Members pages, which are marked "Preview only" and use sample data.

The site loads nothing from other websites (fonts are included in the repo).

## How to contribute

1. Create a branch from `main`. Suggested names: `content/<topic>`, `feature/<topic>`, `fix/<topic>`.
2. Make small, focused commits with clear messages.
3. Preview your change locally with `yarn start`, and run `yarn test`.
4. Open a pull request against `main`. Describe what changed and why, and include a screenshot for visual changes.
5. Ask at least one other contributor to review it. Please don't push straight to `main`.

New to Git? Open a [GitHub issue](https://github.com/cuvmit/vetnet-website/issues) describing the change you'd like and someone will help.

For anything large, such as a new section of the site, open an issue or discussion first so it can be agreed before anyone builds it.

## Troubleshooting

- **`uv: command not found`**: install uv using the [instructions](https://docs.astral.sh/uv/getting-started/installation/), then open a new terminal.
- **Port 8000 is already in use**: run `PORT=8001 yarn start` and open <http://localhost:8001>.
- **The site looks out of date or odd**: run `yarn clean`, then `yarn build`.
- **The build stops with `DataError: data/...yml: entry N (...)`**: that entry in the data file is missing a required field or has a value that isn't allowed. The message says which one.
- **YAML errors**: values containing a colon (`:`) must be in quotes, for example `title: "Part 1: Overview"`.

## Fonts

Source Serif 4 and Public Sans are included under the SIL Open Font License (see `themes/vetnet/static/fonts/`).

## Contact and license

- Contact: _to be decided_
- License: _to be decided_
