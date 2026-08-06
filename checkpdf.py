import pypdf
r = pypdf.PdfReader(r"C:\Users\bli\sgp_offline\sgp_offline.pdf")
print("pages:", len(r.pages))
for i in range(3):
    print(f"--- page {i+1} ---")
    print((r.pages[i].extract_text() or "")[:600])
