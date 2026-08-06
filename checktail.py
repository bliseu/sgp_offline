import pypdf
r = pypdf.PdfReader(r"C:\Users\bli\sgp_offline\sgp_offline.pdf")
last = r.pages[-1].extract_text() or ""
print("last page text (tail):")
print(last[-400:])
