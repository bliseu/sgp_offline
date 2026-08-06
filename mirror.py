#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Mirror the UCL Space Group diagrams site (large resolution set) for offline use."""
import os
import re
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE = "http://img.chem.ucl.ac.uk/sgp"
MIRROR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mirror")

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

downloaded = 0
missing = []
lock = None  # GIL makes counter increments safe enough

def fetch(url, retries=4):
    last = None
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=90) as r:
                return r.read()
        except Exception as e:
            last = e
            time.sleep(1.5 * (i + 1))
    raise last

def save(url, relpath):
    """Download url and write to MIRROR/relpath. Returns True on success."""
    global downloaded
    dest = os.path.join(MIRROR, relpath)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    try:
        data = fetch(url)
        with open(dest, "wb") as f:
            f.write(data)
        downloaded += 1
        return True
    except Exception as e:
        missing.append((url, str(e)))
        return False

def hrefs(content, pattern):
    return sorted(set(re.findall(pattern, content, re.I)))

def main():
    global downloaded
    os.makedirs(MIRROR, exist_ok=True)
    # ---- shared top-level pages ----
    shared = ["copyrite.htm", "mainmenu.htm"]
    for name in shared:
        save(f"{BASE}/{name}", name)

    # ---- misc pages ----
    misc = ["author.htm", "birkbeck.htm", "sgpnum.htm", "spacegrp.htm"]
    for name in misc:
        save(f"{BASE}/misc/{name}", os.path.join("misc", name))

    # ---- main index ----
    index = fetch(f"{BASE}/large/sgp.htm")
    with open(os.path.join(MIRROR, "large", "sgp.htm"), "wb") as f:
        f.write(index)
    downloaded += 1

    # ---- 230 space-group pages ----
    group_pages = hrefs(index.decode("latin-1", "replace"), r'href="(\d{3}[a-z]+\d*\.htm)"')
    print(f"Index lists {len(group_pages)} group pages", flush=True)

    page_urls = [(f"{BASE}/large/{p}", os.path.join("large", p)) for p in group_pages]

    # fetch all group pages first (need them to discover images)
    fetched = {}
    def get_group(item):
        url, rel = item
        try:
            data = fetch(url)
            return rel, url, data
        except Exception as e:
            missing.append((url, str(e)))
            return rel, url, None
    with ThreadPoolExecutor(max_workers=8) as ex:
        futs = [ex.submit(get_group, it) for it in page_urls]
        for fut in as_completed(futs):
            rel, url, data = fut.result()
            fetched[rel] = data
    print(f"Fetched group pages: {len(fetched)}", flush=True)

    # write group pages + collect image / further page references
    image_urls = set()
    more_pages = set()
    for rel, data in fetched.items():
        if data is None:
            continue
        dest = os.path.join(MIRROR, rel)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest, "wb") as f:
            f.write(data)
        text = data.decode("latin-1", "replace")
        for img in hrefs(text, r'src="([^"]+\.gif)"') + hrefs(text, r'src="([^"]+\.jpg)"') + hrefs(text, r'src="([^"]+\.png)"'):
            if not img.startswith("http"):
                image_urls.add(f"{BASE}/large/{img}")
        for pg in hrefs(text, r'href="(\d{3}[a-z]+\d*\.htm)"'):
            more_pages.add(pg)

    # any group pages discovered from inside other pages (az2/az3 chain)
    extra = set(p for p in more_pages if p not in group_pages)
    if extra:
        print(f"Extra pages found: {len(extra)}", flush=True)
        def get_extra(name):
            url = f"{BASE}/large/{name}"
            try:
                data = fetch(url)
                return name, data
            except Exception as e:
                missing.append((url, str(e)))
                return name, None
        with ThreadPoolExecutor(max_workers=8) as ex:
            futs = [ex.submit(get_extra, n) for n in sorted(extra)]
            for fut in as_completed(futs):
                name, data = fut.result()
                if data is None:
                    continue
                with open(os.path.join(MIRROR, "large", name), "wb") as f:
                    f.write(data)
                text = data.decode("latin-1", "replace")
                for img in hrefs(text, r'src="([^"]+\.gif)"'):
                    image_urls.add(f"{BASE}/large/{img}")

    print(f"Images to download: {len(image_urls)}", flush=True)
    def get_image(url):
        name = os.path.basename(url)
        return save(url, os.path.join("large", name))
    with ThreadPoolExecutor(max_workers=8) as ex:
        futs = [ex.submit(get_image, u) for u in sorted(image_urls)]
        for _ in as_completed(futs):
            pass

    # icons etc referenced by index page
    for ic in hrefs(index.decode("latin-1", "replace"), r'(?:src|href)="([^"]+\.ico)"'):
        if not ic.startswith("http"):
            save(f"{BASE}/large/{ic}", os.path.join("large", ic))

    print(f"\nDONE. Downloaded files: {downloaded}", flush=True)
    if missing:
        print(f"Missing/failed ({len(missing)}):")
        for u, e in missing[:20]:
            print(f"  {u}  -> {e}")

if __name__ == "__main__":
    main()
