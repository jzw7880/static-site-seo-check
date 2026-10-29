# 静态站 SEO 与结构自查脚本

做了个纯静态的工具站（[价值007工具箱](https://jiazhi007.cn)，两百来个页面、没有后端），
维护过程中写了几个自查脚本，抽出来公开，改改就能用在别的静态站上。

只用 Python 标准库，不用装依赖。

## 三个脚本

| 脚本 | 干什么 |
|------|--------|
| `scripts/seo_full_check.py` | 23 类 SEO 检查：重复 title/description、H1 数量、canonical 指向、必填元素（统计代码/备案/og/结构化数据）、占位符残留、内链死链、sitemap 与实际文件是否一致、标题描述长度、疑似英文混入等 |
| `scripts/audit_html_deep.py` | HTML 结构 7 项：标签配对、script/style 开闭数量、空区块、页内锚点目标、重复 id、`<b>` 嵌套、是否恰好一个 H1 |
| `scripts/rebuild_sitemap.py` | 扫描目录重建 sitemap.xml，已存在的页面保留原 lastmod，只给新页面写今天 |

## 用法

```bash
SITE_DIR=/path/to/site SITE_URL=https://example.com python scripts/seo_full_check.py
SITE_DIR=/path/to/site python scripts/audit_html_deep.py
SITE_DIR=/path/to/site python scripts/rebuild_sitemap.py
```

不传环境变量时，默认读仓库根目录下的 `site/`。

## 为什么写这两个检查

静态站没有 CMS 兜底，最容易出的是三类问题，而且都不报错：

1. **手工改页面改坏标签** —— 多一个 `</b>`，浏览器照常渲染，肉眼看不出来
2. **重复内容** —— 模板生成的长尾页，正文只差几个数字，搜索引擎会判重
3. **内链指向已删除的页面** —— 页面还在，链接 404，用户点了才发现

`seo_full_check.py` 里的「疑似英文混入」那条，是因为中文站偶尔会把统计代码、
模板变量漏在正文里。规则是可配置的白名单，直接改成自己的即可。

## 说明

- 脚本按具体站点写的，`REQUIRED_CSS_VER`、必填元素清单这类常量需要按自己的站改
- 不联网、不上传任何数据，纯本地读文件

## License

MIT
