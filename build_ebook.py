#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Combine the mirrored high-res space-group pages into one offline HTML book."""
import os
import re

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MIRROR = os.path.join(BASE_DIR, "mirror")
LARGE = os.path.join(MIRROR, "large")

def read(fn):
    with open(os.path.join(LARGE, fn), "rb") as f:
        return f.read().decode("latin-1", "replace")

def extract_body(html):
    m = re.search(r"<BODY[^>]*>(.*)</BODY>", html, re.I | re.S)
    return m.group(1) if m else html

def clean_body(body):
    # remove image-map navigation and areas
    body = re.sub(r"<MAP.*?</MAP>", "", body, flags=re.I | re.S)
    body = re.sub(r"<AREA[^>]*>", "", body, flags=re.I)
    # remove "Return link to the main menu"
    body = re.sub(r"<A HREF=\"\.\./mainmenu\.htm\">.*?</A> link to the main menu",
                  "", body, flags=re.I | re.S)
    # remove goback/goup mini-nav images
    body = re.sub(r"<A HREF=\"[^\"]+\">\s*<IMG SRC=\"go(back|up)\.gif\".*?</A>",
                  "", body, flags=re.I | re.S)
    # remove copyright footers
    body = re.sub(r"<FONT SIZE=-1>.*?</FONT>", "", body, flags=re.I | re.S)
    return body.strip()

def group_pages(prefix, entry):
    """Depth-first walk from the entry page over same-prefix sibling pages."""
    order = []
    seen = set()
    def visit(fn):
        if fn in seen:
            return
        seen.add(fn)
        order.append(fn)
        html = read(fn)
        for link in re.findall(r'href="(\d{3}[a-z0-9]+\.htm)"', html, re.I):
            if link.startswith(prefix):
                visit(link)
    visit(entry)
    return order

def main():
    index_html = read("sgp.htm")

    # locate crystal-system markers and group entries in document order
    events = []
    for m in re.finditer(r"<TH[^>]*>\s*<FONT[^>]*>([A-Za-z]+)</FONT>", index_html, re.I | re.S):
        events.append((m.start(), "system", m.group(1)))
    for m in re.finditer(
        r"(\d+)\.\s*(?:&nbsp;)?\s*<A HREF=\"(\d{3}[a-z0-9]+\.htm)\">(.*?)</A>",
        index_html, re.I | re.S):
        events.append((m.start(), "group", m.group(1), m.group(2), m.group(3)))
    events.sort(key=lambda e: e[0])

    groups = []
    cur_system = "Miscellaneous"
    for e in events:
        if e[1] == "system":
            cur_system = e[2]
        else:
            groups.append({"num": e[2], "file": e[3], "name": e[4], "system": cur_system})

    print(f"Parsed {len(groups)} groups from index")

    # page CSS
    css = """
@page { size: A4 landscape; margin: 10mm; }
body { font-family: Georgia, 'Times New Roman', serif; color: #111; background: #fff; }
h1.title { text-align: center; margin-top: 25mm; font-size: 28pt; }
h1.subtitle { text-align: center; font-weight: normal; font-size: 14pt; }
.cover-meta { text-align: center; margin-top: 8mm; font-size: 10pt; color: #555; }
h2.section { color: #b00; font-size: 18pt; border-bottom: 2px solid #b00; page-break-after: avoid; }
h2.sg { page-break-before: always; font-size: 15pt; border-bottom: 1px solid #999; padding-bottom: 2mm; }
.sgpage { page-break-after: always; }
.sgpage:last-child { page-break-after: auto; }
img.diagram { max-width: 100%; height: auto; }
pre.op { font-size: 10pt; }
.toc { page-break-before: always; }
.toc ol { list-style: none; padding-left: 0; }
.toc li { margin: 1px 0; }
.toc .sys { margin-top: 4mm; font-weight: bold; color: #b00; }
.toc a { color: #111; text-decoration: none; }
table { border-collapse: collapse; }
td, th { padding: 2px 6px; }
"""

    out = ['<!DOCTYPE html>', '<html><head>', '<meta charset="utf-8">',
           "<title>High-Resolution Space Group Diagrams and Tables (offline)</title>",
           "<style>" + css + "</style>", "</head><body>"]

    out.append('<h1 class="title">Space Group Diagrams and Tables</h1>')
    out.append('<h1 class="subtitle">High-Resolution Set &mdash; all 230 space groups</h1>')
    out.append('<div class="cover-meta">Mirrored from '
               'http://img.chem.ucl.ac.uk/sgp/large/sgp.htm<br>'
               '&copy; 1997-1999 Jeremy Karl Cockcroft, Birkbeck College, University of London. '
               'For personal offline reference only.</div>')

    # TOC
    out.append('<div class="toc"><h2>Contents</h2>')
    cur = None
    for g in groups:
        if g["system"] != cur:
            cur = g["system"]
            out.append(f'<p class="sys">{cur}</p>')
        out.append(f'<ol><li><a href="#sg{g["num"]}">'
                   f'{g["num"]}. {g["name"]}</a></li></ol>')
    out.append("</div>")

    # body per group
    missing_imgs = []
    total_pages = 0
    cur = None
    for g in groups:
        prefix = g["file"][:3]
        if g["system"] != cur:
            cur = g["system"]
            out.append(f'<h2 class="section" id="sec-{prefix}">{cur}</h2>')
        pages = group_pages(prefix, g["file"])
        out.append(f'<h2 class="sg" id="sg{g["num"]}">{g["num"]}. {g["name"]}</h2>')
        total_pages += len(pages)
        for i, fn in enumerate(pages):
            body = clean_body(extract_body(read(fn)))
            # rewrite image references to the local gif name only
            body = re.sub(r'\b(WIDTH|HEIGHT|BORDER|ALT|USEMAP|ISMAP)=[^ >]+',
                          "", body, flags=re.I)
            body = body.replace('<IMG SRC="', '<img class="diagram" src="')
            body = body.replace('</IMG>', '')
            for im in re.findall(r'src="([^"]+\.gif)"', body, re.I):
                if not os.path.exists(os.path.join(LARGE, im)):
                    missing_imgs.append((fn, im))
            out.append(f'<div class="sgpage">{body}</div>')
        if not pages:
            out.append(f'<div class="sgpage"><p>[no pages found for {g["file"]}]</p></div>')

    out.append("</body></html>")

    dest = os.path.join(LARGE, "combined.html")
    with open(dest, "w", encoding="utf-8") as f:
        f.write("\n".join(out))
    print(f"Wrote {dest}  ({os.path.getsize(dest)//1024} KB)")
    print(f"Groups: {len(groups)}  Pages included: {total_pages}")
    if missing_imgs:
        print(f"MISSING IMAGES ({len(missing_imgs)}): {missing_imgs[:10]}")

if __name__ == "__main__":
    main()
