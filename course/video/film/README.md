# Lesson films

Each lesson ships as a cinematic film built in HTML and rendered frame by frame to MP4.

- `W01-L01.html`: the lesson 1 film. Open it in a browser to watch it play live.
- `render.js`: renders 25 fps JPEG frames with Playwright (`node render.js "$PWD"`), then encode with
  `ffmpeg -framerate 25 -i frames/f%05d.jpg -c:v libx264 -pix_fmt yuv420p -crf 18 out.mp4`.

Fonts are not committed. Put Bebas Neue and DM Sans (both SIL Open Font Licence, from Google Fonts) in `fonts/` as
`BebasNeue-Regular.ttf` and `DMSans.ttf`.
