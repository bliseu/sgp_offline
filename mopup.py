#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Mop-up: fetch every referenced-but-missing local file, iteratively."""
import os
import re
import time
import urllib.parse
import urllib.request

BASE = "http://img.chem.ucl.ac.uk/sgp"
MIRROR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mirror")
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

def save(url):
    p = urllib.parse.urlsplit(url)
    rel = p.path[len("/sgp/"):]
    if not rel or rel.endswith("/"):
        rel = "index.htm"
    dest = os.path.join(MIRROR, rel)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    req = urllib.request.Request(url, headers=UA)
    last = None
    for attempt in range(8):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                data = r.read()
            with open(dest, "wb") as f:
                f.write(data)
            return rel, data
        except Exception as e:
            last = e
            time.sleep(2 * (attempt + 1))
    return rel, None

def in_scope(url):
    p = urllib.parse.urlsplit(url).path
    if not p.startswith("/sgp/"):
        return False
    rel = p[len("/sgp/"):]
    return rel == "mainmenu.htm" or rel == "copyrite.htm" or rel == "sgp.htm" \
        or rel.startswith("large/") or rel.startswith("misc/")

def find_missing():
    missing = set()
    for dirpath, _, files in os.walk(MIRROR):
        for fn in files:
            if not fn.lower().endswith((".htm", ".html")):
                continue
            full = os.path.join(dirpath, fn)
            with open(full, "rb") as f:
                text = f.read().decode("latin-1", "replace")
            for m in re.finditer(r'(?:href|src)="([^"]+)"', text, re.I):
                ref = m.group(1).split("?")[0].split("#")[0]
                if not ref or ref.startswith(("http", "mailto", "javascript", "tel:", "ftp:")):
                    continue
                absu = urllib.parse.urljoin("file:///" + full.replace("\\", "/"), ref)
                p = urllib.parse.urlsplit(absu)
                if p.scheme != "file":
                    continue
                local = urllib.parse.unquote(p.path).lstrip("/")
                if not local:
                    continue
                rel_under_mirror = os.path.relpath(local, MIRROR)
                if rel_under_mirror.startswith(".."):
                    continue
                url = urllib.parse.urljoin(BASE + "/", rel_under_mirror.replace("\\", "/"))
                if not in_scope(url):
                    continue
                if not os.path.exists(local):
                    missing.add((url, rel_under_mirror.replace("\\", "/")))
    return missing

total_ok = 0
for rnd in range(6):
    missing = find_missing()
    if not missing:
        print("No missing files.")
        break
    print(f"round {rnd}: {len(missing)} missing -> fetching")
    ok = 0
    for url, rel in sorted(missing):
        if os.path.exists(os.path.join(MIRROR, rel)):
            continue
        r, data = save(url)
        if data is not None:
            ok += 1
        else:
            print("  FAIL", rel, flush=True)
    total_ok += ok
    print(f"  fetched {ok} this round")
else:
    still = find_missing()
    print(f"STILL MISSING after 6 rounds: {len(still)}")
    for url, rel in sorted(still)[:20]:
        print("  ", rel)
print(f"Total newly fetched: {total_ok}")
