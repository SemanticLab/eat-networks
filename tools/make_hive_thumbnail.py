"""Render an animated thumbnail of artworks-hive: empty hive, then one
bridging person at a time, then everything.

Usage (from the repo root, with the repo served on 127.0.0.1:8799):
    python3 -m http.server 8799 --bind 127.0.0.1 &
    uv run --with playwright tools/make_hive_thumbnail.py /tmp/hive-frames
    # then assemble, e.g.
    cd /tmp/hive-frames && ffmpeg -f concat -safe 0 -i list.txt -vf \
      "scale=600:600:flags=lanczos,split[a][b];[a]palettegen=stats_mode=diff[p];[b][p]paletteuse=dither=sierra2_4a" \
      -loop 0 img/artworks-hive.gif
Needs `playwright install chromium` once.
"""
import json, sys
from pathlib import Path
from playwright.sync_api import sync_playwright

OUT = Path(sys.argv[1]); OUT.mkdir(exist_ok=True)
for f in OUT.glob('*.png'): f.unlink()
SIZE = 1000
frames = []  # (filename, duration_ms)

SETUP_JS = """
() => {
  for (const sel of ['#panel', '#title', '#tooltip']) { const el = document.querySelector(sel); if (el) el.style.display = 'none'; }
  const style = document.createElement('style');
  style.textContent = `
    #hive .link { opacity: 0 !important; transition: none !important; }
    #hive .link.shown { opacity: 0.4 !important; }
    #hive .link.hl { opacity: 0.95 !important; stroke-width: 2px !important; }
    #hive.focus .node { opacity: 0.35 !important; }
    #hive.focus .node.hl { opacity: 1 !important; }
    #hive.focus .axis-label { opacity: 0.5 !important; }
  `;
  document.head.appendChild(style);
}
"""

GROUP_JS = """
() => {
  const svg = document.getElementById('hive');
  const paths = [...svg.querySelectorAll('path.link')];
  paths.forEach((p, i) => p.dataset.i = i);
  const seen = new Set(); const groups = [];
  for (const c of svg.querySelectorAll('circle.node')) {
    c.dispatchEvent(new Event('mouseenter'));
    const ids = [...svg.querySelectorAll('path.link.hl')].map(p => +p.dataset.i);
    const dots = [...svg.querySelectorAll('circle.node.hl')].length;
    c.dispatchEvent(new Event('mouseleave'));
    if (!ids.length) continue;
    const key = ids.join(',');
    if (seen.has(key)) continue;
    seen.add(key);
    groups.push({ ids, dots, circle: [...svg.querySelectorAll('circle.node')].indexOf(c) });
  }
  groups.sort((a, b) => b.ids.length - a.ids.length);
  return { total: paths.length, groups };
}
"""

SHOW_JS = """
([shown, focusCircle]) => {
  const svg = document.getElementById('hive');
  const paths = svg.querySelectorAll('path.link');
  const circles = svg.querySelectorAll('circle.node');
  // clear any focus
  svg.classList.remove('focus');
  for (const el of svg.querySelectorAll('.hl')) el.classList.remove('hl');
  const s = new Set(shown);
  paths.forEach((p, i) => p.classList.toggle('shown', s.has(i)));
  if (focusCircle != null) circles[focusCircle].dispatchEvent(new Event('mouseenter'));
}
"""

def snap(page, name, ms):
    fn = OUT / f'{len(frames):04d}_{name}.png'
    page.screenshot(path=str(fn), clip={'x': 0, 'y': 0, 'width': SIZE, 'height': SIZE})
    frames.append((fn.name, ms))

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={'width': SIZE, 'height': SIZE}, device_scale_factor=1)
    page.goto('http://127.0.0.1:8799/artworks-hive/index.html')
    page.wait_for_selector('#loading', state='detached', timeout=120000)
    page.wait_for_selector('path.link', timeout=60000)
    page.evaluate(SETUP_JS)
    page.wait_for_timeout(4000)  # let portrait images arrive
    info = page.evaluate(GROUP_JS)
    groups = info['groups']
    print('curves', info['total'], 'people with curves', len(groups), file=sys.stderr)

    # 1. no connections
    page.evaluate(SHOW_JS, [[], None])
    snap(page, 'empty', 1500)

    # 2. cycle through the most-connected people one at a time, accumulating
    shown = []
    N_SOLO = min(14, len(groups))
    for g in groups[:N_SOLO]:
        page.evaluate(SHOW_JS, [shown, g['circle']])
        snap(page, 'person', 550)
        shown = shown + g['ids']
    # 3. remaining people in quicker batches
    rest = groups[N_SOLO:]
    batch = max(1, len(rest) // 10)
    for i in range(0, len(rest), batch):
        for g in rest[i:i+batch]: shown = shown + g['ids']
        page.evaluate(SHOW_JS, [shown, None])
        snap(page, 'batch', 180)
    # 4. all connections
    page.evaluate(SHOW_JS, [list(range(info['total'])), None])
    snap(page, 'all', 3000)
    browser.close()

(OUT / 'frames.json').write_text(json.dumps(frames))
with open(OUT / 'list.txt', 'w') as f:  # ffmpeg concat list with per-frame durations
    for name, ms in frames:
        f.write(f"file '{name}'\nduration {ms/1000:.3f}\n")
    f.write(f"file '{frames[-1][0]}'\n")
print('frames', len(frames), file=sys.stderr)
