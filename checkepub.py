import zipfile, re
p = r"C:\Users\bli\sgp_offline\sgp_offline.epub"
z = zipfile.ZipFile(p)
names = z.namelist()
print("total entries:", len(names))
media = [n for n in names if n.startswith("media/")]
print("media (images):", len(media))
html = [n for n in names if n.endswith(".xhtml")]
print("xhtml chapters:", len(html))
# check a sample image entry size
if media:
    for n in media[:3]:
        print("  ", n, z.getinfo(n).file_size, "bytes")
# nav / toc
nav = [n for n in names if "nav" in n.lower() or "toc" in n.lower()]
print("nav/toc files:", nav)
# count nav point entries in toc.ncx or nav.xhtml
for n in names:
    if n.endswith("nav.xhtml"):
        content = z.read(n).decode("utf-8", "replace")
        print("nav links:", len(re.findall(r"<a[^>]+href=", content)))
        break
