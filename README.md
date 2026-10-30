# 静态网站 SEO 检查脚本

纯静态站点（[jiazhi007.cn](https://jiazhi007.cn)）日常维护用的三个自查脚本，只用 Python 标准库，不联网。

| 脚本 | 作用 |
|---|---|
| `seo_full_check.py` | 23 类 SEO 检查：重复标题描述、H1、canonical、必填元素、内链死链、sitemap 一致性 |
| `audit_html_deep.py` | HTML 结构 7 项：标签配对、script 开闭、空区块、锚点、重复 id、单 H1 |
| `rebuild_sitemap.py` | 重建 sitemap.xml，已有页保留原 lastmod |

脚本在 [`github_repo/scripts/`](github_repo/scripts) 目录，详细说明见 [github_repo/README.md](github_repo/README.md)。

## 用法

```bash
SITE_DIR=/path/to/site SITE_URL=https://example.com python scripts/seo_full_check.py

