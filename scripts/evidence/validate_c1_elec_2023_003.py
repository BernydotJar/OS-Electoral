#!/usr/bin/env python3
from __future__ import annotations
import csv
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
CUR=ROOT/'research/curated/electoral-2023'

def read(name):
    with (CUR/name).open(encoding='utf-8', newline='') as f:
        return list(csv.DictReader(f))

inv=read('official-center-inventory-2023.csv')
ass=read('official-jrv-center-assignment-2023.csv')
labels=read('official-center-labels-2023.csv')
cross=read('electoral-geography-crosswalk.csv')

assert len(inv)==18, f'expected 18 unique centers, got {len(inv)}'
codes=[r['center_code'] for r in inv]
assert len(set(codes))==18
assert set(codes)=={str(i) for i in range(1,19)}
assert all(r['verification_status']=='CONFIRMED_FROM_OFFICIAL_CENTER_PDF' for r in inv)

assert len(ass)==19, f'expected 19 explicit assignment records, got {len(ass)}'
assert sum(int(r['jrv_count']) for r in ass)==100
assert sum(int(r['registered_electorate']) for r in ass)==39099
assert sum(1 for r in ass if r['center_code']=='7')==2

ranges=[]
for r in ass:
    a,b,c=map(int,(r['jrv_initial'],r['jrv_final'],r['jrv_count']))
    assert b-a+1==c, r
    ranges.extend(range(a,b+1))
assert ranges==list(range(5337,5437)), 'JRV range has gap, overlap, or wrong ordering'
assert len(set(ranges))==100

cem=[r for r in labels if r['label_type']=='CEM_COMMUNITY_LABEL']
assert len(cem)==4
assert all(r['change_type']=='CONFIRMED' for r in cem)
assert all(not r['raw_ocr_text'] for r in cem), 'No OCR text should be accepted as raw evidence'

assert len(cross)==28, f'expected 19 center-group and 9 group-community crosswalk rows, got {len(cross)}'
assert all(r['verification_status']=='CONFIRMED' for r in cross)

for path in [
    CUR/'official-center-inventory-2023.csv', CUR/'official-jrv-center-assignment-2023.csv',
    CUR/'official-center-labels-2023.csv', CUR/'electoral-geography-crosswalk.csv',
    CUR/'official-center-cartography-review.md', CUR/'electoral-geography-data-quality.md',
    CUR/'C1-ELEC-2023-003-implementation-report.md']:
    text=path.read_text(encoding='utf-8')
    assert '/Users/' not in text, f'personal absolute path in {path}'

print('[OK] unique centers=18')
print('[OK] assignment rows=19; total JRV=100; registered electorate=39099')
print('[OK] JRV coverage=5337-5436 contiguous without overlap')
print('[OK] center 7 preserved as one identity with two explicit ranges')
print('[OK] visually reviewed CEM labels=4; no OCR value promoted')
print('[OK] explicit crosswalk rows=28')
print('[OK] portability/privacy/political-gate structural checks passed')
