# -*- coding: utf-8 -*-
"""HTML 结构深度审计：标签配对、script 配对、空块、锚点目标、重复 id、b 标签嵌套"""
import os, re, glob, sys, collections

SITE = os.environ.get("SITE_DIR") or os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'site')
VOID = {'br','img','input','meta','link','hr','area','base','col','embed','source','track','wbr','param'}
SKIP = {'404.html', 'offline.html'}

def pages():
    out = []
    for p in sorted(glob.glob(os.path.join(SITE, '*.html'))):
        n = os.path.basename(p)
        if n in SKIP: continue
        if n.startswith('baidu_verify_') or n.startswith('google') or n.startswith('sogou') or n.startswith('360'): continue
        out.append(p)
    return out

def strip_code(h):
    h = re.sub(r'<script\b[^>]*>.*?</script>', '', h, flags=re.S | re.I)
    h = re.sub(r'<style\b[^>]*>.*?</style>', '', h, flags=re.S | re.I)
    h = re.sub(r'<!--.*?-->', '', h, flags=re.S)
    return h

def check_tags(h, name, issues):
    s = strip_code(h)
    stack = []
    for m in re.finditer(r'<(/?)([a-zA-Z][a-zA-Z0-9]*)([^>]*?)(/?)>', s):
        close, tag, attrs, selfclose = m.group(1), m.group(2).lower(), m.group(3), m.group(4)
        if tag in VOID or selfclose: continue
        if not close:
            stack.append((tag, m.start()))
        else:
            if not stack:
                issues.append((name, '多余闭合 </%s>@%d' % (tag, m.start())))
            elif stack[-1][0] == tag:
                stack.pop()
            else:
                # 回退查找
                idx = -1
                for i in range(len(stack) - 1, -1, -1):
                    if stack[i][0] == tag:
                        idx = i; break
                if idx < 0:
                    issues.append((name, '多余闭合 </%s>@%d' % (tag, m.start())))
                else:
                    unclosed = ','.join(t for t, _ in stack[idx+1:])
                    issues.append((name, '</%s> 交叉闭合，未闭合: %s' % (tag, unclosed)))
                    del stack[idx:]
    if stack:
        issues.append((name, '未闭合: ' + ','.join('%s@%d' % (t, p) for t, p in stack[:6])))

def main():
    files = pages()
    print('=== 1. HTML 标签配对（%d 页）===' % len(files))
    issues = []
    cache = {}
    for p in files:
        h = open(p, encoding='utf-8', errors='replace').read()
        cache[p] = h
        check_tags(h, os.path.basename(p), issues)
    if issues:
        for n, msg in issues: print('  x %-34s %s' % (n, msg))
    else:
        print('  全部通过')
    print('  问题: %d' % len(issues))

    print('\n=== 2. script / style 开闭配对 ===')
    bad = []
    for p, h in cache.items():
        for tag in ('script', 'style'):
            op = len(re.findall(r'<%s\b' % tag, h, re.I))
            cl = len(re.findall(r'</%s>' % tag, h, re.I))
            if op != cl:
                bad.append((os.path.basename(p), tag, op, cl))
    if bad:
        for n, t, o, c in bad: print('  x %-34s <%s> 开%d 闭%d' % (n, t, o, c))
    else:
        print('  全部配对')

    print('\n=== 3. 空区块 / 空容器（排除带 id 的 JS 输出位）===')
    empty = []
    for p, h in cache.items():
        s = strip_code(h)
        for m in re.finditer(r'<(section|div|p|ul|ol|table)([^>]*)>\s*</\1>', s, re.I):
            if 'id=' in m.group(2) or 'id =' in m.group(2):
                continue
            empty.append((os.path.basename(p), m.group(0)[:60]))
            break
    if empty:
        for n, frag in empty: print('  x %-34s %s' % (n, frag))
    else:
        print('  无空区块')

    print('\n=== 4. 页内锚点目标存在性 ===')
    miss = []
    for p, h in cache.items():
        ids = set(re.findall(r'\bid\s*=\s*["\']([^"\']+)["\']', h))
        for m in re.finditer(r'href\s*=\s*["\']#([^"\'!][^"\']*)["\']', h):
            t = m.group(1)
            if t and t not in ids:
                miss.append((os.path.basename(p), '#' + t))
    if miss:
        for n, t in miss[:30]: print('  x %-34s %s' % (n, t))
    else:
        print('  全部有目标')

    print('\n=== 5. 重复 id ===')
    dup = []
    for p, h in cache.items():
        ids = re.findall(r'\bid\s*=\s*["\']([^"\']+)["\']', h)
        c = collections.Counter(ids)
        d = [k for k, v in c.items() if v > 1]
        if d: dup.append((os.path.basename(p), d[:5]))
    if dup:
        for n, d in dup: print('  x %-34s %s' % (n, d))
    else:
        print('  无重复 id')

    print('\n=== 6. <b> 嵌套 ===')
    nest = []
    for p, h in cache.items():
        s = strip_code(h)
        for m in re.finditer(r'<b\b[^>]*>([^<]*)<b\b', s):
            nest.append(os.path.basename(p)); break
    if nest:
        for n in nest: print('  x %s' % n)
    else:
        print('  无嵌套')

    print('\n=== 7. 标题层级（单 H1）===')
    h1bad = []
    for p, h in cache.items():
        s = strip_code(h)
        n = len(re.findall(r'<h1\b', s, re.I))
        if n != 1: h1bad.append((os.path.basename(p), n))
    if h1bad:
        for n, c in h1bad: print('  x %-34s H1=%d' % (n, c))
    else:
        print('  全部恰好 1 个 H1')

    total = len(issues) + len(bad) + len(empty) + len(miss) + len(dup) + len(nest) + len(h1bad)
    print('\n合计数问题: %d' % total)
    return 0 if total == 0 else 1

if __name__ == '__main__':
    sys.exit(main())
