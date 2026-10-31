#!/usr/bin/env python3
"""Type and layout test: the same four slides in three type systems."""
import pathlib

SYSTEMS = {
    "1": ("Inter Tight", "font-family:IT;font-weight:500;letter-spacing:-.035em;text-transform:none;line-height:1.0"),
    "2": ("Oswald Regular", "font-family:Osw;font-weight:400;letter-spacing:.005em;text-transform:uppercase;line-height:1.04"),
    "3": ("Oswald Light", "font-family:Osw;font-weight:300;letter-spacing:.02em;text-transform:uppercase;line-height:1.06"),
}

CSS = """
@font-face { font-family: IT; src: url(../fonts/InterTight.ttf); font-weight: 100 900; }
@font-face { font-family: Osw; src: url(../fonts/Oswald-300.ttf); font-weight: 300; }
@font-face { font-family: Osw; src: url(../fonts/Oswald-400.ttf); font-weight: 400; }
@font-face { font-family: Osw; src: url(../fonts/Oswald-500.ttf); font-weight: 500; }
@page { size:1920px 1080px; margin:0; }
* { margin:0; padding:0; box-sizing:border-box; }
body { background:#050505; color:#EDEDED; font-family:IT, sans-serif; }
.s { width:1920px; height:1080px; position:relative; overflow:hidden; background:#070707; page-break-after:always; }
.bg { position:absolute; inset:0; background-size:cover; background-position:center; }
.fade { position:absolute; inset:0; background:linear-gradient(90deg, rgba(5,5,5,.92) 0%, rgba(5,5,5,.7) 34%, rgba(5,5,5,0) 62%); }
.meta { position:absolute; left:120px; right:120px; font-size:15px; font-weight:500; letter-spacing:.02em; color:#8c8c90; display:flex; justify-content:space-between; }
.meta.t { top:56px; } .meta.b { bottom:56px; border-top:1px solid rgba(237,237,237,.12); padding-top:18px; }
.meta b { color:#EDEDED; font-weight:600; }
.block { position:absolute; left:120px; top:50%; transform:translateY(-50%); }
.kick { font-size:17px; font-weight:500; letter-spacing:.02em; color:#9a9a9e; margin-bottom:34px; display:flex; align-items:center; gap:14px; }
.sq { width:10px; height:10px; background:#D90D0D; display:inline-block; }
.body { font-size:26px; line-height:1.45; color:#9a9a9e; max-width:620px; margin-top:34px; font-weight:400; }
.dot { color:#D90D0D; }
.q { position:absolute; left:0; right:0; top:50%; transform:translateY(-50%); text-align:center; }
.q .h { display:inline-block; }
.dim { color:#5a5a5e; }
.nums { position:absolute; left:120px; right:120px; top:50%; transform:translateY(-50%); }
.grid3 { display:grid; grid-template-columns:repeat(3,1fr); gap:60px; margin-top:80px; }
.cell { border-top:1px solid rgba(237,237,237,.16); padding-top:28px; }
.cell.hot { border-top:1px solid #D90D0D; }
.n { font-size:150px; line-height:1; }
.lab { font-size:16px; font-weight:600; letter-spacing:.12em; text-transform:uppercase; margin-top:22px; color:#EDEDED; }
.cap { font-size:22px; color:#8c8c90; line-height:1.4; margin-top:10px; max-width:420px; }
.tag { position:absolute; right:120px; top:120px; font-size:15px; color:#5a5a5e; }
"""


def slides(sys_key):
    name, H = SYSTEMS[sys_key]
    meta_t = f'<div class="meta t"><span><b>Becoming Doom</b></span><span>Week 1 / Claim the Throne</span></div>'
    def meta_b(n):
        return f'<div class="meta b"><span>Lesson 01 / Selfishness as a virtue</span><span>{n} / 22</span></div>'
    tag = f'<div class="tag">Type {sys_key} / {name}</div>'
    out = []
    # 1. title over image
    out.append(f'''<section class="s"><div class="bg" style="background-image:url(img-title.png)"></div><div class="fade"></div>{meta_t}
<div class="block"><div class="kick"><i class="sq"></i>Lesson 01</div>
<div style="{H};font-size:118px">Selfishness<br>as a virtue<span class="dot">.</span></div>
<div class="body">Your life is a legitimate object of your own ambition. This lesson is about acting like it.</div></div>{meta_b("01")}{tag}</section>''')
    # 2. scene with words
    out.append(f'''<section class="s"><div class="bg" style="background-image:url(img-nurse.png)"></div><div class="fade"></div>{meta_t}
<div class="block"><div class="kick"><i class="sq"></i>Amara / Ward nurse / End of a night shift</div>
<div style="{H};font-size:104px">Tuesday. Thursday.<br>Fixed<span class="dot">.</span></div>
<div class="body">Two evenings a week, written into the rota before anyone else could claim them.</div></div>{meta_b("12")}{tag}</section>''')
    # 3. question
    out.append(f'''<section class="s">{meta_t}<div class="q"><div class="kick" style="justify-content:center">Think of the thing you keep saying matters</div>
<div class="h" style="{H};font-size:96px">What has it <span class="dim">actually</span> been<br><span class="dim">allowed</span> to cost<span class="dot">?</span></div></div>{meta_b("03")}{tag}</section>''')
    # 4. numbers
    out.append(f'''<section class="s">{meta_t}<div class="nums"><div class="kick"><i class="sq"></i>Where your hours go</div>
<div style="{H};font-size:84px">Three voices compete<br>for every hour you have<span class="dot">.</span></div>
<div class="grid3">
<div class="cell"><div class="n" style="{H}">42%</div><div class="lab">Appetite</div><div class="cap">What I want right now. Loud, fast, never your interest.</div></div>
<div class="cell"><div class="n" style="{H}">46%</div><div class="lab">Approval</div><div class="cap">What I fear they will think. Quiet and respectable.</div></div>
<div class="cell hot"><div class="n" style="{H};color:#D90D0D">12%</div><div class="lab">Interest</div><div class="cap">What I will be glad I built in five years.</div></div>
</div></div>{meta_b("09")}{tag}</section>''')
    return out


html = ['<!doctype html><html lang="en-GB"><head><meta charset="utf-8"><title>Type test</title><style>', CSS, '</style></head><body>']
for k in SYSTEMS:
    html += slides(k)
html.append('</body></html>')
pathlib.Path(__file__).with_name("type-test.html").write_text("\n".join(html))
print("ok")
