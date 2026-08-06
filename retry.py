#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Retry the failed downloads with more patience."""
import os
import re
import time
import urllib.parse
import urllib.request

BASE = "http://img.chem.ucl.ac.uk/sgp"
MIRROR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mirror")
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

FAILED = [
    "http://img.chem.ucl.ac.uk/sgp/large/019bz1.htm",
    "http://img.chem.ucl.ac.uk/sgp/misc/spacegrp.htm",
    "http://img.chem.ucl.ac.uk/sgp/large/020az1.gif",
    "http://img.chem.ucl.ac.uk/sgp/misc/sgpnum.htm",
    "http://img.chem.ucl.ac.uk/sgp/misc/pointgrp.htm",
    "http://img.chem.ucl.ac.uk/sgp/large/020az2.htm",
    "http://img.chem.ucl.ac.uk/sgp/large/020az3.htm",
    "http://img.chem.ucl.ac.uk/sgp/large/017b.htm",
    "http://img.chem.ucl.ac.uk/sgp/large/017c.htm",
    "http://img.chem.ucl.ac.uk/sgp/large/018bz1.htm",
    "http://img.chem.ucl.ac.uk/sgp/large/018cz1.htm",
    "http://img.chem.ucl.ac.uk/sgp/large/020ez1.htm",
    "http://img.chem.ucl.ac.uk/sgp/large/048bz2.htm",
]

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
            return True, rel, len(data)
        except Exception as e:
            last = e
            time.sleep(3 * (attempt + 1))
    return False, rel, str(last)

ok = 0
for u in FAILED:
    good, rel, info = save(u)
    print(("OK  " if good else "FAIL"), rel, f"({info} bytes)" if good else f"-> {info}", flush=True)
    if good:
        ok += 1
    time.sleep(2)
print(f"\nRetried {len(FAILED)}, succeeded {ok}")
