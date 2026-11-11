# Âm thanh trên Claude: voice, nhạc, SFX và kiểm sync

Toàn bộ trộn âm làm bằng HyperFrames (audio có `data-start`) hoặc ffmpeg. Không dùng Premiere.

## Kiểm kê trước khi render
Liệt kê voice / nhạc / SFX / ambience, audio nhúng trong footage: nguồn, offset in/out, gain, fade. Phân biệt voice tách riêng với voice đã trộn sẵn. Thư viện SFX/nhạc nằm trên máy người dùng thì lấy qua công cụ liên kết máy tính (chỉ các file sẽ dùng); không có thì hỏi người dùng gửi kèm hoặc chỉ giao bản voice.

## Chế độ
- **Có sound design:** nhạc nền thấp hơn voice ~18–22 dB khi có lời, SFX ngắn tại động tác dẫn mắt (giấy vào, highlight, pin bản đồ), không lặp một file nhiều lần, không cắt đuôi SFX. Ducking nhạc dưới voice (`sidechaincompress` hoặc volume envelope).
- **Voice-only:** chỉ dùng file voice gốc riêng; tắt SFX, nhạc, ambience và audio nhúng trong b-roll. Không đổi giọng, tốc độ, cao độ, timing. Không lọc SFX ra khỏi bản trộn nếu đã có voice sạch.
- Không mặc định phim nào cũng có nhạc/SFX; yêu cầu hiện tại của người dùng quyết định.

## Trộn bằng ffmpeg (khi không để HyperFrames tự mix)
```sh
ffmpeg -i voice.wav -i music.wav -i sfx1.wav -filter_complex \
 "[1]volume=0.12[m];[2]adelay=4300|4300[s1];[0][m][s1]amix=inputs=3:normalize=0,alimiter=limit=0.89[a]" \
 -map "[a]" -ar 48000 mix.wav
ffmpeg -i renders/film.mp4 -i mix.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest final.mp4
```

## Kiểm tra
- Probe file thật: số khung, fps, thời lượng, kênh/sample rate audio. Decode audio, nghe/đo đầu–giữa–cuối và đoạn không lời.
- Loudness tham khảo cho mạng xã hội: khoảng −16 đến −14 LUFS integrated, true peak ≤ −1 dBTP (`ffmpeg -af ebur128=peak=true -f null -`). Là mục tiêu tham khảo, không bắt buộc.
- AAC có thể lệch vài trăm sample ở đầu: đo tương quan với voice gốc tại nhiều vị trí để phân biệt lệch cố định với trôi; chỉ bù đúng lượng đo được.
- Không tuyên bố "đã nghe" khi chỉ có phép đo; nêu rõ đã kiểm bằng cách nào.
