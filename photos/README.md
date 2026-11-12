# Photos

Drop real photos here and the site shows them automatically. Until a file exists, the page
shows an illustrated panel in its place. Current files came from the owner on 2026-11-11.

| File | Where it appears | What it is now |
|---|---|---|
| `hero.jpg` | Home page, top right | Playground, Ypsilanti |
| `ypsilanti.jpg` | Locations page, Ypsilanti card | Building with the sign |
| `dearborn.jpg` | Locations page, Dearborn card; About gallery | Entrance with the 18800 awning |
| `dearborn-sign.jpg` | About gallery | Road sign at 18800 Hubbard Drive |
| `fort-gratiot.jpg` | Locations page, Fort Gratiot card | still the illustrated panel |
| `reception.jpg` | Locations page, "What to expect" | Lobby with the logo |
| `services.jpg` | Services page | Therapy room with the chalkboard |
| `careers.jpg` | Home page, careers section | Therapy room with the magnet letters |

The About page shows a gallery of the center photos above (see `{{gallery:...}}` in
`src/pages/about.html`); add a photo there by adding `name|caption` to the list.

Rules: never a client, a client's first name, artwork with a name, or anything that could
identify a child. Staff photos need the staff member's written consent (the team photo
included). Landscape where possible, at least 1600 px wide, JPEG. `tools/build.py` does not
touch these files; resize and strip location metadata before adding (the current files
were saved without EXIF).
