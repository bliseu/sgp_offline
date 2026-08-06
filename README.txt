UCL Space Group Diagrams & Tables — 离线包
==========================================
来源: http://img.chem.ucl.ac.uk/sgp/large/sgp.htm
     "High-Resolution Space Group Diagrams and Tables" (230 个空间群, 高分辨率图)
作者/版权: Jeremy Karl Cockcroft, Birkbeck College, University of London, 1997-1999.
          本离线副本仅供个人离线参考使用。

内容
----
  1) sgp_offline.pdf      ~34.7 MB, 约 1557 页, A4 横向。
     适合桌面/打印/普通阅读器。封面 + 按晶系组织的完整目录(可点内链跳转)。
  2) sgp_offline.epub     24.4 MB, 242 章, 837 张图。
     适合手机/电子书阅读器(如 Calibre, Apple Books, KOReader)。目录可导航。
  3) mirror\              ~59 MB 完整离线镜像(约 5000 个文件)。
     直接双击 mirror\large\sgp.htm 即可离线浏览原网站(高分辨率图 + 全部备选
     原点/轴向设置 + misc 图例页)。
  4) mirror\large\combined.html
     所有 230 组拼接成的单个 HTML(412 KB), 可离线打开或再次转 PDF/EPUB。

空间群内容
----------
每个空间群包含若干页:
   - 对称图 (对称元素 + 一般位置投影的大图)
   - 另一视角/大晶胞的对称图
   - 晶格类型 + 对称操作 (对称操作符坐标表)

重建方法(如需重新生成)
----------------------
  mirror.py / crawl.py   下载镜像(全站爬虫)
  retry.py / mopup.py    补抓失败/缺失文件
  verify.py              校验镜像完整性
  build_ebook.py         生成 combined.html
  Edge 无头打印:
    msedge --headless=new --no-pdf-header-footer
           --print-to-pdf=sgp_offline.pdf mirror\large\combined.html
  pandoc 生成 EPUB:
    cd mirror\large
    pandoc combined.html -o sgp_offline.epub --toc --split-level=2

日期: 2026-08-06
