# -*- coding: utf-8 -*-
"""重建 sitemap.xml

规则：
  - 扫描 site/ 下所有 .html
  - 排除：404.html、baidu_verify_*.html、以及下划线开头的文件
  - 已存在于旧 sitemap 的页面保留原 lastmod；新页面用本次日期
  - 首页 priority 1.0，其余 0.7

用法：python rebuild_sitemap.py [新页面日期 YYYY-MM-DD]
"""
import os
SITE_URL = (os.environ.get("SITE_URL") or "https://example.com").rstrip("/") + "/"

import re
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.environ.get("SITE_DIR") or os.path.abspath(
    os.path.join(HERE, "..", "site"))
SM = os.path.join(SITE, "sitemap.xml")
TODAY = sys.argv[1] if len(sys.argv) > 1 else time.strftime("%Y-%m-%d")
# offline.html 是 Service Worker 离线回退页，不应被搜索引擎索引，故不进 sitemap
EXCLUDE = re.compile(r"^(404\.html|offline\.html|baidu_verify|_|google|bing|yandex)", re.I)


def main():
    # 读旧 lastmod
    old = {}
    if os.path.exists(SM):
        for m in re.finditer(r"<loc>(.*?)</loc><lastmod>(.*?)</lastmod>", open(SM, encoding="utf-8").read()):
            old[m.group(1)] = m.group(2)

    pages = sorted(f for f in os.listdir(SITE)
                   if f.endswith(".html") and not EXCLUDE.match(f))

    rows = []
    newcnt = 0
    for f in pages:
        # 首页固定用根路径，与线上既有 sitemap 保持一致（避免首页 URL 变动）
        url = SITE_URL if f == "index.html" else SITE_URL + f
        lm = old.get(url, TODAY)
        if url not in old:
            newcnt += 1
        pri = "1.0" if f == "index.html" else "0.7"
        rows.append('  <url><loc>%s</loc><lastmod>%s</lastmod>'
                    '<changefreq>weekly</changefreq><priority>%s</priority></url>'
                    % (url, lm, pri))

    xml = ('<?xml version="1.0" encoding="UTF-8"?>\n'
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
           + "\n".join(rows) + "\n</urlset>\n")
    with open(SM, "w", encoding="utf-8") as f:
        f.write(xml)
    print("sitemap 重建完成：共 %d 条（其中新增 %d 条）" % (len(rows), newcnt))
    print("  首条: %s" % rows[0].strip()[:100])
    print("  末条: %s" % rows[-1].strip()[:100])


if __name__ == "__main__":
    main()
