# Scheduled content pipeline

Posts in `posts/` go live automatically on their `date`. The workflow runs
`.github/workflows/publish-scheduled.yml` every day at 06:05 IST. It:

1. Renders every post dated today or earlier to `blog/<slug>.html`.
2. Updates the blog listing and its JSON-LD, `sitemap.xml`, `llms.txt`, the homepage "Latest guides"
   block, the "Related guides" blocks on product pages, and the "More guides" box in the 4 original
   blog posts.
3. Commits and pushes the changes, which redeploys GitHub Pages.

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

`calendar.csv` lists all 156 planned topics. Rows with status `written` exist in `posts/`; `brief`
rows still need writing, and `brief - needs fact-check` topics cover regulations (PM-JAY, CGHS,
NABH, GST, DPDP, etc.) that must be checked against the current official source before publishing.

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

- `title` ≤ 60 characters (shown in Google). `h1` can be longer.
- `product` is one of: `revenue-leakage`, `insurance-claims`, `patient-engagement`,
  `stakeholder-action`, `hms`, `diagnostics`, `pharmacy`, `custom-ai`, `ai-agents`. It picks the CTA
  and which product page lists the post.
- The body is just the article content: `p`, `h2`, `h3`, `ul`, `ol`, `table`, `blockquote` (for formulas),
  and `<div class="callout"><h4>..</h4><p>..</p></div>`. Leave out the H1, FAQ section, CTA, author box and
  related posts; the template adds those.
- Link to other posts with `<a href="post:other-slug">anchor</a>`. The link appears only once
  that post is live (until then it renders as plain text), so there are never broken links.
- Link to product pages with relative paths from `/blog/`, e.g. `../agents/revenue-leakage/`.
- Use INR only (₹, lakh, crore). Don't invent statistics, and hedge regulatory details.
