#!/usr/bin/env python3
"""Chép lời tiếng Việt có mốc từng từ bằng sherpa-onnx (zipformer-vi), chạy hoàn toàn trên Claude.

Cách dùng:
  python3 transcribe_vi.py talk.mp4 [transcript.json] [--model-dir DIR] [--max-seg 18]

Ghi transcript.json:
  { video: {file,width,height,fps,duration}, engine, words:[{text,start,end}], lines:[{start,end,text}] }
và in từng câu kèm mốc thời gian.

Lần đầu tự tải model từ GitHub releases của k2-fsa/sherpa-onnx (huggingface thường bị chặn):
  asr-models/sherpa-onnx-zipformer-vi-2025-04-20.tar.bz2  (~260 MB) vào ~/.cache/sherpa/
Cần: pip install sherpa-onnx numpy ; ffmpeg/ffprobe.

Ghi chú: zipformer cho mốc từ tốt nhưng có thể nghe sai chính tả (tên riêng, tiếng Anh, con số).
Đối chiếu với kịch bản nếu có; chữ đưa lên màn hình phải đúng lời nói.
"""
import argparse, json, os, re, subprocess, sys, tarfile, urllib.request, pathlib
import numpy as np

URL = 'https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-zipformer-vi-2025-04-20.tar.bz2'
NAME = 'sherpa-onnx-zipformer-vi-2025-04-20'
SR = 16000

ap = argparse.ArgumentParser()
ap.add_argument('input'); ap.add_argument('out', nargs='?', default='transcript.json')
ap.add_argument('--model-dir', default=os.path.expanduser('~/.cache/sherpa'))
ap.add_argument('--max-seg', type=float, default=18.0, help='độ dài tối đa mỗi đoạn nhận dạng (giây)')
ap.add_argument('--threads', type=int, default=4)
a = ap.parse_args()

def sh(*cmd):
    return subprocess.run(cmd, check=True, capture_output=True, text=True).stdout

# ── model ───────────────────────────────────────────────────────────────────
md = pathlib.Path(a.model_dir) / NAME
if not (md / 'tokens.txt').exists():
    pathlib.Path(a.model_dir).mkdir(parents=True, exist_ok=True)
    tb = pathlib.Path(a.model_dir) / (NAME + '.tar.bz2')
    print('Đang tải model zipformer-vi (~260 MB)…', file=sys.stderr)
    urllib.request.urlretrieve(URL, tb)
    with tarfile.open(tb) as t: t.extractall(a.model_dir)
    tb.unlink()
def pick(pat):
    c = sorted(md.glob(pat)); return str(c[0])
import sherpa_onnx
rec = sherpa_onnx.OfflineRecognizer.from_transducer(
    encoder=pick('encoder*.onnx'), decoder=pick('decoder*.onnx'), joiner=pick('joiner*.onnx'),
    tokens=str(md / 'tokens.txt'), num_threads=a.threads, decoding_method='greedy_search')

# ── video info ──────────────────────────────────────────────────────────────
pr = json.loads(sh('ffprobe', '-v', 'error', '-show_entries',
    'stream=codec_type,width,height,avg_frame_rate:stream_side_data=rotation:format=duration', '-of', 'json', a.input))
vs = next((s for s in pr['streams'] if s['codec_type'] == 'video'), None)
if not any(s['codec_type'] == 'audio' for s in pr['streams']): sys.exit('File không có audio.')
w = h = fps = None
if vs:
    w, h = vs.get('width'), vs.get('height')
    rot = 0
    for d in vs.get('side_data_list', []) or []:
        if 'rotation' in d: rot = abs(int(d['rotation']))
    if rot in (90, 270): w, h = h, w
    n, d = (vs.get('avg_frame_rate') or '30/1').split('/'); fps = round(int(n) / (int(d) or 1), 2)
dur = float(pr['format']['duration'])

# ── audio → float32 mono 16k ─────────────────────────────────────────────────
raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', a.input, '-ac', '1', '-ar', str(SR), '-f', 'f32le', '-'],
                     check=True, capture_output=True).stdout
audio = np.frombuffer(raw, dtype=np.float32)

# ── cắt theo khoảng lặng ────────────────────────────────────────────────────
win = int(0.03 * SR)
e = np.sqrt(np.convolve(audio ** 2, np.ones(win) / win, mode='same') + 1e-12)
thr = max(np.percentile(e, 20) * 2.5, 0.004)
quiet = e < thr
def cut_points():
    pts, i, n = [], 0, len(audio)
    while i < n:
        end = min(i + int(a.max_seg * SR), n)
        if end >= n: pts.append((i, n)); break
        lo = i + int(a.max_seg * 0.4 * SR)
        seg = quiet[lo:end]
        # tìm vùng lặng dài nhất gần cuối
        best, run, bstart = 0, 0, None
        for k, q in enumerate(seg):
            run = run + 1 if q else 0
            if run > best: best, bstart = run, k - run + 1
        c = lo + bstart + best // 2 if best > int(0.08 * SR) else end
        pts.append((i, c)); i = c
    return pts

words = []
for s0, s1 in cut_points():
    st = rec.create_stream(); st.accept_waveform(SR, audio[s0:s1]); rec.decode_stream(st)
    r = st.result
    toks, ts = list(r.tokens), list(r.timestamps)
    off = s0 / SR
    cur = None
    for k, (tk, t0) in enumerate(zip(toks, ts)):
        t0 = off + float(t0)
        new = tk[:1] in ('▁', ' ') or cur is None
        piece = tk.replace('▁', '').strip()
        if new:
            if cur and cur['text']: words.append(cur)
            cur = {'text': piece, 'start': round(t0, 3), 'end': round(t0 + 0.2, 3)}
        else:
            cur['text'] += piece
        cur['end'] = round(t0 + 0.12, 3)
    if cur and cur['text']: words.append(cur)

# kéo dài 'end' tới gần từ kế tiếp (tối đa 0.5 s) cho phụ đề dễ đọc
for k in range(len(words) - 1):
    gap = words[k + 1]['start'] - words[k]['end']
    if 0 < gap: words[k]['end'] = round(min(words[k + 1]['start'] - 0.02, words[k]['end'] + 0.5, words[k + 1]['start']), 3)
for wd in words: wd['text'] = wd['text'].lower()

# ── câu: tách ở chỗ nghỉ ≥ 0.45 s ─────────────────────────────────────────
lines, cur = [], []
for k, wd in enumerate(words):
    cur.append(wd)
    nxt = words[k + 1] if k + 1 < len(words) else None
    if nxt is None or nxt['start'] - wd['end'] >= 0.45 or len(cur) >= 28:
        lines.append({'start': cur[0]['start'], 'end': cur[-1]['end'], 'text': ' '.join(x['text'] for x in cur)}); cur = []

out = {'video': {'file': os.path.basename(a.input), 'width': w, 'height': h, 'fps': fps, 'duration': round(dur, 3)},
       'engine': 'sherpa-onnx zipformer-vi', 'words': words, 'lines': lines}
pathlib.Path(a.out).write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding='utf-8')
print(f'video {w}x{h} @ {fps} fps, {dur:.2f}s — {len(words)} từ, {len(lines)} câu → {a.out}')
for L in lines: print(f"{L['start']:7.2f}–{L['end']:7.2f}  {L['text']}")
