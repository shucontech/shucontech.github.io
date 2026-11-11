# Scheduled content pipeline

Posts in `posts/` go live automatically on their `date`. The workflow runs
`.github/workflows/publish-scheduled.yml` every day at 06:05 IST. It:

1. Renders every post dated today or earlier to `blog/<slug>.html`.
2. Updates the blog listing and its JSON-LD, `sitemap.xml`, `llms.txt`, the homepage "Latest guides"
   block, the "Related guides" blocks on product pages, and the "More guides" box in the 4 original
   blog posts.
3. Regenerates the RSS feed at `blog/feed.xml`.
4. Commits and pushes the changes, which redeploys GitHub Pages.
5. Submits the changed URLs to IndexNow (Bing, Copilot/ChatGPT search, Yandex, etc.) so they are
   crawled within hours instead of days. The key file `06a7a11c3d7d9e6c42a9282057936d38.txt` at the
   site root must not be deleted. Google does not use IndexNow; it picks changes up from the sitemap.

Folders that start with `_` are not published by GitHub Pages (Jekyll), so drafts are not reachable
on shuconmedai.com. They **are** visible to anyone who can see the GitHub repo.

## Common tasks

| Task | How |
|---|---|
| Change a go-live date | Edit `"date"` in the post's front matter. Moving a published post into the future unpublishes it. |
| Add a post | Add `posts/<slug>.html` (format below) and a row in `calendar.csv`. |
| Validate every post | `python3 _scheduled/publish.py --check` |
| Preview what publishes on a date | `python3 _scheduled/publish.py --date 2026-11-30 --dry-run` |
| Publish now | GitHub → Actions → *Publish scheduled posts* → *Run workflow*, or run `python3 _scheduled/publish.py` locally and push. |

`calendar.csv` lists every planned topic. Rows with status `written` exist in `posts/`; `brief`
rows still need writing, and `brief - needs fact-check` topics cover regulations (PM-JAY, CGHS,
NABH, GST, DPDP, etc.) that must be checked against the current official source before publishing.
Rows marked `covered by …` are already answered by a live page or another post and should not be written.

## Post format

```html
<!--
{
  "slug": "bed-turnover-rate",
  "date": "2026-10-23",
  "title": "Bed Turnover Rate: Formula, Interval & Benchmarks",
  "og_title": "Bed Turnover Rate: Formula, Turnover Interval and What It Tells You",
  "h1": "Bed Turnover Rate: Formula, Turnover Interval and What It Tells You",
  "breadcrumb": "Bed turnover rate",
  "description": "120–155 characters, includes the primary keyword, written as a reason to click.",
  "lede": "One or two sentences shown under the H1.",
  "takeaways": ["3 or 4 one-sentence bullets shown in the Key takeaways box at the top."],
  "category": "Hospital finance",
  "product": "stakeholder-action",
  "keywords": ["bed turnover rate", "bed turnover rate formula", "..."],
  "related": ["bed-occupancy-rate-formula", "alos-average-length-of-stay", "arpob-hospital-guide"],
  "faqs": [{"q": "Question?", "a": "Plain-text answer, 1–3 sentences."}]
}
-->
<p><strong>Direct definition answering the search query in the first 2 sentences.</strong> ...</p>
<h2>...</h2>
...
```

- `title` ≤ 60 characters (shown in Google). `h1` can be longer. Write both as natural phrases
  ("AR Days in Hospitals", not "AR days hospital"); the same goes for the first sentence and headings.
- `takeaways` (optional but recommended): 3–4 bullets, 50–190 characters each. The first one answers the
  search query directly (the definition, or the formula written out). Use only facts that are in the post.
  They render as the "Key takeaways" box and as `abstract` in the article schema.
- `modified` (optional, `YYYY-MM-DD`): set it when a live post is materially edited. It shows an
  "Updated" date on the page and updates `dateModified` and the sitemap `lastmod`.
- `tool` (optional): which free tool the post promotes inline and in the side rail. One of `arpob`, `bor`,
  `alos`, `btr`, `adc`, `checklist`, `formulas`, `tools`, `glossary`. If omitted, `POST_TOOL` / `PRODUCT_TOOL`
  in `publish.py` pick one from the slug or product.
- `product` is one of: `revenue-leakage`, `insurance-claims`, `patient-engagement`,
  `stakeholder-action`, `hms`, `diagnostics`, `pharmacy`, `custom-ai`, `ai-agents`. It picks the CTA
  and which product page lists the post.
- Every `<h2>` automatically gets an id and an entry in the "On this page" table of contents, so keep
  H2s short and descriptive (aim for 6–9 per post).
- The body is just the article content: `p`, `h2`, `h3`, `ul`, `ol`, `table`, `blockquote` (for formulas),
  and `<div class="callout"><h4>..</h4><p>..</p></div>`. Leave out the H1, FAQ section, CTA, author box and
  related posts; the template adds those.
- Link to other posts with `<a href="post:other-slug">anchor</a>`. The link appears only once
  that post is live (until then it renders as plain text), so there are never broken links.
- Link to product pages with relative paths from `/blog/`, e.g. `../agents/revenue-leakage/`.
- Use INR only (₹, lakh, crore). Don't invent statistics, and hedge regulatory details.
