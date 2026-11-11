#!/usr/bin/env python3
"""Render một trang template (canvas) thành MP4 / lớp trong suốt / ảnh tĩnh — chạy hoàn toàn trên Claude.

Hợp đồng của template:
  - <canvas id="c">, window.renderFrame(t) vẽ đúng khung tại giây t (không dùng timer, Date.now, random không seed)
  - window.__dur = độ dài (giây)
  - (tuỳ chọn) window.setData(obj) nhận dữ liệu JSON trước khi render, rồi cập nhật window.__dur

Ví dụ
  python3 render.py template.html out.mp4 --data data.json
  python3 render.py template.html overlay.mov --data data.json --alpha          # ProRes 4444 có alpha
  python3 render.py template.html overlay.webm --data data.json --alpha         # VP9 có alpha (nhẹ)
  python3 render.py template.html film.mp4 --data data.json --video talk.mp4    # vẽ đè lên video, giữ tiếng gốc
  python3 render.py template.html still.png --data data.json --still 2.5
  python3 render.py template.html sheet.jpg --data data.json --sheet 1          # contact sheet, 1 khung/giây

Cần: playwright (Chromium có sẵn trên Claude — không chạy `playwright install`), ffmpeg.
"""
import argparse, base64, json, pathlib, subprocess, sys, urllib.parse, tempfile, os

ap = argparse.ArgumentParser()
ap.add_argument('template'); ap.add_argument('out')
ap.add_argument('--w', type=int, default=1080); ap.add_argument('--h', type=int, default=1920)
ap.add_argument('--fps', type=float, default=30); ap.add_argument('--dur', type=float)
ap.add_argument('--data', help='file JSON truyền vào window.setData')
ap.add_argument('--text'); ap.add_argument('--sub')
ap.add_argument('--set', action='append', default=[], help='đổi màu/tham số, vd c1=3FD6A6 (không cần #)')
ap.add_argument('--alpha', action='store_true', help='nền trong suốt (.mov ProRes 4444 hoặc .webm VP9)')
ap.add_argument('--video', help='video nền: vẽ template đè lên, giữ âm thanh gốc; khớp w/h/fps/dur theo video')
ap.add_argument('--still', type=float, help='xuất một khung tại giây này ra .png')
ap.add_argument('--sheet', type=float, help='contact sheet: mỗi N giây một khung, ra .jpg')
ap.add_argument('--audio', help='âm thanh ghép vào (cắt theo độ dài)')
ap.add_argument('--crf', type=int, default=17)
ap.add_argument('--cues', help='ghi window.__cues (mốc SFX/sự kiện template tự tính) ra file JSON')
a = ap.parse_args()

from playwright.sync_api import sync_playwright

def probe(f):
    j = json.loads(subprocess.run(['ffprobe', '-v', 'error', '-show_entries',
        'stream=codec_type,width,height,avg_frame_rate:stream_side_data=rotation:format=duration', '-of', 'json', f],
        check=True, capture_output=True, text=True).stdout)
    v = next(s for s in j['streams'] if s['codec_type'] == 'video')
    w, h = v['width'], v['height']
    for d in v.get('side_data_list', []) or []:
        if 'rotation' in d and abs(int(d['rotation'])) in (90, 270): w, h = h, w
    n, d = v['avg_frame_rate'].split('/')
    return w, h, int(n) / (int(d) or 1), float(j['format']['duration']), any(s['codec_type'] == 'audio' for s in j['streams'])

has_audio = False
if a.video:
    a.w, a.h, a.fps, vdur, has_audio = probe(a.video)
    a.dur = a.dur or vdur
    a.alpha = True   # template vẽ trong suốt, video nằm dưới

q = {'render': '1', 'w': a.w, 'h': a.h}
if a.dur: q['dur'] = a.dur
if a.text is not None: q['text'] = a.text
if a.sub is not None: q['sub'] = a.sub
if a.alpha: q['alpha'] = '1'
for kv in a.set:
    k, v = kv.split('=', 1); q[k] = v.lstrip('#')
url = pathlib.Path(a.template).resolve().as_uri() + '?' + urllib.parse.urlencode(q)

with sync_playwright() as p:
    br = p.chromium.launch(args=['--disable-gpu-vsync', '--allow-file-access-from-files'])
    pg = br.new_page(viewport={'width': min(a.w, 1920), 'height': min(a.h, 1920)})
    errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto(url); pg.wait_for_function('typeof window.renderFrame === "function"', timeout=30000)
    if a.data:
        data = json.loads(pathlib.Path(a.data).read_text(encoding='utf-8'))
        pg.evaluate('(d)=>window.setData ? window.setData(d) : null', data)
    pg.evaluate('document.fonts ? document.fonts.ready.then(()=>1) : 1')
    pg.evaluate('window.__ready ? window.__ready : 1')
    if errs: sys.exit('lỗi template: ' + errs[0])
    dur = a.dur if (a.video and a.dur) else pg.evaluate('window.__dur')
    if a.cues:
        pathlib.Path(a.cues).write_text(json.dumps(pg.evaluate('window.__cues || []'), ensure_ascii=False, indent=1), encoding='utf-8')
        print('wrote', a.cues)
    grab = "([t,f])=>{renderFrame(t);return document.getElementById('c').toDataURL(f,0.95)}"
    def frame(t, fmt='image/png'):
        d = pg.evaluate(grab, [t, fmt]); return base64.b64decode(d.split(',', 1)[1])

    if a.still is not None:
        pathlib.Path(a.out).write_bytes(frame(a.still)); print('wrote', a.out); br.close(); sys.exit()

    if a.sheet:
        tmp = pathlib.Path(tempfile.mkdtemp())
        ts = [round(x * a.sheet, 3) for x in range(int(dur / a.sheet) + 1) if x * a.sheet < dur]
        for i, t in enumerate(ts):
            dst = tmp / f'{i:04d}.png'
            if a.video:
                lay = tmp / f'l{i:04d}.png'; lay.write_bytes(frame(t))
                subprocess.run(['ffmpeg', '-y', '-v', 'error', '-ss', str(t), '-i', a.video, '-i', str(lay),
                    '-filter_complex', '[0:v][1:v]overlay', '-frames:v', '1', str(dst)], check=True)
            else: dst.write_bytes(frame(t))
        cols = 6 if a.w < a.h else 4
        rows = (len(ts) + cols - 1) // cols
        cmd = ['ffmpeg', '-y', '-v', 'error', '-framerate', '1', '-i', str(tmp / '%04d.png')]
        sc = 'scale=270:-1' if a.w < a.h else 'scale=420:-1'
        subprocess.run(cmd + ['-vf', f"{sc},drawtext=text='%{{eif\\:n*{a.sheet}\\:d}}s':x=8:y=8:fontsize=22:fontcolor=white:box=1:boxcolor=black@0.6,tile={cols}x{rows}:padding=4", '-frames:v', '1', a.out], check=True)
        print('wrote', a.out, f'({len(ts)} khung)'); br.close(); sys.exit()

    n = int(round(dur * a.fps))
    ext = pathlib.Path(a.out).suffix.lower()
    fmt = 'image/png' if a.alpha else 'image/jpeg'
    cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-f', 'image2pipe', '-c:v', 'png' if fmt == 'image/png' else 'mjpeg',
           '-framerate', str(a.fps), '-i', '-']
    if a.video:
        cmd += ['-i', a.video, '-filter_complex', '[1:v][0:v]overlay=format=auto,format=yuv420p[v]', '-map', '[v]']
        if has_audio: cmd += ['-map', '1:a', '-c:a', 'aac', '-b:a', '192k']
        cmd += ['-c:v', 'libx264', '-preset', 'medium', '-crf', str(a.crf), '-movflags', '+faststart', '-t', str(dur)]
    else:
        if a.audio: cmd += ['-i', a.audio, '-map', '0:v', '-map', '1:a', '-shortest', '-c:a', 'aac', '-b:a', '192k']
        if a.alpha and ext == '.webm': cmd += ['-c:v', 'libvpx-vp9', '-pix_fmt', 'yuva420p', '-b:v', '0', '-crf', '24']
        elif a.alpha: cmd += ['-c:v', 'prores_ks', '-profile:v', '4444', '-pix_fmt', 'yuva444p10le']
        else: cmd += ['-c:v', 'libx264', '-preset', 'medium', '-crf', str(a.crf), '-pix_fmt', 'yuv420p', '-movflags', '+faststart']
    ff = subprocess.Popen(cmd + [a.out], stdin=subprocess.PIPE)
    for i in range(n):
        ff.stdin.write(frame(i / a.fps, fmt))
        if i % int(a.fps) == 0: print(f'\rkhung {i}/{n}', end='', flush=True)
    ff.stdin.close(); ff.wait(); br.close()
    if ff.returncode: sys.exit('ffmpeg lỗi')
    print(f'\rwrote {a.out}  ({n} khung, {dur:.2f}s @ {a.fps}fps, {a.w}x{a.h})')
