#!/usr/bin/env python3
"""Point bluemindmi.com at GitHub Pages through the GoDaddy Domains API.

    export GODADDY_TOKEN=...          # Personal Access Token from https://developer.godaddy.com (Domains & DNS scope)
    # or the older key pair:  export GODADDY_API_KEY=...  GODADDY_API_SECRET=...
    python3 tools/godaddy_dns.py --show            # print the current records
    python3 tools/godaddy_dns.py --backup FILE     # save every record to FILE (json)
    python3 tools/godaddy_dns.py --apply           # A @ -> GitHub Pages, CNAME www -> ahmediniesta.github.io
    python3 tools/godaddy_dns.py --restore FILE    # put the A @ and CNAME www records from FILE back
    python3 tools/godaddy_dns.py --add-txt NAME 'VALUE'   # add one TXT record (DKIM, DMARC, verification)
    python3 tools/godaddy_dns.py --dmarc                   # add the monitoring DMARC record (p=none) for the domain

--apply and --restore write only the A records at @ and the CNAME at www. --add-txt and
--dmarc ADD one TXT record and never replace or delete anything. MX, SPF and existing
TXT records are never touched by any mode.
A Personal Access Token is made in the GoDaddy developer dashboard (Custom permissions,
Domains & DNS only, 7 days). It is sent as "Authorization: Bearer"; the deprecated
key:secret pair is sent as "sso-key".
"""
import argparse, json, os, sys, urllib.request, urllib.error

DOMAIN = "bluemindmi.com"
API = "https://api.godaddy.com/v1/domains/" + DOMAIN + "/records"
GITHUB_A = ["185.199.108.153", "185.199.109.153", "185.199.110.153", "185.199.111.153"]
GITHUB_CNAME = "ahmediniesta.github.io"
TTL = 600
# Monitoring only (p=none): mailbox providers report who sends as @bluemindmi.com, nothing is
# rejected yet. Move to p=quarantine once DKIM is on and the reports look clean.
DMARC_MONITOR = "v=DMARC1; p=none; rua=mailto:dmarc@bluemindmi.com; fo=1"


def auth() -> str:
    token = os.environ.get("GODADDY_TOKEN")
    if token:
        return f"Bearer {token.strip()}"
    key, secret = os.environ.get("GODADDY_API_KEY"), os.environ.get("GODADDY_API_SECRET")
    if not key or not secret:
        sys.exit("set GODADDY_TOKEN (personal access token) or GODADDY_API_KEY + GODADDY_API_SECRET first")
    return f"sso-key {key}:{secret}"


def call(method: str, path: str = "", body=None):
    req = urllib.request.Request(API + path, method=method, data=None if body is None else json.dumps(body).encode())
    req.add_header("Authorization", auth())
    req.add_header("Accept", "application/json")
    if body is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            raw = r.read()
            return json.loads(raw) if raw else None
    except urllib.error.HTTPError as e:
        sys.exit(f"GoDaddy answered {e.code} on {method} {path}: {e.read().decode()[:400]}")


def show(records):
    for r in sorted(records, key=lambda r: (r["type"], r["name"])):
        print(f'{r["type"]:6} {r["name"]:20} {r["data"]:45} ttl={r.get("ttl")}' + (f' prio={r["priority"]}' if "priority" in r else ""))


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--show", action="store_true")
    g.add_argument("--backup", metavar="FILE")
    g.add_argument("--apply", action="store_true")
    g.add_argument("--restore", metavar="FILE")
    g.add_argument("--add-txt", nargs=2, metavar=("NAME", "VALUE"))
    g.add_argument("--dmarc", action="store_true")
    a = ap.parse_args()

    if a.show:
        show(call("GET")); return
    if a.backup:
        recs = call("GET")
        with open(a.backup, "w") as f:
            json.dump(recs, f, indent=1)
        print(f"saved {len(recs)} records to {a.backup}"); show(recs); return
    if a.apply:
        before = call("GET")
        print("before:"); show(before)
        call("PUT", "/A/@", [{"data": ip, "ttl": TTL} for ip in GITHUB_A])
        call("PUT", "/CNAME/www", [{"data": GITHUB_CNAME, "ttl": TTL}])
        print("\nafter:"); show(call("GET")); return
    if a.add_txt or a.dmarc:
        name, value = a.add_txt if a.add_txt else ("_dmarc", DMARC_MONITOR)
        existing = [r for r in call("GET") if r["type"] == "TXT" and r["name"] == name]
        if any(r["data"] == value for r in existing):
            print(f"TXT {name} already holds that value; nothing to do"); return
        if name == "_dmarc" and existing:
            sys.exit("a _dmarc record already exists; change it deliberately, not by adding a second one")
        # PATCH appends records; it never replaces the existing ones at other names.
        call("PATCH", "", [{"type": "TXT", "name": name, "data": value, "ttl": TTL}])
        print("added:"); show([r for r in call("GET") if r["type"] == "TXT"]); return
    if a.restore:
        with open(a.restore) as f:
            recs = json.load(f)
        a_at = [{"data": r["data"], "ttl": r.get("ttl", TTL)} for r in recs if r["type"] == "A" and r["name"] == "@"]
        www = [{"data": r["data"], "ttl": r.get("ttl", TTL)} for r in recs if r["type"] == "CNAME" and r["name"] == "www"]
        if a_at:
            call("PUT", "/A/@", a_at)
        if www:
            call("PUT", "/CNAME/www", www)
        print("restored:"); show(call("GET"))


if __name__ == "__main__":
    main()
