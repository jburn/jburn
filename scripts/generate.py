"""Public-only GitHub dashboard. Python standard library; no runtime dependencies."""
import argparse
import calendar
from collections import Counter
from datetime import datetime, timezone
from html import escape
import json
import os
from pathlib import Path
import re
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
BG, PANEL, BORDER, FG, MUTED, ACCENT = '#0b1628', '#12243d', '#29496b', '#e6f1ff', '#a3bbd8', '#8cc8ff'


class API:
    def get(self, path):
        headers = {'User-Agent': 'jburn-profile-dashboard', 'Accept': 'application/vnd.github+json', 'X-GitHub-Api-Version': '2022-11-28'}
        if os.environ.get('GITHUB_TOKEN'):
            headers['Authorization'] = 'Bearer ' + os.environ['GITHUB_TOKEN']
        for attempt in range(4):
            try:
                with urllib.request.urlopen(urllib.request.Request('https://api.github.com' + path, headers=headers), timeout=30) as response:
                    return json.load(response), response.headers.get('Link', '')
            except urllib.error.HTTPError as error:
                if error.code in (403, 429, 500, 502, 503, 504) and attempt < 3:
                    delay = int(error.headers.get('Retry-After', '0'))
                    if error.headers.get('X-RateLimit-Remaining') == '0':
                        delay = max(delay, int(error.headers.get('X-RateLimit-Reset', '0')) - int(time.time()) + 1)
                    if delay > 60:
                        raise RuntimeError('GitHub rate limit reached; retry later or provide GITHUB_TOKEN') from None
                    time.sleep(max(delay, 2 ** attempt))
                    continue
                raise

    def pages(self, path):
        rows = []
        while path:
            data, link = self.get(path)
            rows.extend(data)
            next_link = re.search(r'<https://api.github.com([^>]+)>; rel="next"', link)
            path = next_link.group(1) if next_link else None
        return rows


def month_keys(now):
    index = now.year * 12 + now.month - 1
    return [f'{i // 12:04d}-{i % 12 + 1:02d}' for i in range(index - 11, index + 1)]


def collect(config, now, api):
    user = config['username']
    repos = api.pages(f'/users/{user}/repos?type=owner&per_page=100')
    public = [r for r in repos if not r.get('private') and r['owner']['login'].lower() == user.lower()]
    selected = [r for r in public if r['name'] not in config['exclude_repositories'] and not (config['exclude_forks'] and r['fork'])]
    languages, commits, days = Counter(), {}, set()
    months = month_keys(now)
    since = months[0] + '-01T00:00:00Z'
    until = now.isoformat().replace('+00:00', 'Z')
    for repo in selected:
        base = f"/repos/{user}/{urllib.parse.quote(repo['name'])}"
        langs, _ = api.get(base + '/languages')
        languages.update(langs)
        if repo['size'] == 0:
            continue
        query = urllib.parse.urlencode({'author': user, 'since': since, 'until': until, 'per_page': 100})
        try:
            rows = api.pages(base + '/commits?' + query)
        except urllib.error.HTTPError as error:
            if error.code == 409:  # GitHub's empty-repository response
                continue
            raise
        for commit in rows:
            if (commit.get('author') or {}).get('login', '').lower() != user.lower():
                continue
            # Bucket by committer date, matching REST since/until filtering.
            date = commit['commit']['committer']['date']
            if since <= date <= until and date[:7] in months:
                commits[commit['sha']] = date
    activity = Counter(date[:7] for date in commits.values())
    days.update(date[:10] for date in commits.values())
    return {'as_of': now.date().isoformat(), 'window_start': since[:10], 'public_repositories': len(public),
            'included_repositories': len(selected), 'stars': sum(r['stargazers_count'] for r in selected),
            'languages': dict(sorted(languages.items(), key=lambda item: (-item[1], item[0]))),
            'monthly_commits': {month: activity[month] for month in months}, 'commits': len(commits),
            'active_days': len(days), 'projects': [{k: r[k] for k in ('name', 'description', 'html_url', 'language')} for r in selected if r['name'] in config['featured']]}


def text(x, y, value, size=14, color=FG, weight=400):
    return f'<text x="{x}" y="{y}" fill="{color}" font-size="{size}" font-weight="{weight}" font-family="Arial, sans-serif">{escape(str(value))}</text>'


def rect(x, y, w, h, fill=PANEL, radius=12):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" fill="{fill}"/>'


def svg(width, height, title, body):
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img"><title>{escape(title)}</title>{rect(0,0,width,height,BG)}{body}</svg>\n'


def write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists() or path.read_text(encoding='utf-8') != content:
        path.write_text(content, encoding='utf-8', newline='\n')


def badge(label, slug, color):
    icon = ET.parse(ROOT / 'assets/icons' / (slug + '.svg')).getroot()
    viewbox = icon.get('viewBox', '0 0 24 24').split()
    if slug == 'openai':
        viewbox = ['180', '180', '365', '365']  # Trim whitespace in the preserved original mark.
    scale = 18 / float(viewbox[2])
    content = ''.join(ET.tostring(child, encoding='unicode') for child in icon if child.tag.endswith(('path', 'g', 'mask', 'defs', 'polygon', 'rect', 'circle')))
    width = 46 + len(label) * 7.4
    body = f'<rect x="0.5" y="0.5" width="{width-1}" height="31" rx="16" fill="{PANEL}" stroke="{BORDER}"/><g transform="translate(11 7) scale({scale}) translate({-float(viewbox[0])} {-float(viewbox[1])})" fill="#{color}">{content}</g>' + text(37,21,label,12)
    return svg(width,32,label,body).replace(rect(0,0,width,32,BG), '')


def render(config, data):
    out = ROOT / 'assets/generated'
    header = text(24,32,'JUHO BRUUN  /  FINLAND',12,ACCENT,700) + text(24,75,'Software engineer',32,FG,700) + text(24,108,'I enjoy creating software, graphics and learning new things.',16,MUTED) + rect(24,132,672,34) + text(38,154,'$ status  ·  building',13,ACCENT)
    write(out/'header.svg',svg(720,186,'Juho Bruun - Software engineer',header))
    body = text(24,32,'01 / CODE COMPOSITION',12,ACCENT,700) + text(24,55,f"Public owned repositories · {data['as_of']}",12,MUTED)
    for i,(label,value) in enumerate([('PUBLIC REPOS',data['public_repositories']),('STARS',data['stars']),('LANGUAGES',len(data['languages']))]):
        x=24+i*224
        body += rect(x,72,208,64) + text(x+14,96,label,11,MUTED) + text(x+14,121,value,22,FG,700)
    total=sum(data['languages'].values())
    language_colors = json.loads((ROOT/'assets/language-colors.json').read_text(encoding='utf-8'))
    shown=list(data['languages'].items())[:6]
    remainder=sum(v for _,v in list(data['languages'].items())[6:])
    if remainder: shown.append(('Other',remainder))
    x=24
    for i,(name,value) in enumerate(shown):
        color = language_colors.get(name, '#a3bbd8')
        width=672*value/total if total else 0
        body+=rect(x,158,width,16,color,0)
        x+=width
        y=205+i*29
        body+=rect(24,y-10,8,8,color,2)+text(42,y,name,13)+text(609,y,f'{value/total:.1%}',13,MUTED)
    if not total: body+=text(24,205,'No language bytes reported by GitHub.',13,MUTED)
    height=240+max(1,len(shown))*29
    body+=text(24,height-24,f"{data['included_repositories']} included repos · byte counts, not proficiency",12,MUTED)
    write(out/'languages.svg',svg(720,height,'GitHub code composition by language byte count',body))
    body=text(24,32,'02 / COMMIT ACTIVITY',12,ACCENT,700)+text(24,57,f"{data['commits']} commits · {data['active_days']} active UTC days",20,FG,700)
    values=list(data['monthly_commits'].values()); peak=max(values,default=0)
    for i,(month,value) in enumerate(data['monthly_commits'].items()):
        x=28+i*56; height=110*value/peak if peak else 0
        body+=rect(x,90,34,110,PANEL,4)
        if height: body+=rect(x,200-height,34,height,ACCENT,4)
        body+=text(x,82,value,11,MUTED)+text(x,222,calendar.month_abbr[int(month[5:])],11,MUTED)+text(x,238,month[2:4],10,MUTED)
    body+=text(24,270,f"{data['window_start']} → {data['as_of']} · current month is partial",12,MUTED)+text(24,292,'Owned public repos · default branches · account-attributed commits',12,MUTED)
    write(out/'activity.svg',svg(720,314,'Monthly authored commit activity, current month partial',body))
    for group,technologies in config['technologies'].items():
        for technology in technologies:
            label, slug, color = technology[:3]
            asset_name = technology[3] if len(technology) > 3 else slug
            write(out/(asset_name+'.svg'),badge(label,slug,color))
    projects={p['name']:p for p in data['projects']}
    for name in config['featured']:
        project=projects.get(name)
        if not project: raise ValueError(f'Featured project missing: {name}')
        desc=project['description'] or 'No repository description provided.'
        import textwrap
        lines=textwrap.wrap(desc,width=43)
        body=text(20,34,name,20,FG,700)
        for i,line in enumerate(lines): body+=text(20,64+i*20,line,13,MUTED)
        body+=rect(20,128,94,28)+text(32,147,project['language'] or 'Source',12,ACCENT)+text(320,147,'↗',18,ACCENT)
        write(out/(name+'.svg'),svg(360,176,name+' — '+desc,body))
    write(out/'stats.json',json.dumps(data,indent=2,ensure_ascii=False)+'\n')


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--from-snapshot',action='store_true',help='Render existing public aggregate snapshot without API requests')
    parser.add_argument('--date',help='UTC snapshot date, YYYY-MM-DD (defaults to current UTC date)')
    args=parser.parse_args()
    config=json.loads((ROOT/'profile.json').read_text(encoding='utf-8'))
    now=datetime.fromisoformat(args.date).replace(tzinfo=timezone.utc,hour=23,minute=59,second=59) if args.date else datetime.now(timezone.utc)
    data=json.loads((ROOT/'assets/generated/stats.json').read_text(encoding='utf-8')) if args.from_snapshot else collect(config,now,API())
    render(config,data)
    print(f"Generated public dashboard: {data['public_repositories']} repositories, {data['commits']} commits; as of {data['as_of']}")


if __name__ == '__main__':
    main()
