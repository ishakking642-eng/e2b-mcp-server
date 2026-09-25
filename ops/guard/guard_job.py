#!/usr/bin/env python3
"""ishak-guard serverless job (run by GitHub Actions cron).
Reads ops/guard_data/*, evaluates threat feed, updates blocklist, writes state.
No secrets needed beyond optional GUARD_SOURCES env.
"""
import json, os, sys, time, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
DATA = os.path.join(ROOT, 'ops', 'guard_data')
os.makedirs(DATA, exist_ok=True)
NOW = time.time()
DAY = time.strftime('%Y-%m-%d %H:%M', time.gmtime(NOW))
SOURCES = [s for s in os.environ.get('GUARD_SOURCES', '').replace('\n', ' ').split() if s.startswith('http')]

def _f(n): return os.path.join(DATA, n)
def load(n, d):
    try:
        v = json.load(open(_f(n))); return v if isinstance(v, type(d)) else d
    except Exception: return d
def save(n, v):
    t = _f(n) + '.tmp'; json.dump(v, open(t, 'w'), ensure_ascii=False, indent=1); os.replace(t, _f(n))

BLOCK = load('blocklist.json', {})
SEEN = load('seen.json', {})
HITS = load('hits.json', {})
LOG = load('log.json', [])

def http(url, to=12, as_json=True):
    try:
        r = urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 ishak-guard'}), timeout=to)
        b = r.read()
        return json.loads(b.decode('utf-8', 'replace')) if as_json else b.decode('utf-8', 'replace')
    except Exception as e:
        return None

def ipinfo(ip):
    d = http('http://ip-api.com/json/' + ip + '?fields=status,country,countryCode,isp,as,mobile,proxy')
    return d if d and d.get('status') == 'success' else None

def blocked(ip):
    return ip in BLOCK or ip.rsplit('.', 1)[0] in BLOCK

STRICT = os.environ.get('GUARD_STRICT') == '1'

def evaluate(ip, events, src):
    if blocked(ip) or not STRICT:
        return None
    info = {'ip': ip, 'events': events, 'src': src, 'ts': DAY}
    d = ipinfo(ip)
    if not d:
        info['error'] = 'lookup failed'; return info
    info['iso'] = d.get('countryCode'); info['country'] = d.get('country'); info['isp'] = d.get('isp')
    if d.get('mobile') or d.get('proxy') or 'cellular' in str(d.get('isp', '')).lower():
        info['skip'] = 'mobile/proxy'; return info
    if SEEN.get(ip) == events:
        HITS[ip] = HITS.get(ip, 0) + 1
    else:
        SEEN[ip] = events; HITS[ip] = 1
    hit = HITS[ip]; info['hit'] = hit
    if hit >= 2 and info['iso'] not in ('IL', 'US'):
        BLOCK[ip] = {'reason': '%s: %s events' % (src, events), 'country': info['iso'], 'added_utc': DAY}
        info['ACTION'] = 'BLOCKED'
    return info

def parse_feed(text):
    out = []
    for line in (text or '').splitlines():
        w = line.split()
        if not w or w[0].startswith('#'): continue
        ip = w[0]
        if ip.count('.') != 3: continue
        n = int(w[1]) if len(w) > 1 and w[1].isdigit() else 8
        out.append((ip, n))
    return out

def main():
    results, sources_ok = [], []
    feed = parse_feed(open(_f('incoming.txt')).read() if os.path.exists(_f('incoming.txt')) else '')
    for src in SOURCES:
        t = http(src, to=15, as_json=False)
        if t:
            sources_ok.append(src)
            feed += parse_feed(t)
    seen = set()
    for ip, n in feed:
        if ip in seen: continue
        seen.add(ip)
        e = evaluate(ip, n, 'feed')
        if e: results.append(e)
    for e in results:
        LOG.insert(0, e)
    del LOG[250:]
    save('blocklist.json', BLOCK); save('seen.json', SEEN); save('hits.json', HITS); save('log.json', LOG)
    st = {'updated_utc': DAY, 'strict': STRICT, 'blocklist': len(BLOCK), 'logged': len(LOG),
          'scanned': len(seen), 'sources_ok': sources_ok, 'blocked_total': sum(1 for v in BLOCK.values())}
    save('status.json', st)
    print(json.dumps(st, ensure_ascii=False))
    if any(r.get('ACTION') for r in results):
        print('NEW BLOCKS:', [r['ip'] for r in results if r.get('ACTION') == 'BLOCKED'])

if __name__ == '__main__':
    main()
