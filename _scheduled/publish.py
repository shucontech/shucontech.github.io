#!/usr/bin/env python3
"""Publish scheduled blog posts whose go-live date has arrived.

Each run (idempotent):
  * renders every post in _scheduled/posts/ with date <= today (IST) to blog/<slug>.html
  * resolves <a href="post:slug"> links (linked once the target is live, plain text before)
  * rebuilds auto-managed blocks: blog listing + Blog JSON-LD, sitemap, llms.txt,
    homepage "latest guides", product-page "guides" and legacy-post "more guides"
  * regenerates the RSS feed (blog/feed.xml)
  * with --urls-out, lists changed page URLs for IndexNow submission

Usage: python3 _scheduled/publish.py [--date YYYY-MM-DD] [--dry-run] [--check] [--urls-out FILE]
"""
import argparse
import datetime as dt
import html
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POSTS_DIR = os.path.join(ROOT, '_scheduled', 'posts')
SITE = 'https://shuconmedai.com'
IST = dt.timezone(dt.timedelta(hours=5, minutes=30))
AUTHOR = {
    "@type": "Person", "name": "Saksham Gupta",
    "url": SITE + "/leadership/saksham-gupta/",
    "sameAs": ["https://www.linkedin.com/in/saksham9/"],
    "jobTitle": "Founder & CEO",
    "worksFor": {"@type": "Organization", "name": "Shucon MedAI", "url": SITE + "/"},
}

# Product pages: path, label, CTA copy
PRODUCTS = {
    'revenue-leakage': ('agents/revenue-leakage/', 'Revenue leakage detection agents',
                        'Find the revenue your hospital is already losing',
                        'Shucon MedAI agents reconcile billing, pharmacy, inventory and claims continuously and flag unbilled services before the patient is discharged.'),
    'insurance-claims': ('agents/insurance-claims/', 'Insurance claim and TPA agents',
                         'Move every insurance claim forward, faster',
                         'Shucon MedAI claim agents check documentation readiness, track payer queries and flag denial risks before a file goes to the TPA.'),
    'patient-engagement': ('agents/patient-engagement/', 'Patient engagement voice agents',
                           'Never miss a patient call or follow-up again',
                           'Shucon MedAI voice agents answer and place patient calls for appointments, reminders and follow-ups, and hand over to your team when needed.'),
    'stakeholder-action': ('agents/stakeholder-action/', 'Stakeholder action agents',
                           'Turn hospital data into owned next actions',
                           'Shucon MedAI agents tell leadership, finance, operations, nursing and pharmacy exactly what needs attention today, and who owns it.'),
    'hms': ('platform/hospital-management-system/', 'Hospital management system',
            'One connected platform for your whole hospital',
            'The Shucon MedAI HMS connects OPD, IPD, billing, pharmacy, inventory, lab, OT and insurance on one transaction model, with AI agents built in.'),
    'diagnostics': ('solutions/diagnostics-centres/', 'Diagnostic centre software',
                    'Run your lab and radiology centre on one system',
                    'Shucon MedAI connects bookings, sample tracking, reporting, billing and referrals for diagnostic centres, with agents that chase every delay.'),
    'pharmacy': ('hospital-pharmacy-inventory/', 'Pharmacy and inventory AI',
                 'Stop medicine leaving without a bill',
                 'Shucon MedAI reconciles prescriptions, dispensing, stock and billing continuously, so pharmacy leakage, expiry and pilferage surface early.'),
    'custom-ai': ('custom-healthcare-ai/', 'Custom healthcare AI agents',
                  'Build AI agents around your own SOPs',
                  'Shucon MedAI designs custom agents that follow your workflows, approvals and systems, with humans in the loop where it matters.'),
    'ai-agents': ('ai-agents/', 'Healthcare AI agents',
                  'See healthcare AI agents run on your workflows',
                  'Shucon MedAI agents work across revenue, claims, patient calls and operations, over your existing software or our HMS.'),
}

# Hand-written posts that already exist in blog/
LEGACY = {
    'hospital-revenue-leakage-guide': ('Revenue Leakage in Hospitals: 7 Silent Ways You\'re Losing Money', 'Hospital finance', 'revenue-leakage', '2026-07-30',
                                      'The seven most common leaks between departments, and how to detect and stop them.'),
    'pharmacy-inventory-reconciliation': ('Pharmacy Inventory Reconciliation: Definition, Formula and Leakage Fixes', 'Pharmacy & inventory', 'pharmacy', '2026-07-30',
                                          'Match dispensing, stock and billing continuously so medicine never leaves without a bill.'),
    'fragmented-hospital-software': ('Why Fragmented Hospital Software Causes Revenue Leakage', 'Hospital software', 'hms', '2026-07-30',
                                     'Why siloed hospital systems leak money, and how one shared transaction model closes the gaps.'),
    'arpob-hospital-guide': ('What is ARPOB in a Hospital? Full Form, Formula and Benchmarks', 'Hospital finance', 'revenue-leakage', '2026-07-30',
                             'Average Revenue Per Occupied Bed: the formula, India benchmarks and what drags it down.'),
}

# Pages that get an auto-maintained "guides" block, keyed by product
PRODUCT_PAGES = {
    'agents/revenue-leakage/index.html': ['revenue-leakage'],
    'agents/insurance-claims/index.html': ['insurance-claims'],
    'agents/patient-engagement/index.html': ['patient-engagement'],
    'agents/stakeholder-action/index.html': ['stakeholder-action'],
    'platform/hospital-management-system/index.html': ['hms'],
    'solutions/diagnostics-centres/index.html': ['diagnostics'],
    'custom-healthcare-ai/index.html': ['custom-ai', 'ai-agents'],
    'ai-agents/index.html': ['ai-agents', 'custom-ai', 'patient-engagement', 'stakeholder-action'],
    'hospital-pharmacy-inventory/index.html': ['pharmacy'],
    'hospital-revenue-leakage/index.html': ['revenue-leakage'],
    'hospital-billing-leakage/index.html': ['revenue-leakage', 'insurance-claims'],
    'hospital-operations-ai/index.html': ['stakeholder-action', 'patient-engagement'],
    'hospital-ai/index.html': ['ai-agents', 'stakeholder-action'],
    'hmis/index.html': ['hms'],
    'pacs/index.html': ['diagnostics'],
    'ris/index.html': ['diagnostics'],
    'lis/index.html': ['diagnostics'],
    'hospital-billing-software/index.html': ['revenue-leakage', 'insurance-claims'],
    'hospital-statistics-formulas/index.html': ['stakeholder-action'],
}

# Free tools promoted inside articles: path, title, one-line pitch, link label
TOOLS = {
    'arpob': ('tools/arpob-calculator/', 'Free ARPOB calculator',
              'Enter beds, occupancy and IPD revenue to get your ARPOB, and what a ₹1,000 rise is worth a year.', 'Open the calculator'),
    'bor': ('tools/bed-occupancy-rate-calculator/', 'Free bed occupancy rate calculator',
            'Enter beds, days and occupied bed days to get BOR %, average occupied beds and empty bed days.', 'Open the calculator'),
    'alos': ('tools/alos-calculator/', 'Free ALOS calculator',
             'Enter inpatient days and discharges to get average length of stay, plus the bed days a shorter stay frees up.', 'Open the calculator'),
    'btr': ('tools/bed-turnover-rate-calculator/', 'Free bed turnover rate calculator',
            'Get discharges per bed and the turnover interval, the average days a bed stays empty between patients.', 'Open the calculator'),
    'adc': ('tools/average-daily-census-calculator/', 'Free average daily census calculator',
            'Enter inpatient service days and days in the period to get ADC, plus implied bed occupancy.', 'Open the calculator'),
    'checklist': ('hospital-revenue-leakage-checklist/', '25-point revenue leakage audit checklist',
                  'Audit billing, pharmacy, inventory, cancellations, claims and discharge controls. Free and printable.', 'Use the checklist'),
    'formulas': ('hospital-statistics-formulas/', 'Hospital statistics formulas, in one page',
                 'Bed occupancy rate, ALOS, average daily census, bed turnover, death rates and ARPOB with worked examples.', 'See the formulas'),
    'tools': ('tools/', 'Free hospital calculators',
              'ARPOB, bed occupancy rate, ALOS, bed turnover and average daily census. No sign-up, runs in your browser.', 'Open the tools'),
    'glossary': ('glossary/', 'Hospital full forms glossary',
                 'Plain-English meanings of OPD, IPD, TPA, MRD, NABH, EMR, LIS, PACS, ALOS, ARPOB and more.', 'Browse the glossary'),
}
# Which tool an article promotes: by slug first, then by product. None = no inline promo.
POST_TOOL = {
    'bed-occupancy-rate-formula': 'bor', 'alos-average-length-of-stay': 'alos', 'bed-turnover-rate': 'btr',
    'hospital-kpis-list': 'formulas', 'hospital-mis-report': 'formulas', 'discharge-process-tat': 'alos',
    'how-to-increase-hospital-revenue': 'arpob', 'payer-mix-hospital': 'arpob', 'opd-to-ipd-conversion-ratio': 'tools',
    'emr-vs-ehr-vs-hms': 'glossary', 'tpa-desk-in-hospital': 'glossary', 'admission-process-in-hospital': 'glossary',
    'opd-process-flow-hospital': 'glossary', 'hospital-management-system-modules': 'glossary',
}
PRODUCT_TOOL = {
    'revenue-leakage': 'checklist', 'pharmacy': 'checklist', 'insurance-claims': 'checklist',
    'stakeholder-action': 'formulas', 'hms': 'tools', 'diagnostics': 'glossary',
}

REQUIRED = ['slug', 'date', 'title', 'h1', 'description', 'lede', 'category', 'product', 'keywords', 'faqs']
META_RE = re.compile(r'^\s*<!--\s*(\{.*?\})\s*-->\s*', re.S)
POSTLINK_RE = re.compile(r'<a\s+href="post:([a-z0-9-]+)"\s*>(.*?)</a>', re.S)


def esc(s):
    return html.escape(s, quote=True)


def load_posts():
    posts = []
    for f in sorted(os.listdir(POSTS_DIR)):
        if not f.endswith('.html'):
            continue
        raw = open(os.path.join(POSTS_DIR, f), encoding='utf-8').read()
        m = META_RE.match(raw)
        if not m:
            sys.exit(f'{f}: missing JSON front matter comment')
        try:
            meta = json.loads(m.group(1))
        except json.JSONDecodeError as e:
            sys.exit(f'{f}: bad JSON front matter: {e}')
        missing = [k for k in REQUIRED if not meta.get(k)]
        if missing:
            sys.exit(f'{f}: missing {missing}')
        if meta['slug'] + '.html' != f:
            sys.exit(f'{f}: slug does not match file name')
        if meta['product'] not in PRODUCTS:
            sys.exit(f'{f}: unknown product {meta["product"]}')
        dt.date.fromisoformat(meta['date'])
        meta['body'] = raw[m.end():].strip()
        words = len(re.sub(r'<[^>]+>', ' ', meta['body']).split()) + sum(len((q['q'] + q['a']).split()) for q in meta['faqs'])
        meta['words'] = words
        meta['minutes'] = max(3, round(words / 220))
        posts.append(meta)
    return posts


def check(posts):
    slugs = {p['slug'] for p in posts} | set(LEGACY)
    problems = []
    for p in posts:
        s = p['slug']
        if len(p['title']) > 62:
            problems.append(f'{s}: title {len(p["title"])} chars')
        if not 110 <= len(p['description']) <= 160:
            problems.append(f'{s}: description {len(p["description"])} chars')
        if p['words'] < 1100:
            problems.append(f'{s}: only {p["words"]} words')
        if '<h1' in p['body'] or 'Frequently asked' in p['body']:
            problems.append(f'{s}: body must not contain h1/FAQ section')
        if '$' in p['body'] or 'USD' in p['body']:
            problems.append(f'{s}: dollar amount found')
        for t in POSTLINK_RE.findall(p['body']):
            if t[0] not in slugs:
                problems.append(f'{s}: post link to unknown slug {t[0]}')
        for r in p.get('related', []):
            if r not in slugs:
                problems.append(f'{s}: related unknown slug {r}')
        for href in re.findall(r'href="([^"]+)"', p['body']):
            if href.startswith(('post:', 'http', 'mailto:', '#')):
                continue
            target = os.path.normpath(os.path.join(ROOT, 'blog', href.split('#')[0]))
            if href.endswith('/'):
                target = os.path.join(target, 'index.html')
            if not os.path.exists(target):
                problems.append(f'{s}: broken link {href}')
        if len(p['faqs']) < 3:
            problems.append(f'{s}: needs at least 3 FAQs')
        tk = p.get('takeaways')
        if tk is not None:
            if not 3 <= len(tk) <= 4:
                problems.append(f'{s}: takeaways must have 3-4 bullets')
            for t in tk:
                if not 50 <= len(t) <= 190:
                    problems.append(f'{s}: takeaway length {len(t)}: {t[:40]}')
    return problems


def fmt_date(d):
    return dt.date.fromisoformat(d).strftime('%b %-d, %Y')


def resolve_links(body, live):
    def sub(m):
        slug, text = m.group(1), m.group(2)
        return f'<a href="{slug}.html">{text}</a>' if slug in live else text
    body = POSTLINK_RE.sub(sub, body)
    return re.sub(r'(<table>.*?</table>)', r'<div class="table-scroll">\1</div>', body, flags=re.S)


def card(slug, title, tag, desc, minutes, prefix=''):
    meta = f'<div class="post-meta"><span>{minutes} min read</span></div>' if minutes else ''
    return (f'<article class="post-card" data-cat="{esc(tag)}"><div class="pc-body"><span class="post-tag">{esc(tag)}</span>'
            f'<h2><a href="{prefix}{slug}.html">{esc(title)}</a></h2><p>{esc(desc)}</p>{meta}</div></article>')


def pick_related(p, live_posts):
    by_slug = {q['slug']: q for q in live_posts}
    chosen = [r for r in p.get('related', []) if r in by_slug or r in LEGACY]
    for q in sorted(live_posts, key=lambda q: q['date'], reverse=True):
        if q['slug'] != p['slug'] and q['slug'] not in chosen and (q['product'] == p['product'] or q['category'] == p['category']):
            chosen.append(q['slug'])
    for s, v in LEGACY.items():
        if s not in chosen and v[2] == p['product']:
            chosen.append(s)
    for s in LEGACY:
        if s not in chosen:
            chosen.append(s)
    out = []
    for s in chosen[:3]:
        if s in by_slug:
            q = by_slug[s]
            out.append(card(s, q['h1'], q['category'], q['description'], q['minutes']))
        else:
            t, tag, _, _, desc = LEGACY[s]
            out.append(card(s, t, tag, desc, None))
    return '\n'.join(out)


def slugify(text):
    text = html.unescape(re.sub(r'<[^>]+>', '', text)).lower()
    return re.sub(r'[^a-z0-9]+', '-', text).strip('-')[:60].strip('-') or 'section'


def add_heading_ids(body):
    """Give every <h2> a stable id (for deep links and the table of contents)."""
    toc, used = [], set()

    def sub(m):
        attrs, inner = m.group(1), m.group(2)
        found = re.search(r'id="([^"]+)"', attrs)
        hid = found.group(1) if found else slugify(inner)
        base, n = hid, 2
        while hid in used:
            hid, n = f'{base}-{n}', n + 1
        used.add(hid)
        toc.append((hid, html.unescape(re.sub(r'<[^>]+>', '', inner)).strip()))
        return m.group(0) if found else f'<h2 id="{hid}"{attrs}>{inner}</h2>'
    return re.sub(r'<h2([^>]*)>(.*?)</h2>', sub, body, flags=re.S), toc


def toc_html(toc):
    items = ''.join(f'<li><a href="#{hid}">{esc(text)}</a></li>' for hid, text in toc)
    return (f'<details class="toc" id="toc"><summary>On this page</summary>'
            f'<ol>{items}</ol></details>')


def takeaways_html(items):
    if not items:
        return ''
    lis = ''.join(f'<li>{esc(t)}</li>' for t in items)
    return f'<section class="takeaways" aria-labelledby="key-takeaways"><h2 id="key-takeaways">Key takeaways</h2><ul>{lis}</ul></section>'


def tool_for(p):
    key = p.get('tool', POST_TOOL.get(p['slug'], PRODUCT_TOOL.get(p['product'])))
    return TOOLS.get(key) if key else None


def insert_tool_promo(body, tool):
    """Place the free-tool card before the third section, once the reader is invested."""
    if not tool:
        return body
    path, title, pitch, label = tool
    starts = [m.start() for m in re.finditer(r'<h2[ >]', body)]
    if len(starts) < 4:
        return body
    promo = (f'<a class="inline-tool" data-event="tool_promo_clicked" href="../{path}"><span class="it-tag">Free tool</span>'
             f'<b>{esc(title)}</b><span class="it-pitch">{esc(pitch)}</span><em>{esc(label)} &rarr;</em></a>\n')
    return body[:starts[2]] + promo + body[starts[2]:]


def jsonld(obj):
    return '<script type="application/ld+json">\n' + json.dumps(obj, ensure_ascii=False, indent=2) + '\n</script>'


def render(p, live_posts, live_slugs, template, today):
    url = f'{SITE}/blog/{p["slug"]}.html'
    prod_path, prod_label, cta_h, cta_p = PRODUCTS[p['product']]
    posting = {
        "@context": "https://schema.org", "@type": "BlogPosting",
        "headline": p['h1'], "description": p['description'],
        "image": SITE + "/images/og-shucon-medai.jpg",
        "datePublished": p['date'], "dateModified": p.get('modified', p['date']),
        "inLanguage": "en-IN", "articleSection": p['category'],
        "keywords": ', '.join(p['keywords']), "wordCount": p['words'],
        "timeRequired": f"PT{p['minutes']}M", "isAccessibleForFree": True,
        "author": AUTHOR,
        "publisher": {"@type": "Organization", "@id": SITE + "/#organization", "name": "Shucon MedAI",
                      "logo": {"@type": "ImageObject", "url": SITE + "/images/logo-bg.png"}},
        "mainEntityOfPage": {"@type": "WebPage", "@id": url},
        "about": {"@type": "Thing", "name": p['keywords'][0]},
    }
    crumbs = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "Home", "item": SITE + "/"},
        {"@type": "ListItem", "position": 2, "name": "Blog", "item": SITE + "/blog/"},
        {"@type": "ListItem", "position": 3, "name": p.get('breadcrumb', p['title']), "item": url}]}
    faq = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": q['q'], "acceptedAnswer": {"@type": "Answer", "text": q['a']}} for q in p['faqs']]}
    faq_html = '<h2 id="faq">Frequently asked questions</h2>\n' + '\n'.join(
        f'<h3>{esc(q["q"])}</h3>\n<p>{esc(q["a"])}</p>' for q in p['faqs'])
    cta = (f'<div class="cta-band"><h3>{esc(cta_h)}</h3><p>{esc(cta_p)}</p>'
           f'<a class="btn btn-primary" data-event="demo_clicked" href="../#contact">Book a 30-minute demo</a>'
           f'<a class="text-link" href="../{prod_path}">Explore {esc(prod_label.lower())}</a></div>')
    modified = p.get('modified', p['date'])
    if p.get('takeaways'):
        posting['abstract'] = ' '.join(p['takeaways'])
    body, toc = add_heading_ids(resolve_links(p['body'], live_slugs))
    tool = tool_for(p)
    body = insert_tool_promo(body, tool)
    toc.append(('faq', 'Frequently asked questions'))
    r_path, r_title, r_pitch, r_label = tool or (prod_path, prod_label, cta_p, 'Explore')
    rail_card = (f'<a class="rail-card" data-event="rail_card_clicked" href="../{r_path}"><small>{"Free tool" if tool else "From Shucon MedAI"}</small>'
                 f'<b>{esc(r_title)}</b><span>{esc(r_pitch)}</span><em>{esc(r_label)} &rarr;</em></a>')
    updated = (f'<span class="dot"></span><span>Updated <time datetime="{modified}">{fmt_date(modified)}</time></span>'
               if modified != p['date'] else '')
    vals = {
        'TAKEAWAYS': takeaways_html(p.get('takeaways')), 'TOC': toc_html(toc), 'RAIL_CARD': rail_card, 'UPDATED': updated,
        'TITLE': esc(p['title']), 'DESCRIPTION': esc(p['description']),
        'KEYWORDS': esc(', '.join(p['keywords'])), 'URL': url, 'DATE': p['date'],
        'MODIFIED': p.get('modified', p['date']), 'CATEGORY': esc(p['category']),
        'TAG': esc(p['keywords'][0]), 'OG_TITLE': esc(p.get('og_title', p['h1'])),
        'JSONLD': '\n'.join(jsonld(x) for x in (posting, crumbs, faq)),
        'H1': esc(p['h1']), 'LEDE': esc(p['lede']), 'DATE_HUMAN': fmt_date(p['date']),
        'MINUTES': str(p['minutes']), 'BODY': body,
        'FAQ': faq_html, 'CTA': cta, 'RELATED': pick_related(p, live_posts),
    }
    out = template
    for k, v in vals.items():
        out = out.replace('{{' + k + '}}', v)
    return out


def replace_block(text, name, content, path):
    start, end = f'<!-- AUTO:{name}:START -->', f'<!-- AUTO:{name}:END -->'
    i, j = text.find(start), text.find(end)
    if i == -1 or j == -1:
        sys.exit(f'{path}: missing {name} markers')
    return text[:i + len(start)] + '\n' + content + '\n' + text[j:]


def update_blog_index(text, live_posts):
    cards = '\n'.join(card(p['slug'], p['h1'], p['category'], p['description'], p['minutes'])
                      for p in sorted(live_posts, key=lambda p: p['date'], reverse=True))
    text = replace_block(text, 'BLOG-CARDS', cards, 'blog/index.html')
    m = re.search(r'(<script type="application/ld\+json">\s*)(\{.*?"@type": "Blog".*?\})(\s*</script>)', text, re.S)
    blog = json.loads(m.group(2))
    auto_urls = {f'{SITE}/blog/{p["slug"]}.html' for p in load_all_slugs()}
    kept = [b for b in blog['blogPost'] if b['url'] not in auto_urls]
    author = {"@type": "Person", "name": "Saksham Gupta", "url": AUTHOR['url'], "sameAs": AUTHOR['sameAs'][0]}
    new = [{"@type": "BlogPosting", "headline": p['h1'], "url": f'{SITE}/blog/{p["slug"]}.html',
            "datePublished": p['date'], "author": author}
           for p in sorted(live_posts, key=lambda p: p['date'], reverse=True)]
    blog['blogPost'] = new + kept
    return text[:m.start(2)] + json.dumps(blog, ensure_ascii=False, indent=2) + text[m.end(2):]


_ALL = []


def load_all_slugs():
    return _ALL


def guides_block(items, heading, prefix):
    if not items:
        return ''
    links = ''.join(f'<li><a href="{prefix}blog/{p["slug"]}.html"><small>{esc(p["category"])} &middot; {p["minutes"]} min read</small>'
                    f'{esc(p["h1"])}</a></li>' for p in items)
    return (f'<section class="auto-guides" aria-label="{esc(heading)}"><div class="wrap">'
            f'<span class="eyebrow">Guides</span><h2 class="section-title">{esc(heading)}</h2>'
            f'<ul>{links}</ul><a class="auto-guides-all" href="{prefix}blog/">All insights &rarr;</a></div></section>')


def feed_xml(newest):
    def rfc822(d):
        return dt.datetime.fromisoformat(d).replace(hour=6, tzinfo=IST).strftime('%a, %d %b %Y %H:%M:%S %z')
    items = [(p['h1'], p['slug'], p['date'], p['description'], p['category']) for p in newest]
    items += [(t, slug, d, desc, cat) for slug, (t, cat, _, d, desc) in LEGACY.items()]
    items.sort(key=lambda i: i[2], reverse=True)
    body = ''.join(
        f'\t\t<item>\n\t\t\t<title>{esc(t)}</title>\n\t\t\t<link>{SITE}/blog/{slug}.html</link>\n'
        f'\t\t\t<guid isPermaLink="true">{SITE}/blog/{slug}.html</guid>\n\t\t\t<pubDate>{rfc822(d)}</pubDate>\n'
        f'\t\t\t<category>{esc(cat)}</category>\n\t\t\t<description>{esc(desc)}</description>\n\t\t</item>\n'
        for t, slug, d, desc, cat in items[:30])
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">\n\t<channel>\n'
            '\t\t<title>Shucon MedAI Insights</title>\n'
            f'\t\t<link>{SITE}/blog/</link>\n'
            f'\t\t<atom:link href="{SITE}/blog/feed.xml" rel="self" type="application/rss+xml"/>\n'
            '\t\t<description>Guides on hospital revenue leakage, insurance claims, hospital KPIs and healthcare AI for hospital leaders.</description>\n'
            '\t\t<language>en-IN</language>\n'
            f'\t\t<lastBuildDate>{rfc822(items[0][2])}</lastBuildDate>\n'
            f'{body}\t</channel>\n</rss>\n')


def page_url(path):
    """Public URL for a site file, or None for non-page files (sitemap, feed, llms.txt)."""
    if not path.endswith('.html'):
        return None
    if path == 'index.html' or path.endswith('/index.html'):
        path = path[:-len('index.html')]
    return f'{SITE}/{path}'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--date', help='pretend today is YYYY-MM-DD')
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--check', action='store_true', help='validate all posts and exit')
    ap.add_argument('--urls-out', help='write the URLs of changed pages to this file (for IndexNow)')
    a = ap.parse_args()
    today = a.date or dt.datetime.now(IST).date().isoformat()

    posts = load_posts()
    _ALL.extend(posts)
    problems = check(posts)
    if a.check:
        print('\n'.join(problems) or f'OK: {len(posts)} posts valid')
        sys.exit(1 if problems else 0)
    for pr in problems:
        print('WARN', pr)

    live = [p for p in posts if p['date'] <= today]
    live_slugs = {p['slug'] for p in live} | set(LEGACY)
    template = open(os.path.join(ROOT, '_scheduled', 'template.html'), encoding='utf-8').read()
    writes = {}

    for p in live:
        writes[f'blog/{p["slug"]}.html'] = render(p, live, live_slugs, template, today)
    # Unpublish anything whose date was moved into the future
    removes = [f'blog/{p["slug"]}.html' for p in posts if p['date'] > today
               and os.path.exists(os.path.join(ROOT, 'blog', p['slug'] + '.html'))]

    def edit(path, fn):
        full = os.path.join(ROOT, path)
        cur = writes.get(path) or open(full, encoding='utf-8').read()
        writes[path] = fn(cur)

    edit('blog/index.html', lambda t: update_blog_index(t, live))

    newest = sorted(live, key=lambda p: p['date'], reverse=True)
    sm = ''.join(f'\t<url>\n\t\t<loc>{SITE}/blog/{p["slug"]}.html</loc>\n\t\t<lastmod>{p.get("modified", p["date"])}</lastmod>\n'
                 f'\t\t<changefreq>monthly</changefreq>\n\t\t<priority>0.7</priority>\n\t</url>\n' for p in newest).rstrip('\n')
    edit('sitemap.xml', lambda t: replace_block(t, 'SITEMAP', sm, 'sitemap.xml'))

    llm = '\n'.join(f'- [{p["h1"]}]({SITE}/blog/{p["slug"]}.html): {p["description"]}' for p in newest)
    edit('llms.txt', lambda t: replace_block(t, 'LLMS', llm, 'llms.txt'))

    writes['blog/feed.xml'] = feed_xml(newest)

    edit('index.html', lambda t: replace_block(t, 'HOME-GUIDES', guides_block(newest[:6], 'Latest guides for hospital leaders', ''), 'index.html'))

    for page, prods in PRODUCT_PAGES.items():
        items = [p for p in newest if p['product'] in prods][:6]
        prefix = '../' * page.count('/')
        edit(page, lambda t, items=items, prefix=prefix, page=page: replace_block(t, 'GUIDES', guides_block(items, 'Related guides', prefix), page))

    for slug, (_, _, prod, _, _) in LEGACY.items():
        items = [p for p in newest if p['product'] == prod][:4] or newest[:4]
        links = ''.join(f'<li><a href="{p["slug"]}.html">{esc(p["h1"])}</a></li>' for p in items)
        block = f'<div class="more-guides"><h2>More guides on this topic</h2><ul>{links}</ul></div>' if items else ''
        edit(f'blog/{slug}.html', lambda t, block=block, slug=slug: replace_block(t, 'MORE-GUIDES', block, slug))

    changed = []
    for path, content in writes.items():
        full = os.path.join(ROOT, path)
        old = open(full, encoding='utf-8').read() if os.path.exists(full) else None
        if old != content:
            changed.append(path)
            if not a.dry_run:
                open(full, 'w', encoding='utf-8').write(content)
    for path in removes:
        changed.append('removed ' + path)
        if not a.dry_run:
            os.remove(os.path.join(ROOT, path))
    if a.urls_out:
        urls = [page_url(c.replace('removed ', '')) for c in changed]
        urls = [u for u in urls if u]
        if urls:
            urls += [SITE + '/blog/', SITE + '/sitemap.xml']
        with open(a.urls_out, 'w', encoding='utf-8') as f:
            f.write(''.join(u + '\n' for u in dict.fromkeys(urls)))
    print(f'today={today} live={len(live)}/{len(posts)} changed={len(changed)}')
    for c in changed:
        print('  ', c)


if __name__ == '__main__':
    main()
