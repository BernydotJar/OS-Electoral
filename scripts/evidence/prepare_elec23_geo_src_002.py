#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json, os, subprocess
from pathlib import Path
from PIL import Image

ROOT=Path(__file__).resolve().parents[2]
POLITICS=Path(os.environ.get('POLITICS_ROOT', ROOT/'external/politics'))
OUT=ROOT/'.workspace/elec23-geo-src-002'
CANDIDATES=[
    POLITICS/'ELEC23-GEO-SRC-002.jpg',
    POLITICS/'02-01 ANTIGUA GUATEMALA-min.jpg',
    POLITICS/'0201 ANTIGUA GUATEMALA.jpg',
]
source=next((p for p in CANDIDATES if p.exists()), None)
if source is None:
    print('[BLOCKED] ELEC23-GEO-SRC-002 image not found under POLITICS_ROOT')
    print('Expected one of:')
    for p in CANDIDATES: print(f'  - {p}')
    raise SystemExit(3)
OUT.mkdir(parents=True, exist_ok=True)
data=source.read_bytes(); digest=hashlib.sha256(data).hexdigest()
img=Image.open(source); width,height=img.size
review=img.resize((width*2,height*2))
review_path=OUT/'review-2x.png'; review.save(review_path)
ocr={}
for psm in (6,11):
    base=OUT/f'ocr-spa-eng-psm{psm}'
    cmd=['tesseract',str(review_path),str(base),'-l','spa+eng','--psm',str(psm)]
    proc=subprocess.run(cmd,capture_output=True,text=True)
    ocr[str(psm)]={'returncode':proc.returncode,'stderr':proc.stderr.strip(),'text_file':str(base.with_suffix('.txt'))}
manifest={'source_path':str(source.relative_to(POLITICS)),'sha256':digest,'width':width,'height':height,'review_derivative':str(review_path.relative_to(ROOT)),'ocr':ocr,'policy':'OCR is assistive only; no text may be promoted without visual review.'}
(OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
print(f'[OK] prepared {source.name}: {width}x{height} sha256={digest}')
print(f'[OK] manifest: {OUT/"manifest.json"}')
