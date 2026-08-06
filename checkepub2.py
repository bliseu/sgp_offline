import zipfile, re
p = r"C:\Users\bli\sgp_offline\sgp_offline.epub"
z = zipfile.ZipFile(p)
names = z.namelist()
print("all entries sample:")
for n in names[:30]:
    print("  ", n)
print()
# find an xhtml chapter and inspect img tags
for n in names:
    if n.endswith(".xhtml"):
        content = z.read(n).decode("utf-8", "replace")
        imgs = re.findall(r'<img[^>]+src="([^"]+)"', content)
        print(f"{n}: img tags={len(imgs)}")
        for im in imgs[:5]:
            print("    src:", im)
        if imgs:
            break
