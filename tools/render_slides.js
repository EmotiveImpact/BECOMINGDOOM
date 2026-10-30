// Snapshot each scene of a lesson film at its resting state, one PNG per slide.
//   node tools/render_slides.js course/video/film/W01-L02.html out/dir
const {chromium} = require('playwright');
const path = require('path');
(async () => {
  const [film, out] = process.argv.slice(2);
  const b = await chromium.launch();
  const p = await b.newPage({viewport: {width: 1920, height: 1080}});
  await p.goto('file://' + path.resolve(film) + '#capture');
  await p.evaluate(() => document.fonts.ready);
  await p.waitForTimeout(800);
  const scenes = await p.evaluate(() => [...document.querySelectorAll('.scene')].map(s => [+s.dataset.start, +s.dataset.dur]));
  require('fs').mkdirSync(out, {recursive: true});
  for (let i = 0; i < scenes.length; i++) {
    const [s, d] = scenes[i];
    await p.evaluate(t => window.seek(t), s + d - 0.6);
    await p.screenshot({path: `${out}/slide-${String(i + 1).padStart(2, '0')}.png`});
  }
  await b.close();
  console.log(scenes.length + ' slides');
})();
