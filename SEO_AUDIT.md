# Shucon MedAI SEO and Conversion Audit

Audit date: 2026-09-16

## Current architecture

- Static HTML/CSS/JavaScript site deployed on GitHub Pages through `CNAME`; no site generator or build pipeline.
- Homepage is a single long-form landing page with an inline revenue-at-risk calculator and Google Apps Script contact form.
- Content currently consists of a blog hub and four HTML articles under `/blog/`.
- Shared visual system lives in `css/shucon-vc.css`; article/listing styles live in `css/blog.css`.
- GA4 (`G-5D6VNZNNKQ`) and Apollo website tracking are present on the homepage. Blog pages contain GA4 but no conversion event instrumentation.

## Findings before implementation

### Strong foundations

- Homepage and every existing blog page have a unique title, description, canonical URL and one visible H1.
- Existing articles use visible authorship/date metadata, `BlogPosting`, breadcrumbs and genuine on-page FAQ content where `FAQPage` is used.
- `robots.txt` allows the public site, blocks legacy/demo trees and declares the XML sitemap.
- `sitemap.xml` is valid and includes the homepage, blog hub and all four current articles.
- Homepage has strong supported proof, a working calculator, clear transaction-chain positioning and an existing-system adoption message.
- Images in current indexable pages have descriptive alt text; most product icons are decorative inline SVG.
- Responsive rules already collapse major grids at 980px and 640px.

### Highest-priority gaps

1. There are no dedicated commercial-intent routes for hospital revenue leakage, hospital AI, operations automation, billing leakage, pharmacy/inventory, the pharmacy leakage case study or UAE intent.
2. The homepage title and first-screen copy over-index on generic HMS/ERP language instead of hospital operational intelligence and revenue leakage.
3. The calculator ends in a generic contact/demo CTA and does not explain the next diagnostic step or track funnel progression.
4. CTA language is mostly “Book a demo”; there is no low/medium/high-intent CTA ladder.
5. No lead-magnet/checklist route exists.
6. Commercial pages cannot currently form a topic cluster, and articles can only link back to homepage anchors.
7. GA4 is installed, but requested funnel events are not consistently emitted.
8. There is no custom 404 page.
9. The homepage `SoftwareApplication` offer declares a zero price even though no free offer is presented; this can misrepresent the commercial page.
10. Homepage breadcrumb schema uses fragment URLs for sections rather than a real site hierarchy. A `WebSite` entity is absent.
11. Contact form reports success for every completed XHR regardless of HTTP status and has no network/timeout fallback.
12. Apollo is initialized immediately and can throw if its expected global is unavailable.
13. The Apple touch icon points to SVG despite existing PNG favicon assets.
14. Navigation and footer do not expose a deliberate commercial topic cluster.

### Content and trust risks

- Existing blog copy includes broad industry ranges and benchmark statements without citations. These should not be expanded into additional unsupported numerical claims.
- Existing wording is India-specific in places. New UAE content must describe market intent and compatibility without implying UAE customers or regulatory certifications.
- The supported `$15,000+` leakage result can be used, but customer identity and operational details must remain anonymous.

## Implementation plan

- Preserve the static GitHub Pages stack and existing design tokens.
- Add concise, executive-focused clean routes using directory `index.html` files.
- Add a shared commercial-page stylesheet and shared vanilla-JS analytics/navigation helper.
- Reframe the homepage first screen, CTA ladder, case-study/internal links, calculator next step and form reliability without replacing its overall structure.
- Add a printable 25-point checklist page rather than introducing a PDF-generation dependency.
- Update sitemap, schemas, metadata, navigation/footer links and 404 handling.
- Validate HTML structure, JSON-LD, links, canonicals, sitemap/robots, responsive rendering, calculator, forms and browser console.

## Existing routes reviewed

- `/`
- `/blog/`
- `/blog/hospital-revenue-leakage-guide.html`
- `/blog/pharmacy-inventory-reconciliation.html`
- `/blog/fragmented-hospital-software.html`
- `/blog/arpob-hospital-guide.html`

Legacy files and demo/plugin trees are not part of the intended indexable architecture and remain excluded from the sitemap; demo/plugin trees remain blocked by `robots.txt`.
