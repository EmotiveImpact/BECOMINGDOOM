"""Check the curriculum inventory and cross-file references, not learning efficacy."""
from pathlib import Path
import json, re
root = Path(__file__).resolve().parents[1]
c = json.loads((root / 'curriculum/course.json').read_text())
assert len(c['weeks']) == 6
rows = [d for w in c['weeks'] for d in w['days']]
assert [d['day'] for d in rows] == list(range(1, 43))
assert len({d['workbook_id'] for d in rows}) == 42
assert len(c['models']) == 10
for week in c['weeks']:
    n = week['week']
    assert len(week['days']) == 7
    assert sum(d['minutes'] for d in week['days']) == 370
    assert len(week['new_models']) == (0 if n == 1 else 2)
    text = (root / f'curriculum/weeks/{n:02}.md').read_text()
    for d in week['days']:
        assert d['workbook_id'] in text
        assert all(x['introduced_week'] <= n for x in c['models'] if x['id'] in d['available_models'])
    for source in week['sources']:
        assert (root / f'research/sources/{source}.md').exists()
principles = (root / 'curriculum/PRINCIPLES.md').read_text()
assert len(re.findall(r'^## P\d{2}:', principles, re.M)) == 14
assert {p for w in c['weeks'] for p in w['new_principles']} == {f'P{i:02}' for i in range(1, 15)}
for file in root.rglob('*.md'):
    for link in re.findall(r'\[[^\]]*\]\(([^)]+)\)', file.read_text()):
        if '://' not in link and not link.startswith('#'):
            assert (file.parent / link.split('#')[0]).exists(), (file, link)
print('PASS: 6 weeks; 42 unique days/pages; 14 principles; 10 staged models; weekly workload; source and Markdown links.')
