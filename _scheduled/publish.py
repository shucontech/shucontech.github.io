#!/usr/bin/env python3
"""Publish scheduled blog posts whose go-live date has arrived.

Each run (idempotent):
  * renders every post in _scheduled/posts/ with date <= today (IST) to blog/<slug>.html
  * resolves <a href="post:slug"> links (linked once the target is live, plain text before)
  * rebuilds auto-managed blocks: blog listing + Blog JSON-LD, sitemap, llms.txt,
    homepage "latest guides", product-page "guides" and legacy-post "more guides"

Usage: python3 _scheduled/publish.py [--date YYYY-MM-DD] [--dry-run] [--check]
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
    return (f'<article class="post-card"><div class="pc-body"><span class="post-tag">{esc(tag)}</span>'
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
    faq_html = '<h2>Frequently asked questions</h2>\n' + '\n'.join(
        f'<h3>{esc(q["q"])}</h3>\n<p>{esc(q["a"])}</p>' for q in p['faqs'])
    cta = (f'<div class="cta-band"><h3>{esc(cta_h)}</h3><p>{esc(cta_p)}</p>'
           f'<a class="btn btn-primary" data-event="demo_clicked" href="../#contact">Book a 30-minute demo</a>'
           f'<a class="text-link" href="../{prod_path}">Explore {esc(prod_label.lower())}</a></div>')
    vals = {
        'TITLE': esc(p['title']), 'DESCRIPTION': esc(p['description']),
        'KEYWORDS': esc(', '.join(p['keywords'])), 'URL': url, 'DATE': p['date'],
        'MODIFIED': p.get('modified', p['date']), 'CATEGORY': esc(p['category']),
        'TAG': esc(p['keywords'][0]), 'OG_TITLE': esc(p.get('og_title', p['h1'])),
        'JSONLD': '\n'.join(jsonld(x) for x in (posting, crumbs, faq)),
        'H1': esc(p['h1']), 'LEDE': esc(p['lede']), 'DATE_HUMAN': fmt_date(p['date']),
        'MINUTES': str(p['minutes']), 'BODY': resolve_links(p['body'], live_slugs),
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
    links = ''.join(f'<li><a href="{prefix}blog/{p["slug"]}.html">{esc(p["h1"])}</a></li>' for p in items)
    return (f'<section class="auto-guides" aria-label="{esc(heading)}"><div class="wrap">'
            f'<span class="eyebrow">Guides</span><h2 class="section-title">{esc(heading)}</h2>'
            f'<ul>{links}</ul><a class="auto-guides-all" href="{prefix}blog/">All insights &rarr;</a></div></section>')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--date', help='pretend today is YYYY-MM-DD')
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--check', action='store_true', help='validate all posts and exit')
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
    print(f'today={today} live={len(live)}/{len(posts)} changed={len(changed)}')
    for c in changed:
        print('  ', c)


if __name__ == '__main__':
    main()
