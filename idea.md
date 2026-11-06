# VETNET Website — Idea

> Source material: `idea/guide.docx` (Design Brief & Page Guide, Oct 28 2026) and `idea/mockup.pdf` (page mockups).
> Stack decision: **Pelican** static site generator, hosted in **Amazon S3** (fronted by CloudFront).

---

## 1. Summary

VETNET is an open initiative connecting veterinary medicine and data science. It is building an ecosystem of live benchmarks for AI in veterinary medicine ("any animal, any disease, any task"). It launched at the June 9–11, 2026 Cornell Thought Summit and published a founding whitepaper (arXiv:2610.14149, Oct 2026). Sponsor: Cornell AI Initiative. Contact PI: Renata Ivanek.

The website needs to:

1. Introduce VETNET.
2. Show who is involved.
3. Point researchers to the data.
4. Turn visitors into **members, data users and data donors**.

**Audience:** undergraduates, graduate students, postdocs, faculty, clinicians and industry researchers working where data science meets veterinary medicine.

---

## 2. The key architectural tension

Pelican produces **static HTML**. About 80% of the site is naturally static (content, directories, news, publications). The rest is dynamic in the mockups:

The table below shows the **full-fidelity approach**: build every dynamic feature exactly as mocked up. It is the most capable but also the largest footprint. **[Phase 2](#10-phase-2--reduce-the-dynamic-footprint) describes how to shrink this footprint** by replacing or removing most of these pieces. The full-fidelity build becomes an optional, conditional Phase 3.

| Mockup feature | Why it isn't static | Full-fidelity approach |
|---|---|---|
| Member sign-in / register / SSO | Needs identity and sessions | Amazon Cognito (hosted UI or JS SDK); optional SAML/OIDC federation for institutional login |
| For Members dashboard (donated data, access requests, working group) | Per-user data behind auth | Static shell page + client-side JS that calls an authenticated API (API Gateway + Lambda + DynamoDB) |
| Join forms with 10 options and automatic next steps | Needs form handling and email | API Gateway + Lambda → SES (auto-response emails) + e-list; notifications to team leads |
| E-list subscribe (footer, home, register) | Needs a mailing list backend | SES + DynamoDB, or an external list provider (Mailchimp, Buttondown, etc.) |
| Restricted dataset access and gated Download | Needs authorization | Cognito group + presigned S3 URLs from Lambda; access-request form → approval workflow |
| People/Databases search and filters | Dynamic UX | Client-side JS over a generated JSON index (Pagefind, Lunr or Fuse.js) |
| "Live" counts (collaborators, partners, datasets) | Mockup says they update automatically | **Computed at build time** from the data files (see §4). "Live" means "every rebuild", not real-time |
| Copy-BibTeX button, FAQ accordions, filter chips | Small interactions | Vanilla JS or Alpine.js; no framework |

**Principle:** keep everything that can be static static. Isolate the dynamic parts behind a small serverless API on a single subdomain (e.g. `api.vetnet.org`). The Pelican build stays simple and the S3 bucket stays a pure static origin.

---

## 3. Information architecture

Nine pages plus a shared header and footer. A News & Events page is in the nav but has no mockup (see open questions).

| # | Page | URL | Purpose |
|---|---|---|---|
| 1 | Home | `/` | What VETNET is, live stats, partners, featured news, join form |
| 2 | About | `/about/` | Mission, values, timeline, FAQ |
| 3 | People | `/people/` | Collaborators, working groups and leaders, PIs |
| 4 | Research | `/research/` | Goals, data types, summit, publications, how to cite |
| 5 | Portal | `/portal/` | Sign in / register |
| 6 | Databases | `/databases/` | Search and download datasets, request restricted access |
| 7 | Join Us | `/join/` | Ten ways to take part, each with an automatic next step |
| 8 | For Members | `/members/` | Members-only area, donated data tracking |
| 9 | Sponsors | `/sponsors/` | Current sponsor and how to become one |
| — | News & Events | `/news/` | **No mockup yet**; nav item and "View all news" target |

### Shared header
- Announcement banner (can be switched off): whitepaper on arXiv and community survey.
- Logo + "VETNET / Open data for veterinary AI".
- Nav: About · People · Research · Databases · News & Events · Join Us · Sponsors · For Members (lock icon). The current page is highlighted.
- "Portal · Log in" button.

### Shared footer
- Take the survey and Sponsorship buttons.
- Explore links.
- Connect: LinkedIn, Open-access data (AWS), GitHub.
- E-list subscribe form.
- Contact us and Member login buttons.
- "© 2026 VETNET · Sponsored by the Cornell AI Initiative", Privacy policy, Accessibility.

---

## 4. Content model (what drives the site)

Content lives in version-controlled files, and Pelican builds pages from them. This is how the "live" counts are produced.

```
content/
  pages/            about.md, research.md, sponsors.md, join.md, ...
  news/             one markdown file per article/event (Pelican articles)
  data/
    people.yml      collaborators + PIs (name, title, org, team, sector, linkedin, photo, founding_member, data_donor, role)
    partners.yml    20 organizations (name, type, country, logo, url)
    teams.yml       MVP, Repos, Governance, Stakeholder (focus, leaders)
    datasets.yml    dataset catalog (name, access, species, type, format, s3 path, docs url, contact, status)
    publications.yml
    join_options.yml  10 options (label, description, auto-response)
    site.yml        banner on/off, links (survey, LinkedIn, GitHub, AWS bucket), contact emails
  images/           photos, logos, hero
theme/vetnet/       Jinja2 templates, CSS, JS
plugins/            data loader that exposes the YAML files to Jinja
```

### Derived values (computed at build time)
- **Collaborators** = number of entries in `people.yml` (currently 40: 36 collaborators + 4 PIs).
- **Partner universities** = partners where `type == University` (10).
- **Industry & other partners** = all non-university partners (10).
- **Organizations** = number of entries in `partners.yml` (20).
- **Datasets** = number of entries in `datasets.yml`, split into open and restricted.
- **Publications** = number of entries in `publications.yml`. Citation counts are a manual field, optionally filled by a scheduled job.
- **Group counts on People** (collaborators, working groups, PIs) come from the same files.
- **Founding member** and **Data donor** badges come from boolean fields on each person.

Updating a YAML file and rebuilding changes every number on the site.

---

## 5. Pelican implementation notes

- **Theme:** custom Jinja2 theme `vetnet` with a base template (banner, header, footer) and page templates for each of the nine pages.
- **Pages vs articles:** static pages use Pelican `PAGES`. News & Events use Pelican `ARTICLES` with categories `Publication`, `Event`, `Talks` and so on. Home shows the featured items, and `/news/` lists all.
- **Data-driven pages:** People, Databases, Home partner grid and Join options render from the YAML via a small plugin that adds the data to `context`. Pelican's `JINJA_GLOBALS` or a `generator_init` hook both work.
- **Search/filter index:** a post-build step (or plugin) writes `people.json` and `datasets.json`. Client-side JS provides search, team/sector/"Data donors" filters, and Open/Restricted/species/type filters.
- **Plugins to consider:** `sitemap`, `pelican-search` or Pagefind (run post-build), `image_process` for responsive photos and logos.
- **URLs:** use directory-style URLs (`/people/`). S3 static hosting needs `index.html` per directory, so set `PAGE_URL = '{slug}/'` and `PAGE_SAVE_AS = '{slug}/index.html'`.
- **Members-only pages:** `/members/` is a public static shell. All private data is fetched after login, so nothing sensitive is in the build output.
- **Local dev:** `pelican --autoreload --listen`.

---

## 6. Hosting and deployment (S3)

- **S3 bucket** holds `output/`. Prefer keeping it private with **CloudFront + Origin Access Control** rather than public S3 website hosting. CloudFront gives HTTPS, a custom domain and caching.
- **ACM certificate** (us-east-1) and **Route 53** for the domain.
- **CloudFront Function or redirects** for directory index handling, since the REST S3 origin doesn't serve `index.html` for subpaths on its own.
- **Deploy:** `pelican content -s publishconf.py` followed by `aws s3 sync output/ s3://<bucket> --delete`, then a CloudFront invalidation. Automate with GitHub Actions using OIDC to assume an AWS role, with no long-lived keys.
- **Dataset buckets are separate** from the website bucket. The "Open-access data (AWS)" link and the `s3://` dataset paths point to the AWS Open Data bucket(s). Restricted datasets sit in a private bucket and are shared through presigned URLs.
- **Infrastructure as code:** keep the bucket, CloudFront, API, Cognito and SES setup in Terraform, CDK or SAM so it is reproducible.
- **Environments:** a staging bucket/distribution for review, and production.

---

## 7. Design system (from the guide)

| Element | Choice |
|---|---|
| Primary | Cornell red `#B31B1B` (banner, hero, footer, buttons, links) |
| Headings | Deep carnelian `#6E1414` |
| Accents | Blush `#F7E6E4`; light pink `#F6C9C4` for labels on red |
| Background | Warm off-white `#F7F6F2`, white cards, warm gray body text |
| Badges | Founding member: red outline + star. Data donor / restricted: amber `#F6E8D7` / `#7A4A1A` |
| Heading font | Source Serif 4 (Google Fonts) |
| Body font | Public Sans (Google Fonts) |
| Logo | Placeholder "V" network mark (replace with the real logo) |
| Layout | 1320 px column, fluid, reflows for phones; 56–64 px section spacing |
| Accessibility | Standard text contrast; buttons ≥ 44 px tall; Accessibility statement linked in the footer |

Consider self-hosting the fonts for privacy and performance. Implement the tokens as CSS custom properties.

---

## 8. Page specifications

### 1 · Home
- **Hero:** red section with headline "Shared data to move veterinary AI forward", description, buttons "Learn more about VETNET" (→ About) and "Browse datasets" (→ Databases). Static photo on the right with a whitepaper card overlay.
- **Stats bar (build-time computed):** Collaborators, Partner universities, Industry & other partners, Datasets, Publications and citations.
- **Collaborators:** 20 partner tiles (5 per row) with logo, type and country. Filter chips: All / Universities / Industry / Clinical & public. Heading count is computed. Sponsor strip: "Sponsored by Cornell AI Initiative" + Become a sponsor.
- **Featured news:** whitepaper as lead, two smaller cards (Thought Summit, keynotes), View all news.
- **Join the community:** pitch, audience chips, survey and sponsor buttons, and a compact form with the 10 options, email field and "Join VETNET".

### 2 · About
- Mission (live benchmarks, why veterinary data is hard) and three values: Open by default, Rigorous, Collaborative.
- "Our story so far" timeline: Aug 2025 project funded → June 9–11, 2026 Thought Summit → Oct 2026 whitepaper → Next: first datasets (target date TBD).
- FAQ accordion with four questions: contact, stay up to date, get involved, accomplishments.

### 3 · People
- Hero with jump-link pills (Collaborators · Working groups · PIs), counts computed.
- **Collaborators** (36, A–Z): search by name/institution/expertise, team filters, sector dropdown, "Data donors" toggle. Card: photo, name, title, org, team tag, sector, LinkedIn icon (only if provided), badges, expertise.
- **Working groups & leaders:** four cards (MVP, Repos, Governance, Stakeholder) with a one-line focus and leader(s).
- **Principal investigators:** Renata Ivanek (Contact PI, with Contact the PI button), Casey Cazer, Parminder Basran, Jennifer J. Sun.

### 4 · Research
- Two goals: (1) data for good research, (2) benchmarks, competitions and papers.
- "Where we're starting": Now = CT scans and radiographs (DICOM). Coming soon = free-text notes, tabular records, more.
- "Where it began": three summit day cards (June 9, 10, 11).
- Publications by VETNET: whitepaper card (abstract, Read on arXiv, Cite, authors list).
- How to cite: plain-text citation and a BibTeX block with a Copy button.
- Publications using VETNET data: empty state with a "Submit a publication" button.

### 5 · Portal
- Sign in (email, password, forgot password, keep me signed in, optional institutional SSO) and Register (first/last name, email, institution, role, password, agree to data use terms and privacy policy).
- Notice that new members are added to the e-list automatically (unsubscribe anytime).
- Three benefit tiles: restricted data requests, working groups, early news.

### 6 · Databases
- Search bar with suggested keywords. Results bar with counts (open vs. restricted). Filters for access, species and data type.
- **Open access** cards: name, tags, description, S3 path, documentation link, Download button.
- **Restricted access** cards: same, plus named contact, Request access, and a locked Download. A callout explains the request process and links to the form.
- Feedback band: Leave feedback / Add your data.

### 7 · Join Us / Opportunities
- Ten option cards, each with its automatic next step (table below), then a "Tell us about you" form (name, email, institution, role).
- Working groups strip (links to leaders on People).
- "Contributing data?" panel with the planned protections (de-identification, data use agreements, controlled access, donor credit). These are marked **to confirm**.

| Option | Automatic response |
|---|---|
| Receive updates and announcements | Welcome email with latest update; stays on e-list |
| Join events, convenings or working groups | Event calendar + working-group interest form; team leads notified |
| Use benchmark datasets | Links to catalog, docs, member sign-up, restricted-access form |
| Contribute data or datasets | Data intake form + data-protection overview; data team follows up |
| Contribute your expertise | Expertise-profile form |
| Contribute to validation | Validation-site questionnaire (setting, species, caseload) |
| Contribute to technical infrastructure | GitHub invitation + contributor guide |
| Help shape governance, ethics & policy | Introduction to Governance team and open questions |
| Contribute to education, training & mentorship | Education and mentorship interest form |
| Facilitate partnerships or funding | Routed to contact PI with sponsorship information |

### 8 · For Members
- Welcome line (institution, member since, team, badges).
- **My donated data:** summary tiles and a table with a status pipeline (Intake review → De-identifying → Published), access level, downloads and citations.
- Cards: My data access requests, My working group, Member announcements, My participation, Resources.
- Signed-out view: lock icon and "Sign in or register free".
- The mockup labels this a "proposed starting point"; treat it as phase 2.

### 9 · Sponsors
- Founding sponsor: Cornell AI Initiative.
- What sponsorship supports: open datasets, benchmarks & competitions, convenings, students & training (proposed).
- Become a sponsor: contact PI, sponsor packet PDF.

---

## 9. Suggested phasing

**Phase 1: Static MVP (Pelican + S3/CloudFront)**
- Theme, design tokens, header/footer.
- Home, About, People, Research, Sponsors, News & Events.
- Databases as a static catalog with client-side search. Open datasets link straight to the S3 paths.
- Contact and e-list subscribe via a hosted form/list service. **No custom backend in this phase.**
- Build-time counts, CI/CD deploy, sitemap, accessibility pass.

**Phase 2: Reduce the dynamic footprint** (see [§10](#10-phase-2--reduce-the-dynamic-footprint))
- Deliver the join flow, restricted-data access, donor tracking, citations and a members area using hosted services, build-time generation and a manual-but-scripted approval step instead of custom accounts and APIs.
- Target: no servers, no databases, no stored passwords, and at most one small function.
- Requires a few mockup adjustments (Portal, For Members, locked Download button).

**Phase 3: Full-fidelity dynamic build (conditional)**
- Only if Phase 2 volume or user feedback justifies it: Cognito accounts, the For Members dashboard with live status, self-service access requests and automated presigned downloads (the §2 table).
- Triggers are defined in §10.8.

---

## 10. Phase 2 — Reduce the dynamic footprint

> **Status: Phase 2.** Not part of the Phase 1 build. This section proposes how to deliver the original design with as little dynamic infrastructure as possible.

### 10.1 Goal and guardrails

Deliver the *outcomes* of the original design (members, data users, data donors) while avoiding the *machinery* (user accounts, session handling, a database, and a custom API). Guardrails:

- **No user passwords or sessions** stored by VETNET.
- **No database** owned by VETNET. State lives in Git, a spreadsheet, or a hosted service.
- **No always-on compute.** Anything that runs is a scheduled CI job, a one-off admin script, or (at most) one Lambda Function URL.
- **The S3 website bucket stays a pure static origin.**
- Anything involving sensitive data has a **human in the loop** instead of an automated gate. Volume is low (a 40-person initiative with a handful of restricted datasets), so manual approval is cheap and easier to audit.

### 10.2 The key insight: why accounts exist at all

The mockups say registration is "free and open to everyone". So accounts are not there to protect the site; they exist to do four jobs. Each can be done without accounts:

| Job accounts do in the mockups | Account-free replacement |
|---|---|
| Build the e-list | Join/subscribe form feeds a hosted mailing list |
| Gate restricted datasets | Request form + human approval + time-limited access (§10.5) |
| Let donors see their data status | Status lives in `datasets.yml` plus a periodic emailed donor report (§10.6) |
| Give members private resources and working-group info | Link out to tools that already have auth, or a light gate on a few static pages (§10.7) |

### 10.3 Feature-by-feature footprint reduction

| Feature | Full-fidelity (original) | Phase 2 replacement | Dynamic footprint left | What the user loses |
|---|---|---|---|---|
| E-list subscribe (footer, home) | SES + DynamoDB | Hosted list provider's embedded/POST form (e.g. Mailchimp, MailerLite, Buttondown, Brevo) | None (third-party) | Nothing |
| Join Us: 10 options + automatic next steps | API Gateway + Lambda + SES | Hosted form. Each checked option becomes a **tag/group** in the list provider; each tag triggers the provider's own **automation email** (the "automatic next step") | None (third-party config) | Nothing visible. Confirm the chosen provider's plan supports tag-triggered automations |
| Notifying team leads / contact PI | Lambda fan-out | Provider automation or form-tool notification rules sending to a shared mailbox or lead per team | None | Nothing |
| Contact form, feedback, "Add your data", "Talk to us about donating" | Lambda + SES | Hosted form tool (e.g. Tally, Google Forms, Formspree), or plain `mailto:` links | None | Nothing |
| "Submit a publication" | Form + review queue | GitHub issue form or PR against `publications.yml` (or the generic form) | None | Needs a GitHub account, or use the generic form |
| Portal: sign in / register | Cognito | **Register = the Join form.** No sign-in. See §10.7 for the optional light gate | None | No account; "Log in" disappears or becomes "Members" resources |
| Restricted dataset request, approval and download | Cognito group + presigned URLs from Lambda | Request form → email to data access coordinator → DUA → **admin script** issues a time-limited S3 presigned URL (or grants access via bucket policy) and emails it. See §10.5 | One admin script, run by a human | Approval is not instant; no in-page status |
| Locked "Download" button | Unlocks on approval | **Remove it.** A static page can't know who is approved. Show "Request access" only | None | Resolves open question 8 |
| Donated-data tracker (My donated data) | DynamoDB + authenticated API | Dataset records in Git carry `status` and `donor`; **monthly emailed donor report**; public credit on dataset pages. See §10.6 | One scheduled CI job | No self-serve dashboard |
| Downloads and "papers citing your data" counts | Live counters | Scheduled job: S3/CloudFront access logs via Athena (or log parsing) for downloads; OpenAlex/Crossref for citations. Writes JSON committed to the repo and shown on the next build | One scheduled CI job | Counts are daily/monthly, not real-time |
| My data access requests (statuses) | Per-user view | Status communicated **by email** at each step; internal tracking sheet for the coordinator | None | No self-serve status page |
| My working group, next meeting, notes, roster | Per-user view | Public team pages on People with a link to the team's calendar/folder (Google Drive, Slack, Teams or GitHub Discussions) that already handle their own auth | None | No unified dashboard |
| My participation / "Edit my choices" | Profile DB | Link to a **preferences page** in the list provider (tags are the participation record) | None | Slightly off-brand page |
| Live counts and stats bar | Dynamic | Already build-time (§4). Add a **nightly scheduled rebuild** so the numbers and citation data refresh without a commit | One scheduled CI job | Nothing |
| People/Databases search and filters | Client-side | Unchanged | None | Nothing |
| Content editing by non-developers | N/A | Optional: maintain `people.yml`/`partners.yml` in a **Google Sheet** pulled at build time, or Decap CMS committing to Git | One build-time fetch | Nothing |

### 10.4 Ranked "less dynamic" tiers

If the full Phase 2 is still more than needed, the options below can be picked per feature, from smallest to largest footprint:

1. **Tier 0 — Pure static + third-party services.** Hosted forms, hosted list, Google Sheet, scheduled GitHub Actions. *Zero AWS compute.* (Recommended target.)
2. **Tier 1 — One Lambda Function URL.** A single function that accepts all form posts, writes to the list provider and sends mail via SES. Use this only if the organisation will not allow third-party form processors for institutional-data or privacy reasons. No API Gateway or database.
3. **Tier 2 — Light gate for a few static pages.** CloudFront + a CloudFront Function (shared passphrase) or Lambda@Edge/OIDC. See §10.7.
4. **Tier 3 — Full Cognito + API + DynamoDB.** This is Phase 3.

### 10.5 Restricted data without accounts

Proposed flow:

1. Visitor clicks **Request access** on a restricted dataset card. The link opens the request form with the dataset ID in the query string (e.g. `?dataset=abdominal-ct-clinical`).
2. The form collects name, email, institution, role, intended use and acceptance of the data use terms. The submission emails the **data access coordinator** and appends a row to a tracking sheet.
3. The coordinator reviews, and signs a **data use agreement** (PDF/e-signature, or via the institution's usual process).
4. The coordinator runs `scripts/grant_access.py <dataset> <email> --days 14`, which creates a time-limited S3 presigned URL (or adds the requester's AWS account/role to the bucket policy for ongoing access) and drafts the email. Presigned URLs from IAM user credentials can last up to 7 days, so long-lived access should use bucket-policy grants or short re-issues.
5. The requester is notified by email; the sheet row is updated.

Alternative: **host restricted data on a platform that already provides credentialed access** (e.g. Hugging Face gated datasets, a Dataverse instance, Synapse or similar). This moves the whole approval workflow out of VETNET's footprint at the cost of having data outside the AWS bucket. Decide with the data governance team.

Open-access data needs none of this: link directly to the public S3 paths (ideally registered with AWS Open Data) so downloads need no website logic.

### 10.6 Donor tracking without a dashboard

- Each dataset in `datasets.yml` gets `donor`, `contributed` (date), `status` (`intake` → `de-identifying` → `published`), `access`, `contact`.
- **Public credit:** published datasets list their donors on the dataset page and in documentation. The "Data donor" badge on People is derived from the same file.
- **Private status:** a scheduled job generates a **monthly donor report** (status, downloads, citations) and emails it to each donor via the list provider or SES. Donors who want a faster answer email the data team.
- **Internal tracking:** the data team can manage intake in a GitHub Project, Airtable or shared sheet, which is a tool they already need.

### 10.7 The "Members" area, three options

Choose one (in order of least to most dynamic):

- **A. No gate, recommended.** Rename "For Members" to **Resources**. Publish what isn't sensitive (data contribution guidelines, DUA templates, logo kit). Anything that must stay private is linked from the welcome email and lives in a Drive/Teams/Slack space that has its own auth.
- **B. Light gate.** Put `/members/` behind a CloudFront Function with a shared passphrase that is rotated periodically and distributed in the welcome email. This is a deterrent rather than real security and so is only suitable for non-sensitive material.
- **C. Delegated identity.** Gate `/members/` via OIDC login with an identity provider VETNET doesn't operate (institutional SSO, GitHub org membership, ORCID). No password storage, but it brings back an auth-aware edge function.

### 10.8 Triggers to escalate to Phase 3

Revisit the full-fidelity build if any of these hold (initial proposals; adjust):

- Restricted-access requests exceed roughly **15–20 per month**, or approval turnaround becomes a complaint.
- Donors repeatedly ask for self-serve, real-time status.
- A funder or regulator requires audit logs or identity-verified access that a manual process can't provide.
- Member count or working-group traffic makes email/Drive-based coordination unmanageable.

### 10.9 Impact on the mockups and nav

| Mockup element | Change in Phase 2 |
|---|---|
| Header **Portal · Log in** button | Replace with **Join VETNET** (or keep "Members" if option 10.7-B/C) |
| **Portal** page (sign in + register) | Collapse into the Join Us flow; "Register" becomes the join form |
| **For Members** page | Becomes **Resources** (10.7-A), with donor reporting by email |
| Footer **Member login** | Remove, or point to Resources |
| Restricted card **locked Download** | Remove; show **Request access** only |
| Home/Join "see what happens next" | Unchanged; powered by list-provider automations |
| "Papers citing your data", download counts | Shown on dataset pages from generated JSON (not per-user) |

The original mockups stay as the target design for Phase 3.

### 10.10 Resulting footprint

- **Custom runtime components:** 0 (Tier 0) or 1 Lambda Function URL (Tier 1).
- **Databases / servers / user accounts:** none.
- **Scheduled jobs (GitHub Actions):** nightly rebuild with refreshed counts and citations; monthly donor report and download stats.
- **Admin scripts (human-run):** `grant_access.py`.
- **Third-party services:** one list/automation provider, one form tool (can be the same), one tracking sheet. Each needs a privacy/data-processing check with Cornell.
- **AWS:** S3 + CloudFront + ACM + Route 53, plus the existing data buckets.

### 10.11 Risks and trade-offs

- **Third-party data processing:** emails, names and institutions go to external providers. Needs a privacy review, DPA, and (given UK/EU partners) GDPR consent wording.
- **Vendor limits:** free tiers may not include tag-triggered automations or enough volume. Verify before selecting a provider.
- **Manual steps don't scale** and depend on named people (data access coordinator). Name a primary and a backup.
- **Weaker UX** than a real dashboard: status is delivered by email and not in-page.
- **Shared-passphrase gate is not real security** (10.7-B). Never put restricted or personal data behind it.

---

## 11. Content still needed (from the guide)

- Final logo, and the full expansion of "VETNET" if any.
- Hero photo and news images (static).
- Dataset count and citation count.
- Partner and sponsor logos (20 partners plus Cornell AI Initiative).
- Whitepaper abstract (2–3 sentences) and confirmed author order.
- Contact emails: general, sponsorship, data access.
- Each team's one-line focus and leaders; each person's team assignment.
- Photos, LinkedIn links and fuller bios.
- Dataset names, descriptions, S3 paths and documentation links.
- Survey link, sponsor packet PDF, wording of each automatic response email.
- Links: LinkedIn, open-access AWS bucket, GitHub, access request form, feedback form.
- Privacy policy, accessibility statement and data use terms.

---

## 12. Open questions

**From the guide**
1. Is the Thought Summit participant list the same as the whitepaper author list? (All 40 currently get the Founding member badge.)
2. Should the Cornell Center for Data Science for Enterprise & Society also be listed as a sponsor?
3. Which team has two leaders, and which leader is also a PI?
4. Who receives each automatic response (data contribution and partnerships need a named owner)?
5. Should News & Events be its own page? (Currently in the nav without a mockup.)
6. Which data protections will VETNET commit to for donated data?
7. Will sign-in support institutional SSO, or only email and password?
8. Does the restricted-data Download button stay visible but locked, or appear only after approval?

**New, raised by the Pelican + S3 choice**
9. Is it acceptable that "live counts" update on rebuild rather than in real time? (Recommended, with a CI deploy on every content change.)
10. Who will maintain content, and are they comfortable editing YAML/Markdown in Git? If not, consider a lightweight CMS (e.g. Decap CMS) that commits to the repo.
11. Auth and member data: build on AWS (Cognito + Lambda + DynamoDB) or use an external service? Cornell IT/security requirements may decide this.
12. E-list provider: SES-based custom list or an external tool? Also, auto-subscribing registrants without opt-in needs a legal check (GDPR/CAN-SPAM), since partners are in the UK, EU and elsewhere.
13. Who hosts the domain (`vetnet.org` appears in the mockup), and does Cornell need to approve the AWS account and DNS?
14. Is a PHI/privacy review needed for member profiles and the donated-data tracker?

**Phase 2 (footprint reduction)**
15. Is a no-account model acceptable, with "Register" meaning "join the list" and no sign-in? This drives most of the Phase 2 savings (§10.2).
16. Which hosted list/form providers are approved by Cornell, and do their plans support tag-triggered automations?
17. Who is the named data access coordinator (and a backup) for manual restricted-data approvals, and what is the expected turnaround?
18. Keep restricted data in the AWS bucket with scripted presigned/bucket-policy grants, or move it to a platform with built-in credentialed access (§10.5)?
19. For the Members area, which option: A (no gate), B (shared passphrase) or C (delegated identity)? (§10.7)
20. Are the Phase 3 escalation triggers in §10.8 the right ones?

---

## 13. Spots in the source documents to double-check

- The mockup's header says "Collaborators · 36", while the hero says 40. That works only if the 4 PIs are counted separately, so the computed count must be defined clearly (PIs + collaborators = 40).
- The mockup shows 3 donated datasets and 1 published for a sample user. This is placeholder data, not real content.
- The citation text and the BibTeX use "et al.", and the guide notes "author order to be confirmed".
- The mockup shows "[Team]" on every person card, so no team assignments exist yet.
- The citation date (Oct 2026) and the arXiv ID `2610.14149` should be verified before launch.
