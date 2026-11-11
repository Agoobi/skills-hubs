import struct,json,csv,zipfile,xml.etree.ElementTree as ET,re,argparse
from pathlib import Path
parser=argparse.ArgumentParser(description='Index local WAV headers and vendor descriptions without copying audio.')
parser.add_argument('--root',type=Path,default=Path(r'E:\TaiNguyen\SFX Meme\Boom_Library_Casual_UI_Construction_Kit_WAV'))
parser.add_argument('--output',type=Path,required=True)
args=parser.parse_args()
root=args.root
out=args.output;out.mkdir(parents=True,exist_ok=True)
ns={'m':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
descs={}
with zipfile.ZipFile(root/'00_Casual_UI_CK_Metadata.xlsx') as z:
 shared=[]
 if 'xl/sharedStrings.xml' in z.namelist():
  shared=[''.join(e.itertext()) for e in ET.fromstring(z.read('xl/sharedStrings.xml')).findall('m:si',ns)]
 for file in z.namelist():
  if not re.match(r'xl/worksheets/sheet\d+.xml$',file):continue
  for row in ET.fromstring(z.read(file)).findall('.//m:row',ns):
   vals=[]
   for c in row.findall('m:c',ns):
    v=c.find('m:v',ns)
    if v is not None: s=shared[int(v.text)] if c.get('t')=='s' else (v.text or '')
    else:s=''.join(c.find('m:is',ns).itertext()) if c.find('m:is',ns) is not None else ''
    vals.append(s)
   for i,s in enumerate(vals):
    if s.lower().endswith('.wav') and i+1<len(vals):descs[s]=vals[i+1]
def info(p):
 fmt=None;size=None
 with p.open('rb') as f:
  head=f.read(12)
  if head[:4]!=b'RIFF':raise ValueError(str(p))
  while h:=f.read(8):
   tag,n=struct.unpack('<4sI',h)
   if tag==b'fmt ':fmt=struct.unpack('<HHIIHH',f.read(16));f.seek(n-16,1)
   elif tag==b'data':size=n;f.seek(n,1)
   else:f.seek(n,1)
   if n%2:f.seek(1,1)
   if fmt and size is not None:break
 code,ch,sr,br,block,bits=fmt
 name=p.name;u=name.upper();cats=[]
 for cat,keys in [('UI Click',['CLICK','TICK','SNAP']),('Pop',['POOF','POP','PLOP']),('Whoosh',['WHOOSH']),('Impact',['IMPACT','HIT','PUNCH','SLAP']),('Notification',['REWARD','BELL','PING','SHIMMER']),('Button',['BUTTON','SWITCH','CLICK']),('Swipe',['SWIPE','SLIDE','SCRAPE','WIPE']),('Transition',['WHOOSH','RISING','SWIRL']),('Meme Reaction',['BOING','WHISTLE']),('Accent',['SHIMMER','ZAP','SNAP','RATTLE'])]:
  if any(k in u for k in keys):cats.append(cat)
 if not cats:cats=['Accent']
 return dict(filename=name,path=str(p),duration_s=round(size/br,6),sample_rate=sr,channels=ch,bits=bits,categories='; '.join(cats),description=descs.get(name,name.split('_',1)[-1].removesuffix('_B00M_CUCK.wav')),classification_basis='filename heuristic; vendor description; audition pending',license_status='local EULA present; entitlement unverified')
rows=[info(p) for p in sorted(root.rglob('*.wav'))]
with (out/'SFX_INDEX.csv').open('w',newline='',encoding='utf-8-sig') as f:
 w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)
(out/'summary.json').write_text(json.dumps({'count':len(rows),'vendor_descriptions':sum(r['filename'] in descs for r in rows),'duration_min':min(r['duration_s'] for r in rows),'duration_max':max(r['duration_s'] for r in rows),'category_counts':{cat:sum(cat in r['categories'].split('; ') for r in rows) for cat in sorted({c for r in rows for c in r['categories'].split('; ')})}},indent=2),encoding='utf8')
print((out/'summary.json').read_text())
