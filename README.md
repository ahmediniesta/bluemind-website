# bluemindmi.com

The public website for BlueMind Therapy. Static HTML, no framework, no build server:
nine pages, one stylesheet, one script. Forms post to the BlueMind dashboard's public
intake API and land in the dashboard's Referral Queue and Website Inbox.

## Edit a page

1. Edit the page body in `src/pages/<page>.html` (the shared header, footer, icons and
   center cards live in `tools/build.py`).
2. Run `python3 tools/build.py` (Python 3, no packages needed).
3. Commit the result. The root `*.html` files are what gets served.

Addresses, phone and emails are in one place: the `ORG` and `CENTERS` tables at the top of
`tools/build.py`. Change them there and rebuild.

Photos: drop files into `photos/` (see `photos/README.md`). The pages pick them up
automatically and show an illustrated panel until then.

## Where the forms go

`assets/config.js` holds the API base (the dashboard on Railway). The three forms post to:

| Form | Endpoint | Shows up in |
|---|---|---|
| Refer a child | `POST /api/referral-portal/referrals` | Dashboard → Referral Queue |
| Careers application | `POST /api/website-portal/applications` | Dashboard → Website Inbox → Applicants |
| Contact message | `POST /api/website-portal/messages` | Dashboard → Website Inbox → Messages |

The dashboard must allow this site's origin: `CORS_ORIGINS` on Railway needs
`https://bluemindmi.com,https://www.bluemindmi.com` added.

## Go live: two ways

### A. GitHub Pages (free, recommended)


1. Create the GitHub repo and push (from this folder):

       gh repo create ahmediniesta/bluemind-website --public --source=. --push

   Public, because GitHub Pages on a free account needs a public repo and the site is
   public anyway. Nothing private is in here.
2. Repo → Settings → Pages → Source: *Deploy from a branch* → `main` / `/ (root)` → Save.
   `CNAME` already says `bluemindmi.com`, so Pages will ask for the DNS below.
3. In GoDaddy → My Products → bluemindmi.com → DNS, replace the current records with:

   | Type | Name | Value |
   |---|---|---|
   | A | @ | 185.199.108.153 |
   | A | @ | 185.199.109.153 |
   | A | @ | 185.199.110.153 |
   | A | @ | 185.199.111.153 |
   | CNAME | www | ahmediniesta.github.io |

   Leave the MX, TXT and SPF records alone (that is Google Workspace mail).
   Delete the two old A records (76.223.105.230 and 13.248.243.5), which point at the
   GoDaddy Website Builder.
4. Back in GitHub Pages, tick *Enforce HTTPS* once the certificate appears (up to an hour).
5. Cancel the GoDaddy Website Builder subscription after the new site is confirmed live.

Any push to `main` republishes within a minute.

### B. GoDaddy Web Hosting (keeps everything at GoDaddy, about $6 to $12 a month)

The current site runs on GoDaddy *Website Builder*, which cannot host custom files. Hosting
here means GoDaddy's regular **Web Hosting** (Linux, cPanel) plan.

1. GoDaddy → My Products → **Web Hosting** → buy the Economy (Linux) plan if there is none,
   and pick `bluemindmi.com` when it asks which domain to use. GoDaddy then points the
   domain's A record at the hosting server itself; the Website Builder stops answering.
2. Run `tools/package.sh` on the Mac. It writes `~/Desktop/bluemindmi-site.zip`.
3. Hosting dashboard → **cPanel Admin** → **File Manager** → `public_html` → delete the
   placeholder files there → **Upload** the zip → right click it → **Extract** → delete the zip.
4. Hosting dashboard → **SSL**: turn on the certificate that comes with the plan so
   https://bluemindmi.com works (the `.htaccess` already forces HTTPS and drops `www`).
5. Check https://bluemindmi.com/services and https://bluemindmi.com/nothing-here (the 404 page).
6. Cancel the Website Builder subscription once the new site is confirmed live.

Later updates: run `tools/package.sh` and upload again, or give Claude an FTP account from
cPanel → FTP Accounts and `tools/deploy_godaddy.sh` pushes the site in one command.

Either way, the dashboard on Railway needs `CORS_ORIGINS` to include
`https://bluemindmi.com,https://www.bluemindmi.com` before the forms and the chat can post.
