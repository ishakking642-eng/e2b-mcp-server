import json, os, time, threading, subprocess, urllib.request, urllib.parse
DATA = os.environ.get('GUARD_DATA', os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'guard_data'))
DATA = os.path.abspath(DATA)
os.makedirs(DATA, exist_ok=True)
PORT = int(os.environ.get('PORT', '8000'))
REPO = os.environ.get('GUARD_REPO', '/workspaces/e2b-mcp-server')
LOCK = threading.Lock()
def _f(n): return os.path.join(DATA, n)
def load(n, d):
    try:
        v = json.load(open(_f(n))); return v if isinstance(v, type(d)) else d
    except Exception: return d
def save(n, v):
    t = _f(n) + '.tmp'; json.dump(v, open(t, 'w'), ensure_ascii=False); os.replace(t, _f(n))
BLOCK = load('blocklist.json', {})
SEEN = load('seen.json', {})
HITS = load('hits.json', {})
LOG = load('log.json', [])
def jget(url, to=10):
    try:
        r = urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'ishak-guard'}), timeout=to)
        return json.loads(r.read().decode('utf-8', 'replace'))
    except Exception: return None
def ipinfo(ip):
    d = jget('http://ip-api.com/json/' + ip + '?fields=status,country,countryCode,isp,as,mobile,proxy')
    return d if d and d.get('status') == 'success' else None
def blocked(ip):
    return ip in BLOCK or ip.rsplit('.', 1)[0] in BLOCK
def logadd(e):
    with LOCK:
        LOG.insert(0, e); del LOG[200:]; save('log.json', LOG)
def evaluate(ip, events, do_block, src):
    if blocked(ip): return None
    info = {'ip': ip, 'events': events, 'src': src, 'ts': time.strftime('%Y-%m-%d %H:%M')}
    d = ipinfo(ip)
    if not d:
        info['error'] = 'lookup failed'; return info
    info['iso'] = d.get('countryCode'); info['country'] = d.get('country'); info['isp'] = d.get('isp')
    if d.get('mobile') or d.get('proxy') or 'cellular' in str(d.get('isp', '')).lower():
        info['skip'] = 'mobile/proxy'; return info
    with LOCK:
        if SEEN.get(ip) == events:
            HITS[ip] = HITS.get(ip, 0) + 1
        else:
            SEEN[ip] = events; HITS[ip] = 1
        hit = HITS[ip]
        save('seen.json', SEEN); save('hits.json', HITS)
    info['hit'] = hit
    if do_block and hit >= 2 and info['iso'] not in ('IL', 'US'):
        with LOCK:
            BLOCK[ip] = {'reason': '%s: %d events' % (src, events), 'country': info['iso'], 'added_utc': info['ts']}
            save('blocklist.json', BLOCK)
        info['ACTION'] = 'BLOCKED'
    return info
def scan_ulpen(octet, hours, do_block):
    r = jget('https://api.hackertarget.com/ulpen/?q=972.%s' % octet, to=20)
    out = []
    if not r: return None
    rec = ((r.get('data') or {}).get('records') or []) if isinstance(r, dict) else []
    for x in rec[:400]:
        h = (x.get('host') or '').lower()
        if 'ssh.rooter' not in h and 'barracudacentral' not in h: continue
        ip = '.'.join(h.split('.')[:4])
        e = evaluate(ip, 5, do_block, 'ulpen')
        if e: out.append(e)
    return out
def scan_feed(do_block):
    p = _f('incoming.txt')
    if not os.path.exists(p): return []
    out = []
    try:
        for line in open(p):
            w = line.split()
            if not w or w[0].startswith('#'): continue
            ip = w[0]
            if ip.count('.') != 3: continue
            try: n = int(w[1]) if len(w) > 1 and w[1].isdigit() else 5
            except Exception: n = 5
            e = evaluate(ip, n, do_block, 'feed')
            if e: out.append(e)
    except Exception: pass
    return out
def auto_loop():
    while True:
        time.sleep(600)
        try:
            scan_feed(True)
            scan_ulpen(os.environ.get('OCT', '1'), 6, True)
        except Exception: pass
def git_loop():
    while True:
        time.sleep(600)
        try:
            tok = os.environ.get('GITHUB_TOKEN', '')
            sub = subprocess.run
            sub(['git', '-C', REPO, 'remote', 'set-url', 'origin',
                 'https://x-access-token:%s@github.com/ishakking642-eng/e2b-mcp-server.git' % tok], capture_output=True)
            sub(['git', '-C', REPO, 'add', '-A', 'ops/guard_data'], capture_output=True)
            r = sub(['git', '-C', REPO, '-c', 'user.email=guard@ishak.dev', '-c', 'user.name=ishak-guard',
                     'commit', '-m', 'guard data ' + time.strftime('%FT%TZ')], capture_output=True)
            if r.returncode == 0:
                sub(['git', '-C', REPO, 'push', '-q', 'origin', 'HEAD:main'], capture_output=True)
        except Exception: pass
threading.Thread(target=auto_loop, daemon=True).start()
threading.Thread(target=git_loop, daemon=True).start()
async def app(scope, receive, send):
    if scope['type'] != 'http': return
    path = scope['path'].rstrip('/') or '/'
    q = urllib.parse.parse_qs(scope.get('query_string', b'').decode())
    def g(k, d=''):
        return (q.get(k) or [d])[0]
    body = b''
    while True:
        m = await receive()
        body += m.get('body', b'')
        if not m.get('more_body'): break
    loop = _asyncio.get_event_loop()
    res = await loop.run_in_executor(None, _handle, path, g, body.decode('utf-8', 'replace'))
    code, data = res
    raw = json.dumps(data, ensure_ascii=False).encode()
    await send({'type': 'http.response.start', 'status': code, 'headers': [(b'content-type', b'application/json; charset=utf-8'), (b'access-control-allow-origin', b'*')]})
    await send({'type': 'http.response.body', 'body': raw})
def _handle(path, g, body):
    if path in ('/', '/healthz'):
        return 200, {'ok': True, 'svc': 'ishak-guard', 'time_utc': time.strftime('%F %T'), 'blocklist': len(BLOCK), 'seen': len(SEEN), 'log': len(LOG)}
    if path == '/tools':
        return 200, [p for p in _ROUTES]
    if path == '/guard/status':
        return 200, {'ok': True, 'blocklist': len(BLOCK), 'seen': len(SEEN), 'hits': len(HITS), 'time_utc': time.strftime('%F %T')}
    if path == '/guard/whois':
        out = {}
        for ip in [x.strip() for x in g('ips').split(',') if x.strip()][:30]:
            d = ipinfo(ip)
            out[ip] = d and {'iso': d.get('countryCode'), 'country': d.get('country'), 'isp': d.get('isp'), 'asn': d.get('as'), 'blocked': blocked(ip)} or {'error': 'fail'}
        return 200, out
    if path == '/guard/scan':
        do_b = g('block', '1') != '0'
        n = int(g('n', '5') or 5)
        fed = []
        for ip in [x.strip() for x in g('ips').split(',') if x.strip()][:50]:
            e = evaluate(ip, n, do_b, 'manual')
            if e: fed.append(e)
        feed = scan_feed(do_b)
        ul = scan_ulpen(g('oct', '1'), 6, do_b)
        return 200, {'manual': fed, 'feed': feed, 'ulpen': ul if ul is not None else 'unreachable', 'blocklist': len(BLOCK)}
    if path == '/guard/ingest':
        try:
            j = json.loads(body) if body.strip().startswith('{') else {}
            ips = j.get('ips') or []
        except Exception:
            ips = body.split()
        c = 0
        with LOCK:
            for ip in ips:
                ip = str(ip).strip()
                if ip.count('.') != 3: continue
                p = _f('incoming.txt'); ex = open(p).read() if os.path.exists(p) else ''
                if ip in ex: continue
                open(p, 'a').write(ip + ' 8 #ingest\n'); c += 1
        return 200, {'queued': c}
    if path == '/guard/log':
        return 200, LOG[:int(g('limit', '25') or 25)]
    if path == '/guard/stats':
        by = {}
        for e in LOG:
            k = e.get('iso') or ('ERR' if e.get('error') else '?')
            by[k] = by.get(k, 0) + 1
        return 200, {'events_by_country': by, 'blocklist': len(BLOCK), 'logged': len(LOG)}
    if path == '/guard/blocklist':
        return 200, BLOCK
    if path == '/guard/watch':
        ip = g('ip')
        with LOCK:
            BLOCK[ip] = {'reason': g('reason', 'manual'), 'added_utc': time.strftime('%F %H:%M')}; save('blocklist.json', BLOCK)
        logadd({'ip': ip, 'ACTION': 'MANUAL-BLOCK', 'reason': g('reason', 'manual')})
        return 200, {'blocked': ip, 'blocklist': len(BLOCK)}
    if path == '/guard/unwatch':
        ip = g('ip')
        with LOCK:
            r = BLOCK.pop(ip, None); save('blocklist.json', BLOCK)
        return 200, {'removed': bool(r), 'blocklist': len(BLOCK)}
    if path == '/guard/scan':
        do_b = g('block', '1') != '0'
        try: n = int(g('n', '8') or 8)
        except Exception: n = 8
        out = []
        for ip in [x.strip() for x in g('ips').split(',') if x.strip()][:40]:
            e = evaluate(ip, n, do_b, 'manual')
            if e: out.append(e)
        return 200, {'checked': len(out), 'items': out, 'blocklist': len(BLOCK)}
    if path == '/guard/feed':
        do_b = g('block', '1') != '0'
        res = scan_feed(do_b)
        return 200, {'processed': len(res), 'items': res, 'blocklist': len(BLOCK)}
    return 404, {'error': 'no route', 'path': path}
import asyncio as _asyncio
_ROUTES = ['/healthz', '/tools', '/guard/scan', '/guard/feed', '/guard/status', '/guard/whois', '/guard/ingest', '/guard/log', '/guard/stats', '/guard/blocklist', '/guard/watch', '/guard/unwatch']
if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=PORT, log_level='warning')
