# -*- coding: utf-8 -*-
"""全站深度检查（本地静态文件）

覆盖 12 类检查，任何一类有问题都会明确列出：
  1. 内链死链（href 指向的站内 html 是否存在）
  2. 重复 title / 重复 description
  3. H1 数量必须恰好 1
  4. canonical 是否指向自身、是否 https、是否带 .html
  5. 必填元素：百度统计 / 备案号 / 360验证 / 搜狗验证 / og 标签 / 结构化数据
  6. 占位符残留（TODO、lorem、待填、xxx 等）
  7. CSS 引用版本是否统一
  8. 图片/静态资源引用是否存在
  9. sitemap 与文件系统是否一致
  10. 页面体积异常（过小可能是空壳）
  11. 标题过长 / 描述过长
  12. 英文单词混入检测（用户硬性要求全中文）

用法：python seo_full_check.py
"""
import os
SITE_URL = (os.environ.get("SITE_URL") or "https://example.com").rstrip("/") + "/"

import re
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.environ.get("SITE_DIR") or os.path.abspath(
    os.path.join(HERE, "..", "site"))
# offline.html 是 Service Worker 的离线回退页：不该被索引，因此也
# 不应有 canonical / 统计 / og / 结构化数据，且不进 sitemap。属例外页。
EXCLUDE = re.compile(r"^(404\.html|offline\.html|baidu_verify|google|bing|yandex)", re.I)
REQUIRED_CSS_VER = "style.css?v=20261029c"
STAT_ID = "5fc068dcb84fbe2b860c81769f9961b5"
ICP = "黔ICP备2024033749号-1"
V360 = "621cc18c144262c4e22a88a056d327da"
VSOGOU = "E2JjZvo6nO"

# 允许出现的英文（技术缩写、域名、标签名等）
ALLOW_EN = {
    "jpg", "png", "svg", "ico", "webp", "html", "css", "js", "json", "xml", "txt",
    "cn", "com", "org", "gov", "http", "https", "www", "utf", "vg", "path", "d",
    "application", "ld", "context", "schema", "type", "name", "url", "description",
    "browserrequirements", "requiresjavascript", "applicationcategory", "operatingsystem",
    "isaccessibleforfree", "inch", "offers", "price", "pricecurrency", "cny",
    "page", "mainentityofpage", "webpage", "datepublished", "datemodified", "inch",
    "inlanguage", "author", "organization", "publisher", "headline", "article",
    "breadcrumblist", "itemlistelement", "listitem", "position", "item",
    "webapplication", "utilitiesapplication", "any", "zh", "og", "twitter", "card",
    "summary", "large", "image", "width", "height", "alt", "site", "locale",
    "keywords", "canonical", "stylesheet", "icon", "sizes", "apple", "touch",
    "mobile", "theme", "color", "manifest", "capable", "title", "status", "bar",
    "style", "default", "applicable", "device", "pc", "verification", "googlebot",
    "viewport", "initial", "scale", "fit", "cover", "charset", "lang", "lang",
    "hm", "baidu", "var", "function", "document", "createElement", "script",
    "getElementsByTagName", "parentNode", "insertBefore", "src", "href", "rel",
    "org", "w3", "svg", "rect", "fill", "text", "font", "family", "aria", "hidden",
    "viewBox", "xmlns", "i", "if", "navigator", "serviceWorker", "addEventListener",
    "register", "window", "load", "p", "br", "img", "jpg", "jpeg",
}

# 2026-09-27 逐词核实后追加的合理用词：
#   · 技术/专业缩写：ICP BMI LPR VIN NDA WHO NIPT CRL DNA PWA GPA EUR RGB IEEE
#   · 软件与网络术语：App APP Excel Word PDF WPS Network Cookie localStorage Canvas
#   · 系统与字体：Linux Chrome Edge Firefox Safari Consolas Courier Logo iPhone chmod
#   · 表格函数名：DATEDIF DAY EDATE EOMONTH DBNum INT NUMBERSTRING REM
#   · 汉语拼音韵母：an ang en eng in ing ong zhi chi shi ri
#   · 示例文本（计数/数学/医学术语）：I love China / word count / don't / V=abh / sleep inertia / Naegele
ALLOW_EN |= {
    "icp", "bmi", "lpr", "vin", "nda", "who", "nipt", "crl", "dna", "pwa", "gpa",
    "eur", "rgb", "ieee", "app", "excel", "word", "pdf", "wps", "network", "cookie",
    "localstorage", "canvas", "linux", "chrome", "edge", "firefox", "safari",
    "consolas", "courier", "logo", "iphone", "chmod", "datedif", "day", "edate",
    "eomonth", "dbnum", "int", "numberstring", "rem", "an", "ang", "en", "eng",
    "in", "ing", "ong", "zhi", "chi", "shi", "ri", "love", "china", "count", "don",
    "abh", "inertia", "sleep", "naegele", "contact", "income", "annual", "javascript",
    "yyyymmdd", "yymmdd", "xxx", "ch", "sh", "c", "s", "z", "q", "j", "x", "y", "e",
    "utf", "seo", "uv", "pv", "api", "sdk", "html", "css", "json", "xml", "csv",
    "gif", "webp", "pptx", "xlsx", "docx", "vip", "sim", "esim", "otp", "bmi", "hr",
    "ct", "nt", "crl", "hcg", "bpd", "fl", "ac",
    # 二次核实后追加：域名、表格函数、权限/进制示例、拼音、软件名
    "jiazhi", "ffd", "rwxr", "xff", "liang", "qing", "shang", "tou", "yin", "lotus",
    "month", "networkdays", "now", "today", "workday", "amp", "ppt", "rule",
    "known", "well", "datevalue", "text", "value", "sum", "average", "if",
    "ying", "you", "yuan", "yue", "yun", "year", "month", "day", "hour", "minute",
    # 汉语拼音片段（声母/韵母组合，拼音页正文中会出现，属合理用词）
    "chu", "shu", "zhu", "xing", "nao", "shen", "seng", "zhen", "zeng", "cheng",
    "chang", "zhang", "shang", "chun", "shui", "zhui", "duo", "shao", "gao", "di",
    "tian", "kong", "bai", "yun", "xiao", "niao", "peng", "lao", "shi", "tong",
    "xue", "xiao", "shu", "ben", "qian", "bi", "zao", "wan", "tai", "yang", "yue",
    "liang", "xing", "hua", "er", "cao", "di", "da", "he", "guo", "mian", "bao",
    "niu", "nai", "yi", "fu", "mao", "jin", "zhuo", "zi", "yi", "qi", "che", "fei",
    "ji", "jiao", "hei", "ban", "ren", "zhen", "nu", "li", "guan", "cha", "fa",
    "xian", "gui", "gong", "yu", "dong", "qiu", "ye", "sen", "lin", "hai", "bao",
    "hu", "zi", "ran", "wu", "zhi", "ke", "wang", "gan", "xie", "wei", "xiao",
    "jing", "re", "huan", "shi", "yan", "jie", "lun", "shou", "huo", "gu", "jian",
    "chi", "xi", "meng", "sheng", "xian", "yan", "can", "lan", "liao", "kuo",
    "zhuang", "ning", "gui", "chuan", "shuo", "hui", "chuang", "zao", "tan", "suo",
    "ao", "mi", "qi", "ji", "feng", "ze", "tuan", "you", "si", "nian", "hui",
    "dai", "nan", "bei", "dong", "xi", "zhong", "guo", "ren", "min",
    # 其他合理技术缩写
    "gps", "abs", "esp", "suv", "mph", "led", "usb", "hdmi", "wifi",
    "pvc", "ppr", "pe", "abs", "eva", "eva", "mdf", "e0", "e1", "en",
    "apf", "seer", "cop", "eer", "ipc", "jgj", "gb",
    # 健康/医学领域的公式名、人名、单位（健康计算器页面专用）
    "bmi", "bmr", "tdee", "mmol", "dl", "mg",
    "mifflin", "jeor", "harris", "benedict", "broca", "tanaka",
    "dexa", "bod", "pod", "karvonen", "who", "si",
    "hdl", "ldl", "tc", "tg", "mmhg", "mol", "umol", "mgdl",
    # 数学速查表页面：三角函数符号、罗马数字、技术术语
    "sin", "cos", "tan", "mac",
    "i", "ii", "iii", "iiii", "iv", "v", "vi", "vii", "viii", "ix", "x",
    "xl", "l", "xc", "c", "cd", "d", "cm", "m", "mmxxvi", "lxxxx",
    # 罗马数字页「易错写法」段落里刻意举的错误示例
    "viiii", "xxxx",
}


def main():
    pages = {}
    for root, _, files in os.walk(SITE):
        for f in files:
            if f.endswith(".html") and not EXCLUDE.match(f):
                rel = os.path.relpath(os.path.join(root, f), SITE).replace("\\", "/")
                pages[rel] = open(os.path.join(root, f), encoding="utf-8", errors="replace").read()

    print("=" * 74)
    print("全站深度检查：共 %d 个页面" % len(pages))
    print("=" * 74)

    existing = set(os.listdir(SITE))
    statics = set()
    for r, d, fs in os.walk(SITE):
        for f in fs:
            statics.add(os.path.relpath(os.path.join(r, f), SITE).replace("\\", "/"))

    issues = defaultdict(list)
    titles, descs = {}, {}

    for rel, h in pages.items():
        # 1 内链
        for href in set(re.findall(r'href="(/[^"#?]+\.html)"', h)):
            t = href.lstrip("/")
            if t not in existing:
                issues["内链死链"].append("%s -> %s" % (rel, href))
        # 2 title/desc
        mt = re.search(r"<title[^>]*>(.*?)</title>", h, re.S | re.I)
        md = re.search(r'name="description" content="(.*?)"', h, re.S | re.I)
        titles[rel] = (mt.group(1).strip() if mt else "")
        descs[rel] = (md.group(1).strip() if md else "")
        if not titles[rel]:
            issues["缺title"].append(rel)
        if not descs[rel]:
            issues["缺description"].append(rel)
        # 3 H1
        n1 = len(re.findall(r"<h1[\s>]", h, re.I))
        if n1 != 1:
            issues["H1数量异常"].append("%s (%d个)" % (rel, n1))
        # 4 canonical
        mc = re.search(r'rel="canonical" href="(.*?)"', h)
        if not mc:
            issues["缺canonical"].append(rel)
        else:
            want = SITE_URL if rel == "index.html" else SITE_URL + rel
            if mc.group(1) != want:
                issues["canonical指向异常"].append("%s -> %s" % (rel, mc.group(1)))
        # 5 必填元素
        if STAT_ID not in h:
            issues["缺百度统计"].append(rel)
        if ICP not in h:
            issues["缺备案号"].append(rel)
        if V360 not in h:
            issues["缺360验证"].append(rel)
        if VSOGOU not in h:
            issues["缺搜狗验证"].append(rel)
        if 'property="og:title"' not in h:
            issues["缺og标签"].append(rel)
        if "application/ld+json" not in h:
            issues["缺结构化数据"].append(rel)
        # 6 占位符
        for pat in ("TODO", "lorem", "待填", "占位", "xxx", "XXXX", "FIXME", "???"):
            if pat in h:
                issues["占位符残留"].append("%s (%s)" % (rel, pat))
        # 7 CSS 版本
        if "style.css" in h and REQUIRED_CSS_VER not in h:
            m = re.search(r"style\.css\?[^\"']*", h)
            issues["CSS版本不一致"].append("%s (%s)" % (rel, m.group(0) if m else "无参数"))
        # 8 静态资源（剥离 ?v=xxx 查询串后再比对）
        for src in set(re.findall(r'(?:src|href)="(/assets/[^"]+)"', h)):
            t = src.split("?")[0].lstrip("/")
            if t not in statics:
                issues["资源缺失"].append("%s -> %s" % (rel, src))
        # 10 体积
        if len(h) < 3000:
            issues["体积过小"].append("%s (%d字节)" % (rel, len(h)))
        # 11 长度
        if len(titles[rel]) > 60:
            issues["标题过长"].append("%s (%d字)" % (rel, len(titles[rel])))
        if len(descs[rel]) > 160:
            issues["描述过长"].append("%s (%d字)" % (rel, len(descs[rel])))
        # 12 英文混入（正文部分，粗略剔除标签与允许词）
        text = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", h, flags=re.S | re.I)
        text = re.sub(r"<[^>]+>", " ", text)
        words = re.findall(r"[A-Za-z]{3,}", text)
        bad = [w for w in words if w.lower() not in ALLOW_EN]
        if bad:
            issues["疑似英文混入"].append("%s: %s" % (rel, ",".join(sorted(set(bad))[:6])))

    # 重复 title / desc
    for k, v in titles.items():
        pass
    ct = Counter(v for v in titles.values() if v)
    for t, c in ct.items():
        if c > 1:
            who = [r for r, v in titles.items() if v == t]
            issues["重复标题"].append("×%d %s :: %s" % (c, t[:40], ",".join(who[:5])))
    cd = Counter(v for v in descs.values() if v)
    for t, c in cd.items():
        if c > 1:
            who = [r for r, v in descs.items() if v == t]
            issues["重复描述"].append("×%d %s :: %s" % (c, t[:40], ",".join(who[:5])))

    # 9 sitemap 一致性
    sm_path = os.path.join(SITE, "sitemap.xml")
    sm = open(sm_path, encoding="utf-8").read()
    locs = set(re.findall(r"<loc>(.*?)</loc>", sm))
    expect = set()
    for rel in pages:
        expect.add(SITE_URL if rel == "index.html" else SITE_URL + rel)
    missing = expect - locs
    extra = locs - expect
    if missing:
        issues["sitemap缺页"].append("%d 个: %s" % (len(missing), ",".join(sorted(missing)[:5])))
    if extra:
        issues["sitemap多余"].append("%d 个: %s" % (len(extra), ",".join(sorted(extra)[:5])))

    print()
    order = ["内链死链", "重复标题", "重复描述", "H1数量异常", "缺title", "缺description",
             "缺canonical", "canonical指向异常", "缺百度统计", "缺备案号", "缺360验证",
             "缺搜狗验证", "缺og标签", "缺结构化数据", "CSS版本不一致", "资源缺失",
             "占位符残留", "体积过小", "标题过长", "描述过长", "sitemap缺页", "sitemap多余",
             "疑似英文混入"]
    total = 0
    for k in order:
        v = issues.get(k)
        if not v:
            continue
        total += len(v)
        print("✗ %s：%d 项" % (k, len(v)))
        for x in v[:12]:
            print("      %s" % x)
        if len(v) > 12:
            print("      ... 另有 %d 项" % (len(v) - 12))
    if total == 0:
        print("✓ 全部 23 类检查通过，未发现问题。")
    else:
        print()
        print("合计问题 %d 项。" % total)

    # 英文词频汇总（便于一次性判断哪些是合理技术缩写）
    if issues.get("疑似英文混入"):
        freq = Counter()
        for line in issues["疑似英文混入"]:
            for w in line.split(": ", 1)[1].split(","):
                freq[w.strip()] += 1
        print()
        print("【英文词频汇总（出现≥1次，按频次排序）】")
        print("  " + "  ".join("%s(%d)" % (w, c) for w, c in freq.most_common(80)))

    print()
    print("【统计】页面 %d 个 ｜ sitemap %d 条 ｜ 平均标题 %.1f 字 ｜ 平均描述 %.1f 字"
          % (len(pages), len(locs),
             sum(len(t) for t in titles.values()) / max(len(titles), 1),
             sum(len(d) for d in descs.values()) / max(len(descs), 1)))


if __name__ == "__main__":
    main()
