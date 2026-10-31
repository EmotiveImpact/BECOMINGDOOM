# Lesson films

Each lesson ships as a cinematic film built in HTML and rendered frame by frame to MP4.

- `W01-L01.html`: the lesson 1 film. Open it in a browser to watch it play live.
- `render.js`: renders 25 fps JPEG frames with Playwright (`node render.js "$PWD"`), then encode with
  `ffmpeg -framerate 25 -i frames/f%05d.jpg -c:v libx264 -pix_fmt yuv420p -crf 18 out.mp4`.

Fonts are not committed. Put these in `fonts/` (all SIL Open Font Licence, from Google Fonts):
`Anton-Regular.ttf` (headlines), `InterTight.ttf` (variable, for kickers and body) and `ArchivoBlack-Regular.ttf` (label blocks).

## Look

Near-black frames with a neon red light bar, slice glitch and grain. Headlines are condensed caps finished with a red full stop.
Poster devices appear where they earn it: stacked label blocks, a full red panel for the core idea, distressed red type,
short statement cards and numbered caption footers. The cast rotates across lessons; lesson 1 leads with a Black man.
