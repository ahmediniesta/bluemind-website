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

ORG = {
    "name": "BlueMind Therapy",
    "legal": "BlueMind Therapy LLC",
    "phone": "(734) 252-5215",
    "phone_href": "tel:+17342525215",
    "phone_e164": "+1-734-252-5215",
    "email": "info@bluemindmi.com",
    "careers_email": "hr@bluemindmi.com",
    "instagram": "https://www.instagram.com/bluemindtherapymi/",
    "dashboard": "https://bluemind-dashboard-production.up.railway.app/login",
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
    },
    {
        "key": "fort-gratiot", "name": "Fort Gratiot", "county": "St. Clair County",
        "street": "4435 24th Avenue", "city": "Fort Gratiot", "state": "MI", "zip": "48059",
        "payer": "St. Clair County Community Mental Health",
        "phone": "(810) 479-9375", "phone_href": "tel:+18104799375", "phone_e164": "+1-810-479-9375",
        "hours": [("Monday to Friday", "8:00 am to 8:00 pm"), ("Saturday", "8:00 am to 3:00 pm"), ("Sunday", "Closed")],
        "opening": ["Mo-Fr 08:00-20:00", "Sa 08:00-15:00"],
        "lat": 43.0340, "lng": -82.4530,
    },
]


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
    ("cctv", "24/7", "Cameras record every room, 24 hours a day", "كاميرات تسجّل كل غرفة على مدار الساعة", "Cámaras graban cada sala las 24 horas"),
    ("lock", "", "Locked doors. Only staff and checked-in families enter", "أبواب مقفلة، لا يدخل إلا الموظفون والعائلات المسجّلة", "Puertas con cerradura. Solo entran el personal y las familias registradas"),
    ("id-check", "", "Every team member passes background checks", "كل عضو في الفريق يجتاز فحص السجل الجنائي", "Todo el personal pasa verificación de antecedentes"),
    ("eye", "", "A BCBA supervises every child's program", "محلل سلوك معتمد يشرف على برنامج كل طفل", "Un BCBA supervisa el programa de cada niño"),
]


def safety_block() -> str:
    banner = (
        '<figure class="safety-photo">'
        + photo("cameras", "The camera wall at one of our centers: every room on screen, recorded around the clock (feeds blurred for privacy)", "wide")
        + '<figcaption><strong>Every room, on camera, 24/7.</strong> This is the monitor at one of our centers. The feeds are blurred here for privacy. In the building, every room is recorded around the clock.</figcaption>'
        '</figure>'
    )
    cards = ""
    for name, badge, en, ar, es in SAFETY:
        badge_html = f'<span class="safety-badge">{badge}</span>' if badge else ""
        cards += (
            '<li class="safety-card">'
            f'<div class="safety-icon">{icon(name)}{badge_html}</div>'
            f'<p class="safety-en">{en}</p>'
            f'<p class="safety-l" lang="ar" dir="rtl">{ar}</p>'
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


def center_card(c: dict, with_photo: bool = False, detailed: bool = False) -> str:
    hours = "".join(f"<tr><td>{d}</td><td>{h}</td></tr>" for d, h in c["hours"])
    photo_html = photo(c["key"], f"The BlueMind Therapy center in {c['name']}", "wide", pos=c.get("photo_pos", "")) if with_photo else ""
    details = (
        f'<p class="muted small" style="margin:0.5rem 0 0">Medicaid members: {c["payer"]}</p>'
        f'<table class="hours-table" style="margin-top:0.75rem"><tbody>{hours}</tbody></table>'
        if detailed else ""
    )
    return (
        f'<div class="card center-card" id="{c["key"]}">{photo_html}'
        f'<div class="county">{c["county"]}</div>'
        f'<h3 style="margin:0">{c["name"]}</h3>'
        f'<address>{c["street"]}<br>{c["city"]}, {c["state"]} {c["zip"]}</address>'
        f'{details}'
        f'<div class="links"><a href="{maps_url(c)}" target="_blank" rel="noopener">Get directions</a>'
        f'<a href="{c["phone_href"]}">Call {c["phone"]}</a>'
        + (f'<a href="refer.html">Refer to this center</a>' if detailed else "")
        + '</div></div>'
    )


def json_ld() -> str:
    import json
    orgs = []
    for c in CENTERS:
        orgs.append({
            "@type": "MedicalBusiness",
            "name": f"BlueMind Therapy {c['name']}",
            "parentOrganization": {"@type": "Organization", "name": ORG["legal"]},
            "url": f"{SITE}/locations#{c['key']}",
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


def header(active: str) -> str:
    links = ""
    for key, label, href in NAV:
        current = ' aria-current="page"' if key == active else ""
        links += f'<a href="{href}"{current}>{label}</a>'

    return (
        '<a class="skip" href="#main">Skip to content</a>'
        '<header class="site-header"><div class="wrap">'
        '<a class="brand" href="index.html"><img src="assets/logo.png" alt="" width="48" height="48">'
        '<span>BlueMind Therapy<small>Autism therapy services</small></span></a>'
        f'<button class="nav-toggle" type="button" aria-expanded="false" aria-controls="nav" aria-label="Open menu">{icon("menu")}</button>'
        f'<nav class="nav" id="nav" aria-label="Main">{links}'
        '<a class="btn btn-primary" href="refer.html">Refer a client</a></nav>'
        '</div></header>'
    )


def footer() -> str:
    centers = "".join(
        f'<li><strong>{c["name"]}</strong><br><address>{c["street"]}<br>{c["city"]}, {c["state"]} {c["zip"]}</address>'
        f'<a href="{c["phone_href"]}">{c["phone"]}</a></li>'
        for c in CENTERS
    )
    return (
        '<footer class="site-footer"><div class="wrap"><div class="cols">'
        '<div><a class="brand" href="index.html"><img src="assets/logo.png" alt="" width="48" height="48"><span>BlueMind Therapy<small>Autism therapy services</small></span></a>'
        '<p style="margin-top:1rem">One-on-one ABA therapy for children and teens with autism, at our three Michigan centers, at home, at school and in the community.</p>'
        f'<p><a class="social" href="{ORG["instagram"]}" target="_blank" rel="noopener">{icon("instagram")} Instagram</a></p></div>'
        f'<div><h4>Our centers</h4><ul>{centers}</ul></div>'
        '<div><h4>Families</h4><ul><li><a href="services.html">Services</a></li><li><a href="index.html#how-it-works">How it works</a></li>'
        '<li><a href="index.html#faq">Questions parents ask</a></li><li><a href="refer.html">Refer a child</a></li><li><a href="status.html">Check your status</a></li><li><a href="contact.html">Contact us</a></li></ul></div>'
        f'<div><h4>Company</h4><ul><li><a href="about.html">About BlueMind</a></li><li><a href="careers.html">Careers</a></li><li><a href="locations.html">Locations</a></li>'
        f'<li><a href="privacy.html">Privacy notice</a></li><li><a href="{ORG["dashboard"]}" rel="nofollow">Staff sign in</a></li></ul></div>'
        '</div><div class="legal"><span>© <span data-year>2026</span> BlueMind Therapy LLC. All rights reserved.</span>'
        '<span>Serving Washtenaw, Wayne, St. Clair and Monroe counties, Michigan</span></div></div></footer>'
    )


def head(meta: dict, slug: str) -> str:
    title = meta["title"] if slug == "index" else f'{meta["title"]} · BlueMind Therapy'
    desc = meta["description"]
    canonical = SITE + ("/" if slug == "index" else f"/{slug}")
    noindex = '<meta name="robots" content="noindex">' if meta.get("noindex") == "true" else ""
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{canonical}">
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
{json_ld() if slug in ("index", "locations") else ""}
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


def expand(body: str) -> str:
    """Tiny template tags so pages stay readable."""
    body = re.sub(r"\{\{icon:([a-z-]+)(?::([a-z -]+))?\}\}", lambda m: icon(m.group(1), m.group(2) or ""), body)
    body = re.sub(
        r"\{\{photo:([a-z-]+)\|([^|}]+)(?:\|([a-z ]*))?(?:\|([abc]))?\}\}",
        lambda m: photo(m.group(1), m.group(2), m.group(3) or "", m.group(4) or "a", eager=(m.group(1) == "hero")),
        body,
    )
    body = re.sub(r"\{\{gallery:([^}]+)\}\}", lambda m: gallery(m.group(1)), body)
    body = body.replace("{{centers}}", "".join(center_card(c) for c in CENTERS))
    body = body.replace("{{centers-detailed}}", "".join(center_card(c, with_photo=True, detailed=True) for c in CENTERS))
    body = re.sub(r"\{\{phones(?::([a-z -]+))?\}\}", lambda m: phone_list(m.group(1) or ""), body)
    for k, v in ORG.items():
        body = body.replace("{{" + k + "}}", v)
    for k, v in REPLY.items():
        body = body.replace("{{reply:" + k + "}}", v)
    body = body.replace("{{safety}}", safety_block())
    return body


def pretty_links(html: str) -> str:
    html = re.sub(r'href="index\.html(#[^"]*)?"', lambda m: f'href="/{m.group(1) or ""}"', html)
    return re.sub(r'href="([a-z0-9-]+)\.html(#[^"]*)?"', lambda m: f'href="/{m.group(1)}{m.group(2) or ""}"', html)


def build(out: Path, html_links: bool) -> list[str]:
    out.mkdir(parents=True, exist_ok=True)
    slugs = []
    for src in sorted(SRC.glob("*.html")):
        meta, body = parse(src)
        slug = src.stem
        body_attr = ' data-no-sticky' if meta.get("sticky") == "false" else ""
        widget = "" if meta.get("nav") == "contact" else message_widget()
        page = (
            head(meta, slug) + f"\n<body{body_attr}>\n" + sprite() + header(meta.get("nav", "")) +
            f'<main id="main">{expand(body)}</main>' + footer() + widget +
            '\n<script src="assets/config.js"></script>\n<script src="assets/site.js" defer></script>\n</body>\n</html>\n'
        )
        if not html_links:
            page = pretty_links(page)
        (out / f"{slug}.html").write_text(page, encoding="utf-8")
        slugs.append(slug)
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
    (out / "sitemap.xml").write_text(
        f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>\n',
        encoding="utf-8",
    )
    return slugs


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT))
    ap.add_argument("--html-links", action="store_true")
    args = ap.parse_args()
    built = build(Path(args.out).resolve(), args.html_links)
    print(f"built {len(built)} pages: {', '.join(built)} -> {args.out}")
