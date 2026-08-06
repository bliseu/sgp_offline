#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Full recursive crawl of http://img.chem.ucl.ac.uk/sgp/ for offline use."""
import os
import re
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE = "http://img.chem.ucl.ac.uk/sgp"
MIRROR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mirror")
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

done = set()      # absolute urls already fetched
failed = {}       # url -> error
downloaded = 0

def norm(url):
    """Normalize: drop fragment, keep host/path/query."""
    p = urllib.parse.urlsplit(url)
    return urllib.parse.urlunsplit((p.scheme, p.netloc, p.path, p.query, ""))

def in_scope(url):
    """Only the high-resolution set: /large/, /misc/ shared pages, and root files."""
    if not url.startswith(BASE):
        return False
    path = url[len(BASE):]
    if path in ("/mainmenu.htm", "/copyrite.htm", "/sgp.htm"):
        return True
    return path.startswith("/large/") or path.startswith("/misc/")

def fetch(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=90) as r:
        return r.read(), r.geturl()

def crawl():
    global downloaded
    frontier = [BASE + "/large/sgp.htm"]
    # shared root pages the index relies on
    frontier += [BASE + "/mainmenu.htm", BASE + "/copyrite.htm"]
    seen = set()
    while frontier:
        # round of fetches
        batch = [u for u in frontier if u not in seen and u not in done]
        seen |= set(batch)
        if not batch:
            break
        results = {}
        with ThreadPoolExecutor(max_workers=6) as ex:
            futs = {ex.submit(fetch, u): u for u in batch}
            for fut in as_completed(futs):
                u = futs[fut]
                try:
                    data, final = fut.result()
                    results[u] = data
                except Exception as e:
                    failed[u] = str(e)
        # save + discover
        new_frontier = []
        for u, data in results.items():
            if not in_scope(u):
                continue
            done.add(u)
            p = urllib.parse.urlsplit(u)
            rel = p.path[len("/sgp/"):] if p.path.startswith("/sgp/") else p.path.lstrip("/")
            if not rel or rel.endswith("/"):
                rel = os.path.join(rel, "index.htm") if rel else "index.htm"
            dest = os.path.join(MIRROR, rel)
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            try:
                with open(dest, "wb") as f:
                    f.write(data)
            except OSError:
                # collision with an existing directory / reserved name
                dest = os.path.join(os.path.dirname(dest), os.path.basename(rel) + ".html")
                with open(dest, "wb") as f:
                    f.write(data)
            downloaded += 1
            text = data.decode("latin-1", "replace")
            for m in re.findall(r'(?:href|src)="([^"]+)"', text, re.I):
                ref = m.split("?")[0].split("#")[0]
                if not ref or ref.startswith(("mailto:", "javascript:", "tel:", "ftp:")):
                    continue
                absu = urllib.parse.urljoin(u, ref)
                absu = norm(absu)
                if in_scope(absu) and absu not in seen and absu not in done:
                    new_frontier.append(absu)
        frontier = new_frontier
        print(f"[round] batch={len(batch)} done={len(done)} pending={len(frontier)} "
              f"failed={len(failed)}", flush=True)

    print(f"\nCRAWL DONE. files written: {downloaded}")
    if failed:
        print(f"FAILED ({len(failed)}):")
        for u, e in list(failed.items())[:40]:
            print(f"  {u}  -> {e}")

if __name__ == "__main__":
    crawl()
