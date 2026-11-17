#!/usr/bin/env python3
"""Build the site: wrap each page body in src/pages/ with the shared layout.

    python3 tools/build.py            # writes production pages to the repo root
    python3 tools/build.py --out DIR  # writes to DIR instead
    python3 tools/build.py --html-links   # keep ".html" in internal links (local previews)

No dependencies. Edit src/pages/*.html, run this, commit the result.
"""
from __future__ import annotations

import argparse
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src" / "pages"
SITE = "https://bluemindmi.com"

REPLY = {"referral": "two business days", "application": "three business days", "message": "one business day"}

# The only server the site talks to (forms, chat, status). It is also the CSP connect-src.
API_ORIGIN = "https://bluemind-dashboard-production.up.railway.app"

ORG = {
    "name": "BlueMind Therapy",
    "legal": "BlueMind Therapy LLC",
    "phone": "(734) 252-5215",
    "phone_href": "tel:+17342525215",
    "phone_e164": "+1-734-252-5215",
    "email": "info@bluemindmi.com",
    "careers_email": "hr@bluemindmi.com",
    "instagram": "https://www.instagram.com/bluemindtherapymi/",
    "dashboard": API_ORIGIN + "/login",
}

CENTERS = [
    {
        "key": "ypsilanti", "name": "Ypsilanti", "county": "Washtenaw County",
        "street": "1122 Walnut Street", "city": "Ypsilanti", "state": "MI", "zip": "48198",
        "payer": "Washtenaw County Community Mental Health",
        "phone": "(734) 252-5215", "phone_href": "tel:+17342525215", "phone_e164": "+1-734-252-5215",
        "hours": [("Monday to Friday", "8:00 am to 8:00 pm"), ("Saturday", "8:00 am to 3:00 pm"), ("Sunday", "Closed")],
        "opening": ["Mo-Fr 08:00-20:00", "Sa 08:00-15:00"],
        "lat": 42.2443, "lng": -83.6090,
        "towns": ["Ann Arbor", "Ypsilanti Township", "Superior Township", "Pittsfield Township", "Saline", "Milan"],
        "find": "The center is on Walnut Street in Ypsilanti. Look for the BlueMind Therapy sign on the building.",
        "gallery": "reception|The lobby at our Ypsilanti center;hero|The playground at our Ypsilanti center;services|A therapy room ready for the day",
    },
    {
        "key": "dearborn", "name": "Dearborn", "county": "Wayne County",
        "street": "18800 Hubbard Drive", "city": "Dearborn", "state": "MI", "zip": "48126",
        "payer": "Detroit Wayne Integrated Health Network (DWIHN)",
        "phone": "(313) 436-0319", "phone_href": "tel:+13134360319", "phone_e164": "+1-313-436-0319",
        "photo_pos": "center 12%",
        "hours": [("Monday to Friday", "8:00 am to 8:00 pm"), ("Saturday", "8:00 am to 3:00 pm"), ("Sunday", "Closed")],
        "opening": ["Mo-Fr 08:00-20:00", "Sa 08:00-15:00"],
        "lat": 42.3157, "lng": -83.2286,
        "towns": ["Dearborn Heights", "Detroit", "Allen Park", "Melvindale", "Inkster", "Garden City"],
        "find": "The entrance is under the 18800 awning on Hubbard Drive. Look for BlueMind on the road sign.",
        "gallery": "dearborn-sign|Look for BlueMind on the sign at 18800 Hubbard Drive;services|A therapy room ready for the day",
    },
    {
        "key": "fort-gratiot", "name": "Fort Gratiot", "county": "St. Clair County",
        "street": "4435 24th Avenue", "city": "Fort Gratiot", "state": "MI", "zip": "48059",
        "payer": "St. Clair County Community Mental Health",
        "phone": "(810) 479-9375", "phone_href": "tel:+18104799375", "phone_e164": "+1-810-479-9375",
        "photo_pos": "12% center",
        "hours": [("Monday to Friday", "8:00 am to 8:00 pm"), ("Saturday", "8:00 am to 3:00 pm"), ("Sunday", "Closed")],
        "opening": ["Mo-Fr 08:00-20:00", "Sa 08:00-15:00"],
        "lat": 43.0340, "lng": -82.4530,
        "towns": ["Port Huron", "Marysville", "Kimball Township", "St. Clair", "Marine City"],
        "find": "The center is the brick building on 24th Avenue. Look for the BlueMind Therapy sign by the road.",
        "gallery": "",
    },
]


# Other languages. Each has src/i18n/<code>.json (shared texts) and src/pages-<code>/ (the
# translated pages). Pages that are not translated stay English and are linked as such.
# Owner 2026-11-17: Spanish only. No Arabic anywhere on the site.
LANGS = {"es": {"dir": "ltr", "name": "Español"}}
_T: dict = {}


def T(lang: str) -> dict:
    """Shared texts for a language, English filling any gap."""
    import json
    if lang not in _T:
        base = json.loads((ROOT / "src" / "i18n" / "en.json").read_text(encoding="utf-8"))
        f = ROOT / "src" / "i18n" / f"{lang}.json"
        if lang != "en" and f.exists():
            base.update(json.loads(f.read_text(encoding="utf-8")))
        _T[lang] = base
    return _T[lang]


def translated_slugs(lang: str) -> set:
    d = ROOT / "src" / f"pages-{lang}"
    return {f.stem for f in d.glob("*.html")} if d.exists() else set()


def lang_switch(slug: str, lang: str) -> str:
    """EN | Español. Points at the same page when that language has it, else its home."""
    def url(code: str) -> str:
        if code == "en":
            return f"/{slug}.html"
        target = slug if slug in translated_slugs(code) else "index"
        return f"/{code}/{target}.html"
    items = [("en", "EN")] + [(c, v["name"]) for c, v in LANGS.items() if translated_slugs(c)]
    if len(items) == 1:
        return ""
    links = "".join(
        f'<a href="{url(c)}" lang="{c}" hreflang="{c}"' + (' aria-current="true"' if c == lang else "") + f'>{label}</a>'
        for c, label in items
    )
    return f'<div class="lang-switch" role="group" aria-label="Language">{links}</div>'


def localize_links(html: str, lang: str) -> str:
    """Inside a translated page: internal links go to the translated page when
    there is one, else to the English page; assets and photos become root paths
    because the page lives one folder down. (No <base>: it breaks the SVG icons.)"""
    have = translated_slugs(lang)
    def fix(m):
        slug, rest = m.group(1), m.group(2) or ""
        return f'href="/{lang}/{slug}.html{rest}"' if slug in have else f'href="/{slug}.html{rest}"'
    html = re.sub(r'href="([a-z0-9-]+)\.html([#?][^"]*)?"', fix, html)
    return re.sub(r'(src|href)="(assets|photos)/', r'\1="/\2/', html)


def maps_url(c: dict) -> str:
    q = f"{c['street']} {c['city']} {c['state']} {c['zip']}".replace(" ", "+")
    return f"https://www.google.com/maps/search/?api=1&query={q}"


ICONS = {
    "home": '<path d="M3 10.5 12 3l9 7.5"/><path d="M5 9.5V21h14V9.5"/><path d="M10 21v-6h4v6"/>',
    "building": '<rect x="4" y="3" width="16" height="18" rx="2"/><path d="M9 7h2M13 7h2M9 11h2M13 11h2M9 15h2M13 15h2M10 21v-3h4v3"/>',
    "school": '<path d="M3 10 12 5l9 5-9 5-9-5z"/><path d="M7 12.5V17c0 1.5 2.5 3 5 3s5-1.5 5-3v-4.5"/><path d="M21 10v5"/>',
    "family": '<circle cx="9" cy="7" r="3"/><circle cx="17" cy="9" r="2.2"/><path d="M3 20v-2a5 5 0 0 1 5-5h2a5 5 0 0 1 5 5v2"/><path d="M16 14h1a4 4 0 0 1 4 4v2"/>',
    "clipboard": '<rect x="5" y="4" width="14" height="17" rx="2"/><path d="M9 4V2.5h6V4"/><path d="M9 10h6M9 14h6M9 18h3"/>',
    "badge": '<path d="M12 2.5 15 5l4 .5.5 4L22 12l-2.5 2.5-.5 4-4 .5-3 2.5-3-2.5-4-.5-.5-4L2 12l2.5-2.5.5-4L9 5z"/><path d="m9 12 2 2 4-4"/>',
    "phone": '<path d="M5 3h4l2 5-2.5 1.5a11 11 0 0 0 6 6L16 13l5 2v4a2 2 0 0 1-2 2A16 16 0 0 1 3 5a2 2 0 0 1 2-2z"/>',
    "mail": '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="m3 7 9 6 9-6"/>',
    "pin": '<path d="M12 21s7-6.5 7-11.5a7 7 0 0 0-14 0C5 14.5 12 21 12 21z"/><circle cx="12" cy="9.5" r="2.5"/>',
    "clock": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    "check": '<path d="M20 6 9 17l-5-5"/>',
    "arrow": '<path d="M5 12h14M13 6l6 6-6 6"/>',
    "instagram": '<rect x="3" y="3" width="18" height="18" rx="5"/><circle cx="12" cy="12" r="4"/><circle cx="17.5" cy="6.5" r="1" fill="currentColor" stroke="none"/>',
    "menu": '<path d="M4 7h16M4 12h16M4 17h16"/>',
    "heart": '<path d="M12 20s-7-4.5-7-10a4 4 0 0 1 7-2.5A4 4 0 0 1 19 10c0 5.5-7 10-7 10z"/>',
    "chat": '<path d="M4 5h16v11H8l-4 4z"/>',
    "briefcase": '<rect x="3" y="7" width="18" height="13" rx="2"/><path d="M9 7V5h6v2M3 12h18"/>',
    "map": '<path d="M3 6l6-2 6 2 6-2v14l-6 2-6-2-6 2z"/><path d="M9 4v14M15 6v14"/>',
    "video": '<rect x="3" y="6" width="13" height="12" rx="2"/><path d="m16 10 5-3v10l-5-3"/>',
    "chart": '<path d="M4 20V10M10 20V4M16 20v-8M22 20H2"/>',
    "shield": '<path d="M12 3 4 6v6c0 5 3.5 8 8 9 4.5-1 8-4 8-9V6z"/><path d="m9 12 2 2 4-4"/>',
    "star": '<path d="m12 3 2.7 5.6 6.1.9-4.4 4.3 1 6.1L12 17l-5.4 2.9 1-6.1L3.2 9.5l6.1-.9z"/>',
    "cctv": '<path d="M3 5h18"/><path d="M6 5v3.5a6 6 0 0 0 12 0V5"/><circle cx="12" cy="9" r="2.2"/><path d="M12 14.5V19"/><path d="M8.5 19h7"/>',
    "lock": '<rect x="5" y="11" width="14" height="10" rx="2.2"/><path d="M8 11V8a4 4 0 0 1 8 0v3"/><circle cx="12" cy="16" r="1.3"/>',
    "id-check": '<rect x="3" y="5" width="18" height="14" rx="2"/><circle cx="8.5" cy="11" r="2"/><path d="M5.5 16c.5-1.6 1.6-2.4 3-2.4s2.5.8 3 2.4"/><path d="m14 11 1.5 1.5L18.5 9.5"/><path d="M14 15h4.5"/>',
    "eye": '<path d="M2.5 12s3.5-6 9.5-6 9.5 6 9.5 6-3.5 6-9.5 6-9.5-6-9.5-6z"/><circle cx="12" cy="12" r="2.6"/>',
    "send": '<path d="M4 12 20 4l-4 16-4-7z"/><path d="m12 13 8-9"/>',
    "check2": '<path d="m2 12 4 4L13 9"/><path d="m11 16 9-9"/>',
    "close": '<path d="M6 6l12 12M18 6 6 18"/>',
    "sun": '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>',
}

PUZZLE = "M20,20 H45 a8,8 0 1 1 16,0 H86 V45 a8,8 0 1 1 0,16 V86 H61 a8,8 0 1 0 -16,0 H20 V61 a8,8 0 1 0 0,-16 Z"


def sprite() -> str:
    syms = "".join(
        f'<symbol id="i-{k}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round">{v}</symbol>'
        for k, v in ICONS.items()
    )
    syms += f'<symbol id="i-puzzle" viewBox="0 0 106 106"><path d="{PUZZLE}" fill="currentColor"/></symbol>'
    return f'<svg width="0" height="0" style="position:absolute" aria-hidden="true" focusable="false">{syms}</svg>'


def icon(name: str, cls: str = "") -> str:
    classes = ("ic " + cls).strip()
    return f'<svg class="{classes}" aria-hidden="true" focusable="false"><use href="#i-{name}"/></svg>'


def art(name: str, label: str, variant: str = "a") -> str:
    """Illustrated panel used until a real photo is dropped into photos/."""
    variants = {
        "a": (0, "#0B3C8C", "#5AA9E6", "#FFFFFF"),
        "b": (12, "#1E5BD8", "#FFFFFF", "#5AA9E6"),
        "c": (-10, "#5AA9E6", "#0B3C8C", "#FFFFFF"),
    }
    rot, c1, c2, c3 = variants.get(variant, variants["a"])
    gid = f"g-{name}"
    return (
        f'<div class="art"><svg viewBox="0 0 800 600" role="img" aria-label="{label}">'
        f'<defs><linearGradient id="{gid}" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#EBF3FC"/><stop offset="1" stop-color="#BFE0F7"/></linearGradient></defs>'
        f'<rect width="800" height="600" fill="url(#{gid})"/>'
        f'<circle cx="650" cy="130" r="180" fill="#FFFFFF" opacity=".55"/>'
        f'<circle cx="140" cy="500" r="220" fill="#5AA9E6" opacity=".28"/>'
        f'<g transform="translate(290 150) rotate({rot}) scale(2.3)" opacity=".95"><g class="fp"><path d="{PUZZLE}" fill="{c1}"/></g></g>'
        f'<g transform="translate(470 300) rotate({rot + 18}) scale(1.6)" opacity=".9"><g class="fp fp2"><path d="{PUZZLE}" fill="{c2}"/></g></g>'
        f'<g transform="translate(150 110) rotate({rot - 22}) scale(1.25)" opacity=".9"><g class="fp fp3"><path d="{PUZZLE}" fill="{c3}"/></g></g>'
        f'<circle cx="690" cy="470" r="28" fill="#F5B52B"/>'
        f'</svg></div>'
    )


def photo(name: str, label: str, cls: str = "", variant: str = "a", eager: bool = False, pos: str = "") -> str:
    loading = "eager" if eager else "lazy"
    priority = ' fetchpriority="high"' if eager else ""
    style = f' style="object-position:{pos}"' if pos else ""
    return (
        f'<div class="photo {cls}"><img src="photos/{name}.jpg" alt="{label}" loading="{loading}"{priority} decoding="async"{style}>'
        f'{art(name, label, variant)}</div>'
    )


SAFETY = [
    ("cctv", "24/7", "Cameras record every room, 24 hours a day", "Cámaras graban cada sala las 24 horas"),
    ("lock", "", "Locked doors. Only staff and checked-in families enter", "Puertas con cerradura. Solo entran el personal y las familias registradas"),
    ("id-check", "", "Every team member passes background checks", "Todo el personal pasa verificación de antecedentes"),
    ("eye", "", "A BCBA supervises every child's program", "Un BCBA supervisa el programa de cada niño"),
]


def safety_block(lang: str = "en") -> str:
    t = T(lang)
    banner = (
        '<figure class="safety-photo">'
        + photo("cameras", t["safety_alt"], "wide")
        + f'<figcaption><strong>{t["safety_caption_strong"]}</strong> {t["safety_caption"]}</figcaption>'
        '</figure>'
    )
    cards = ""
    for name, badge, en, es in SAFETY:
        badge_html = f'<span class="safety-badge">{badge}</span>' if badge else ""
        cards += (
            '<li class="safety-card">'
            f'<div class="safety-icon">{icon(name)}{badge_html}</div>'
            f'<p class="safety-en">{en}</p>'
            f'<p class="safety-l" lang="es">{es}</p>'
            '</li>'
        )
    return banner + f'<ul class="safety clean">{cards}</ul>'


def gallery(spec: str, label: str = "Photos of our centers") -> str:
    """{{gallery:name|caption;name|caption;...}} -> a swipeable photo gallery.
    Slides whose photo is missing remove themselves (site.js)."""
    slides = ""
    items = [s for s in spec.split(";") if s.strip()]
    for i, item in enumerate(items):
        name, _, caption = item.partition("|")
        name, caption = name.strip(), caption.strip()
        loading = "eager" if i == 0 else "lazy"
        slides += (
            f'<figure class="gallery-slide" data-index="{i}">'
            f'<img src="photos/{name}.jpg" alt="{caption}" loading="{loading}" decoding="async">'
            f'<figcaption>{caption}</figcaption></figure>'
        )
    return (
        f'<div class="gallery" aria-roledescription="carousel" aria-label="{label}">'
        f'<div class="gallery-track" tabindex="0" aria-live="polite">{slides}</div>'
        f'<button type="button" class="gallery-btn prev" aria-label="Previous photo"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m15 5-7 7 7 7"/></svg></button>'
        f'<button type="button" class="gallery-btn next" aria-label="Next photo"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m9 5 7 7-7 7"/></svg></button>'
        f'<div class="gallery-dots" role="tablist" aria-label="Choose a photo"></div>'
        f'<div class="gallery-count" aria-hidden="true"></div>'
        '</div>'
    )


def phone_list(cls: str = "") -> str:
    """One line per center: name + its direct number."""
    items = "".join(
        f'<li><span>{c["name"]}</span><a href="{c["phone_href"]}">{c["phone"]}</a></li>' for c in CENTERS
    )
    klass = ("phone-list " + cls).strip()
    return f'<ul class="{klass}">{items}</ul>'


def center_card(c: dict, with_photo: bool = False, detailed: bool = False, lang: str = "en") -> str:
    t = T(lang)
    words = {
        "Monday to Friday": t["day_weekdays"], "Saturday": t["day_saturday"], "Sunday": t["day_sunday"], "Closed": t["closed"],
        "8:00 am to 8:00 pm": t["hours_weekday"], "8:00 am to 3:00 pm": t["hours_saturday"],
        "Washtenaw County": t["county_washtenaw"], "Wayne County": t["county_wayne"], "St. Clair County": t["county_st_clair"],
    }
    hours = "".join(f"<tr><td>{words.get(d, d)}</td><td>{words.get(h, h)}</td></tr>" for d, h in c["hours"])
    photo_html = photo(c["key"], t["photo_center_alt"].format(name=c["name"]), "wide", pos=c.get("photo_pos", "")) if with_photo else ""
    details = (
        f'<p class="muted small" style="margin:0.5rem 0 0">{t["card_medicaid"]} {c["payer"]}</p>'
        f'<table class="hours-table" style="margin-top:0.75rem"><tbody>{hours}</tbody></table>'
        if detailed else ""
    )
    return (
        f'<div class="card center-card" id="{c["key"]}">{photo_html}'
        f'<div class="county">{words.get(c["county"], c["county"])}</div>'
        f'<h3 style="margin:0">{c["name"]}</h3>'
        f'<address>{c["street"]}<br>{c["city"]}, {c["state"]} {c["zip"]}</address>'
        f'{details}'
        f'<div class="links"><a href="{maps_url(c)}" target="_blank" rel="noopener">{t["card_directions"]}</a>'
        f'<a href="{c["phone_href"]}">{t["card_call"]} <span dir="ltr">{c["phone"]}</span></a>'
        + (f'<a href="{center_slug(c)}.html">{t["card_about"].format(name=c["name"])}</a>'
           f'<a href="refer.html?center={c["name"].replace(" ", "+")}">{t["card_refer"]}</a>' if detailed else "")
        + '</div></div>'
    )


def center_slug(c: dict) -> str:
    """One page per center, named for what families search: "ABA therapy Dearborn"."""
    return f"aba-therapy-{c['key']}"


def center_faq(c: dict) -> list[tuple[str, str]]:
    hours = "; ".join(f"{d} {h}" for d, h in c["hours"])
    return [
        (f"Where is the BlueMind Therapy center in {c['name']}?",
         f"{c['street']}, {c['city']}, {c['state']} {c['zip']}. {c['find']} Parking is free."),
        (f"What insurance does the {c['name']} center take?",
         f"Medicaid through {c['payer']}, Blue Cross Blue Shield of Michigan, HAP and UnitedHealthcare, and private pay. Call {c['phone']} and we will check your plan with you."),
        ("What ages do you work with?",
         "Children and teens from 12 months to 18 years with an autism spectrum diagnosis."),
        (f"What are the hours at the {c['name']} center?", f"{hours}."),
        ("Do you come to our home or school?",
         f"Yes. In-home, school and community sessions are scheduled from this center across {c['county']}."),
        ("How do we get started?",
         f"Send a referral online or call {c['phone']}. Our intake team calls the parent or guardian within {REPLY['referral']}, confirms the diagnosis and insurance, and requests authorization. Then a BCBA schedules the assessment."),
    ]


def center_json_ld(c: dict) -> str:
    import json
    data = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "MedicalBusiness",
                "name": f"BlueMind Therapy {c['name']}",
                "parentOrganization": {"@type": "Organization", "name": ORG["legal"], "url": SITE},
                "url": f"{SITE}/{center_slug(c)}",
                "telephone": c["phone_e164"],
                "email": ORG["email"],
                "address": {
                    "@type": "PostalAddress", "streetAddress": c["street"], "addressLocality": c["city"],
                    "addressRegion": c["state"], "postalCode": c["zip"], "addressCountry": "US",
                },
                "geo": {"@type": "GeoCoordinates", "latitude": c["lat"], "longitude": c["lng"]},
                "areaServed": [c["county"], *c["towns"]],
                "openingHours": c["opening"],
                "medicalSpecialty": "Behavioral health",
                "image": f"{SITE}/photos/{c['key']}.jpg",
            },
            {
                "@type": "FAQPage",
                "mainEntity": [
                    {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}}
                    for q, a in center_faq(c)
                ],
            },
        ],
    }
    return f'<script type="application/ld+json">{json.dumps(data, separators=(",", ":"))}</script>'


def center_page(c: dict) -> tuple[dict, str]:
    """(front matter, body) for a center's own page. Built from CENTERS so the
    address, phone and hours can never drift from the rest of the site."""
    name, county = c["name"], c["county"]
    towns = ", ".join(c["towns"][:-1]) + " and " + c["towns"][-1]
    hours = "".join(f"<tr><td>{d}</td><td>{h}</td></tr>" for d, h in c["hours"])
    refer = f'refer.html?center={name.replace(" ", "+")}'
    faq = "".join(f"<details><summary>{q}</summary><p>{a}</p></details>" for q, a in center_faq(c))
    others = "".join(
        f'<a class="btn btn-secondary" href="{center_slug(o)}.html">{o["name"]}</a>' for o in CENTERS if o is not c
    )
    extra = (
        f'<section class="band band-tight" aria-label="Photos of the {name} center"><div class="wrap">{gallery(c["gallery"], f"Photos of the {name} center")}</div></section>'
        if c.get("gallery") else ""
    )
    meta = {
        "title": f"ABA therapy in {name}, Michigan",
        "description": (
            f"BlueMind Therapy {name}: one-on-one ABA therapy for children and teens with autism at {c['street']}, "
            f"{c['city']}, MI, and at home and school across {county}. Medicaid through {c['payer']}. Call {c['phone']}."
        ),
        "nav": "locations",
    }
    body = f"""
<section class="page-intro"><div class="wrap">
  <p class="eyebrow">{county}</p>
  <h1>ABA therapy in {name}, Michigan</h1>
  <p class="lede">One-on-one Applied Behavior Analysis therapy for children and teens with autism, from 12 months to 18 years, at our {name} center and at home, at school and in the community across {county}.</p>
  <div class="cta-row"><a class="btn btn-primary" href="{refer}">Refer a child to {name}</a><a class="btn btn-secondary" href="{c['phone_href']}">Call {c['phone']}</a></div>
</div></section>

<section class="band band-tight" aria-labelledby="visit-h">
  <div class="wrap split" style="align-items:start">
    <div>{photo(c['key'], f"The BlueMind Therapy center in {name}", "wide", eager=True, pos=c.get("photo_pos", ""))}</div>
    <div>
      <p class="eyebrow">Visit us</p>
      <h2 id="visit-h">BlueMind Therapy {name}</h2>
      <address style="font-style:normal;font-size:1.1rem;margin:0 0 0.75rem">{c['street']}<br>{c['city']}, {c['state']} {c['zip']}</address>
      <p>{c['find']}</p>
      <table class="hours-table" style="margin:0 0 1rem"><tbody>{hours}</tbody></table>
      <ul class="checks">
        <li>{icon('check')}<span>Free parking</span></li>
        <li>{icon('check')}<span>Interpreter services arranged on request</span></li>
        <li>{icon('check')}<span>Tours for families considering BlueMind</span></li>
      </ul>
      <div class="cta-row"><a class="btn btn-primary" href="{maps_url(c)}" target="_blank" rel="noopener">Get directions</a><a class="btn btn-secondary" href="contact.html">Book a tour</a></div>
    </div>
  </div>
</section>
{extra}
<section class="band band-mist" aria-labelledby="area-h">
  <div class="wrap grid grid-3">
    <div class="card"><div class="icon">{icon('map')}</div><h3 id="area-h">Where we serve</h3>
      <p>Families come to the center in {name}. In-home, school and community sessions are scheduled from this center across {county}, including {towns}.</p></div>
    <div class="card"><div class="icon">{icon('shield')}</div><h3>Insurance</h3>
      <p>Medicaid through {c['payer']}, Blue Cross Blue Shield of Michigan, HAP and UnitedHealthcare, and private pay. For Medicaid members we bill the county program directly.</p></div>
    <div class="card"><div class="icon">{icon('heart')}</div><h3>What we offer here</h3>
      <p>Assessment by a BCBA, one-on-one ABA therapy, parent training, and coordination with your child's school. <a href="services.html">See all services</a>.</p></div>
  </div>
</section>

<section class="band" aria-labelledby="safe-h">
  <div class="wrap">
    <div class="section-head center" style="margin-inline:auto"><p class="eyebrow">Safe by design</p><h2 id="safe-h">The same protections at every center</h2></div>
    {safety_block()}
  </div>
</section>

<section class="band band-mist" aria-labelledby="faq-h">
  <div class="wrap">
    <div class="section-head"><p class="eyebrow">{name}</p><h2 id="faq-h">Questions families in {county} ask</h2></div>
    <div class="faq">{faq}</div>
  </div>
</section>

<section class="band band-tight" aria-label="Our other centers">
  <div class="wrap" style="text-align:center">
    <p class="eyebrow">Our other centers</p>
    <div class="cta-row" style="justify-content:center">{others}<a class="btn btn-secondary" href="locations.html">All locations</a></div>
  </div>
</section>
"""
    return meta, body


JOBS = [
    {
        "title": "Behavior Technician (RBT)", "type": ["FULL_TIME", "PART_TIME"],
        "description": (
            "<p>Deliver one-on-one ABA therapy sessions for children and teens with autism under BCBA supervision, at a center, "
            "in homes and at schools. Run programs, collect data, write session notes and celebrate progress with families.</p>"
            "<p>You bring: a high school diploma or higher, patience and energy for working with children, reliable transportation, "
            "and a clean background check. RBT credential preferred; we train and support candidates who are working toward it.</p>"
            "<p>Structured onboarding, hands-on training and supervision hours that count toward RBT requirements.</p>"
        ),
    },
    {
        "title": "Board Certified Behavior Analyst (BCBA)", "type": ["FULL_TIME"],
        "description": (
            "<p>Carry a manageable caseload, lead assessments and treatment planning, supervise and mentor technicians, and run "
            "parent training. In person at a center, with telehealth for some supervision and family sessions.</p>"
            "<p>You bring: current BCBA certification, Michigan licensure as a behavior analyst (or eligibility), and experience "
            "with early intervention or school-age programs.</p>"
        ),
    },
]


def jobs_json_ld() -> str:
    """Job postings for Google's job search. Both roles are open all year at
    every center (owner 2026-11-17), so the posting date is the build date."""
    import datetime
    import json
    today = datetime.date.today().isoformat()
    graph = []
    for j in JOBS:
        graph.append({
            "@type": "JobPosting", "title": j["title"], "description": j["description"],
            "datePosted": today, "employmentType": j["type"], "directApply": True,
            "url": f"{SITE}/careers",
            "hiringOrganization": {"@type": "Organization", "name": ORG["name"], "sameAs": SITE, "logo": f"{SITE}/assets/logo.png"},
            "jobLocation": [
                {"@type": "Place", "address": {
                    "@type": "PostalAddress", "streetAddress": c["street"], "addressLocality": c["city"],
                    "addressRegion": c["state"], "postalCode": c["zip"], "addressCountry": "US"}}
                for c in CENTERS
            ],
        })
    return f'<script type="application/ld+json">{json.dumps({"@context": "https://schema.org", "@graph": graph}, separators=(",", ":"))}</script>'


def json_ld() -> str:
    import json
    orgs = []
    for c in CENTERS:
        orgs.append({
            "@type": "MedicalBusiness",
            "name": f"BlueMind Therapy {c['name']}",
            "parentOrganization": {"@type": "Organization", "name": ORG["legal"]},
            "url": f"{SITE}/{center_slug(c)}",
            "telephone": c["phone_e164"],
            "email": ORG["email"],
            "address": {
                "@type": "PostalAddress", "streetAddress": c["street"], "addressLocality": c["city"],
                "addressRegion": c["state"], "postalCode": c["zip"], "addressCountry": "US",
            },
            "geo": {"@type": "GeoCoordinates", "latitude": c["lat"], "longitude": c["lng"]},
            "areaServed": c["county"],
            "openingHours": c["opening"],
            "medicalSpecialty": "Behavioral health",
            "image": f"{SITE}/assets/logo.png",
        })
    data = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "Organization", "name": ORG["name"], "legalName": ORG["legal"], "url": SITE,
                "logo": f"{SITE}/assets/logo.png", "telephone": ORG["phone_e164"], "email": ORG["email"],
                "sameAs": [ORG["instagram"]],
                "description": "Applied Behavior Analysis (ABA) therapy for children and teens with autism in Washtenaw, Wayne, St. Clair and Monroe counties, Michigan.",
            },
            *orgs,
        ],
    }
    return f'<script type="application/ld+json">{json.dumps(data, separators=(",", ":"))}</script>'


NAV = [
    ("services", "Services", "services.html"),
    ("locations", "Locations", "locations.html"),
    ("about", "About", "about.html"),
    ("careers", "Careers", "careers.html"),
    ("contact", "Contact", "contact.html"),
]


def message_widget() -> str:
    """Floating "Message us" chat window. A conversation with the team, not a
    form: the welcome message is already there, the visitor just types."""
    typical = REPLY["message"]
    return (
        '<div class="chat" id="chat">'
        '<button type="button" class="chat-fab" aria-expanded="false" aria-controls="chat-window">'
        + icon("chat") + '<span class="chat-fab-label">Message us</span><span class="chat-badge" hidden></span></button>'
        '<section class="chat-window" id="chat-window" role="dialog" aria-label="Chat with BlueMind Therapy" hidden>'
        '<header class="chat-head">'
        '<img src="assets/logo.png" alt="" width="40" height="40">'
        '<div class="chat-who"><strong>BlueMind Therapy</strong><span class="chat-status" data-chat-status>Typically replies within ' + typical + '</span></div>'
        '<button type="button" class="chat-close" aria-label="Close chat">' + icon("close") + '</button>'
        '</header>'
        '<div class="chat-log" data-chat-log role="log" aria-live="polite" aria-relevant="additions"></div>'
        '<div class="chat-quick" data-chat-quick></div>'
        '<form class="chat-compose" data-chat-compose>'
        '<label for="chat-input" class="sr-only">Your message</label>'
        '<textarea id="chat-input" rows="1" placeholder="Type a message…" maxlength="2000" enterkeyhint="send"></textarea>'
        '<button type="submit" class="chat-send" aria-label="Send">' + icon("send") + '</button>'
        '</form>'
        '</section></div>'
    )


def header(active: str, lang: str = "en", slug: str = "index") -> str:
    t = T(lang)
    labels = {"services": t["nav_services"], "locations": t["nav_locations"], "about": t["nav_about"],
              "careers": t["nav_careers"], "contact": t["nav_contact"]}
    links = ""
    for key, _label, href in NAV:
        current = ' aria-current="page"' if key == active else ""
        links += f'<a href="{href}"{current}>{labels[key]}</a>'

    return (
        f'<a class="skip" href="#main">{t["skip"]}</a>'
        '<header class="site-header"><div class="wrap">'
        '<a class="brand" href="index.html"><img src="assets/logo.png" alt="" width="48" height="48">'
        f'<span>BlueMind Therapy<small>{t["brand_small"]}</small></span></a>'
        f'<button class="nav-toggle" type="button" aria-expanded="false" aria-controls="nav" aria-label="{t["open_menu"]}">{icon("menu")}</button>'
        f'<nav class="nav" id="nav" aria-label="Main">{links}{lang_switch(slug, lang)}'
        f'<a class="btn btn-primary" href="refer.html">{t["nav_refer"]}</a></nav>'
        '</div></header>'
    )


def footer(lang: str = "en") -> str:
    t = T(lang)
    centers = "".join(
        f'<li><strong>{c["name"]}</strong><br><address>{c["street"]}<br>{c["city"]}, {c["state"]} {c["zip"]}</address>'
        f'<a href="{c["phone_href"]}" dir="ltr">{c["phone"]}</a></li>'
        for c in CENTERS
    )
    return (
        '<footer class="site-footer"><div class="wrap"><div class="cols">'
        f'<div><a class="brand" href="index.html"><img src="assets/logo.png" alt="" width="48" height="48"><span>BlueMind Therapy<small>{t["brand_small"]}</small></span></a>'
        f'<p style="margin-top:1rem">{t["footer_blurb"]}</p>'
        f'<p><a class="social" href="{ORG["instagram"]}" target="_blank" rel="noopener">{icon("instagram")} Instagram</a></p></div>'
        f'<div><h4>{t["footer_centers"]}</h4><ul>{centers}</ul></div>'
        f'<div><h4>{t["footer_families"]}</h4><ul><li><a href="services.html">{t["nav_services"]}</a></li><li><a href="index.html#how-it-works">{t["footer_how"]}</a></li>'
        f'<li><a href="index.html#faq">{t["footer_faq"]}</a></li><li><a href="refer.html">{t["footer_refer"]}</a></li><li><a href="status.html">{t["footer_status"]}</a></li><li><a href="contact.html">{t["footer_contact"]}</a></li></ul></div>'
        f'<div><h4>{t["footer_company"]}</h4><ul><li><a href="about.html">{t["footer_about"]}</a></li><li><a href="careers.html">{t["nav_careers"]}</a></li><li><a href="locations.html">{t["nav_locations"]}</a></li>'
        f'<li><a href="privacy.html">{t["footer_privacy"]}</a></li><li><a href="{ORG["dashboard"]}" rel="nofollow">{t["footer_staff"]}</a></li></ul></div>'
        f'</div><div class="legal"><span>© <span data-year>2026</span> BlueMind Therapy LLC. {t["footer_rights"]}</span>'
        f'<span>{t["footer_serving"]}</span></div></div></footer>'
    )


def head(meta: dict, slug: str, ld: str = "", lang: str = "en") -> str:
    title = meta["title"] if slug == "index" else f'{meta["title"]} · BlueMind Therapy'
    desc = meta["description"]
    prefix = "" if lang == "en" else f"/{lang}"
    canonical = SITE + prefix + ("/" if slug == "index" else f"/{slug}")
    alts = ""
    others = [c for c in LANGS if slug in translated_slugs(c)]
    if others:
        tail = "/" if slug == "index" else f"/{slug}"
        alts = f'<link rel="alternate" hreflang="en" href="{SITE}{tail}"><link rel="alternate" hreflang="x-default" href="{SITE}{tail}">' + "".join(
            f'<link rel="alternate" hreflang="{c}" href="{SITE}/{c}{tail}">' for c in others)
    direction = LANGS.get(lang, {}).get("dir", "ltr")

    noindex = '<meta name="robots" content="noindex">' if meta.get("noindex") == "true" else ""
    return f"""<!doctype html>
<html lang="{lang}" dir="{direction}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta http-equiv="Content-Security-Policy" content="default-src 'self'; script-src 'self'; style-src 'self' https://fonts.googleapis.com 'unsafe-inline'; font-src https://fonts.gstatic.com; img-src 'self' data:; connect-src 'self' {API_ORIGIN}; form-action 'self'; base-uri 'self'; object-src 'none'; frame-src 'none'; upgrade-insecure-requests">
<meta name="referrer" content="strict-origin-when-cross-origin">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{canonical}">
{alts}
{noindex}
<meta property="og:type" content="website">
<meta property="og:site_name" content="BlueMind Therapy">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{SITE}/assets/logo.png">
<meta name="theme-color" content="#0B3C8C">
<link rel="icon" href="assets/favicon.png" type="image/png">
<link rel="apple-touch-icon" href="assets/apple-touch-icon.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fredoka:wght@500;600&family=Nunito+Sans:ital,wght@0,400;0,600;0,700;1,400&display=swap">
<link rel="stylesheet" href="assets/site.css">
{ld or (json_ld() if slug in ("index", "locations") else "")}
</head>"""


def parse(path: Path) -> tuple[dict, str]:
    text = path.read_text(encoding="utf-8")
    m = re.match(r"\s*<!--(.*?)-->\s*", text, re.S)
    if not m:
        raise SystemExit(f"{path}: missing front matter comment")
    meta = {}
    for line in m.group(1).strip().splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip()
    body = text[m.end():]
    return meta, body


def expand(body: str, lang: str = "en") -> str:
    """Tiny template tags so pages stay readable."""
    body = re.sub(r"\{\{icon:([a-z-]+)(?::([a-z -]+))?\}\}", lambda m: icon(m.group(1), m.group(2) or ""), body)
    body = re.sub(
        r"\{\{photo:([a-z-]+)\|([^|}]+)(?:\|([a-z ]*))?(?:\|([abc]))?\}\}",
        lambda m: photo(m.group(1), m.group(2), m.group(3) or "", m.group(4) or "a", eager=(m.group(1) == "hero")),
        body,
    )
    body = re.sub(r"\{\{gallery:([^}]+)\}\}", lambda m: gallery(m.group(1)), body)
    body = body.replace("{{centers}}", "".join(center_card(c, lang=lang) for c in CENTERS))
    body = body.replace("{{centers-detailed}}", "".join(center_card(c, with_photo=True, detailed=True, lang=lang) for c in CENTERS))
    body = re.sub(r"\{\{phones(?::([a-z -]+))?\}\}", lambda m: phone_list(m.group(1) or ""), body)
    for k, v in ORG.items():
        body = body.replace("{{" + k + "}}", v)
    for k, v in REPLY.items():
        body = body.replace("{{reply:" + k + "}}", v)
    body = body.replace("{{safety}}", safety_block(lang))
    return body


def pretty_links(html: str) -> str:
    html = re.sub(r'href="(/(?:[a-z]{2}/)?)?index\.html(#[^"]*)?"', lambda m: f'href="{m.group(1) or "/"}{m.group(2) or ""}"', html)
    return re.sub(r'href="(/(?:[a-z]{2}/)?)?([a-z0-9-]+)\.html([#?][^"]*)?"', lambda m: f'href="{m.group(1) or "/"}{m.group(2)}{m.group(3) or ""}"', html)


def build(out: Path, html_links: bool) -> list[str]:
    out.mkdir(parents=True, exist_ok=True)
    slugs = []
    for src in sorted(SRC.glob("*.html")):
        meta, body = parse(src)
        slug = src.stem
        body_attr = ' data-no-sticky' if meta.get("sticky") == "false" else ""
        widget = "" if meta.get("nav") == "contact" else message_widget()
        page = (
            head(meta, slug, jobs_json_ld() if slug == "careers" else "") + f"\n<body{body_attr}>\n" + sprite() + header(meta.get("nav", ""), "en", slug) +
            f'<main id="main">{expand(body)}</main>' + footer() + widget +
            '\n<script src="assets/config.js"></script>\n<script src="assets/site.js" defer></script>\n</body>\n</html>\n'
        )
        if not html_links:
            page = pretty_links(page)
        (out / f"{slug}.html").write_text(page, encoding="utf-8")
        slugs.append(slug)
    lang_urls = []
    for lang in LANGS:
        src_dir = ROOT / "src" / f"pages-{lang}"
        if not src_dir.exists():
            continue
        import json
        (out / lang).mkdir(exist_ok=True)
        (ROOT / "assets" / f"i18n-{lang}.js").write_text(
            "window.BM_T = " + json.dumps({**{k: v for k, v in T(lang).items() if k.startswith("js_")}, "js_refer_href": f"/{lang}/refer" + (".html" if html_links else "")}, ensure_ascii=False) + ";\n",
            encoding="utf-8",
        )
        for src in sorted(src_dir.glob("*.html")):
            meta, body = parse(src)
            slug = src.stem
            body_attr = ' data-no-sticky' if meta.get("sticky") == "false" else ""
            widget = "" if meta.get("nav") == "contact" else message_widget()
            page = (
                head(meta, slug, "", lang) + f"\n<body{body_attr}>\n" + sprite() + header(meta.get("nav", ""), lang, slug) +
                f'<main id="main">{expand(body, lang)}</main>' + footer(lang) + widget +
                f'\n<script src="assets/config.js"></script>\n<script src="assets/i18n-{lang}.js"></script>\n<script src="assets/site.js" defer></script>\n</body>\n</html>\n'
            )
            page = localize_links(page, lang)
            if LANGS[lang]["dir"] == "rtl":
                # Phone numbers and clock times read left to right even inside Arabic text.
                parts = re.split(r"(<[^>]*>)", page)
                for i in range(0, len(parts), 2):
                    parts[i] = re.sub(r"(\(\d{3}\) \d{3}-\d{4})", r'<bdi dir="ltr">\1</bdi>', parts[i])
                page = "".join(parts)
            if not html_links:
                page = pretty_links(page)
            (out / lang / f"{slug}.html").write_text(page, encoding="utf-8")
            lang_urls.append(f"{SITE}/{lang}" + ("/" if slug == "index" else f"/{slug}"))
    center_slugs = []
    for c in CENTERS:
        meta, body = center_page(c)
        slug = center_slug(c)
        page = (
            head(meta, slug, center_json_ld(c)) + "\n<body>\n" + sprite() + header(meta["nav"]) +
            f'<main id="main">{body}</main>' + footer() + message_widget() +
            '\n<script src="assets/config.js"></script>\n<script src="assets/site.js" defer></script>\n</body>\n</html>\n'
        )
        if not html_links:
            page = pretty_links(page)
        (out / f"{slug}.html").write_text(page, encoding="utf-8")
        center_slugs.append(slug)
    if out != ROOT:
        for d in ("assets", "photos"):
            if (out / d).exists():
                shutil.rmtree(out / d)
            shutil.copytree(ROOT / d, out / d)
    # sitemap
    urls = "".join(
        f"<url><loc>{SITE}/{'' if s == 'index' else s}</loc></url>"
        for s in slugs if s not in ("404",) and parse(SRC / f"{s}.html")[0].get("noindex") != "true"
    )
    urls += "".join(f"<url><loc>{SITE}/{s}</loc></url>" for s in center_slugs)
    urls += "".join(f"<url><loc>{u}</loc></url>" for u in lang_urls)
    (out / "sitemap.xml").write_text(
        f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>\n',
        encoding="utf-8",
    )
    return slugs + center_slugs


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT))
    ap.add_argument("--html-links", action="store_true")
    args = ap.parse_args()
    built = build(Path(args.out).resolve(), args.html_links)
    print(f"built {len(built)} pages: {', '.join(built)} -> {args.out}")
