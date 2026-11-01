#!/usr/bin/env python3
"""Build a Becoming Doom lesson from its spec.

    python3 tools/build_lesson.py course/video/lessons/W01-L02.json

Writes the film (course/video/film/<id>.html) and the teleprompter script
(course/video/<id>.md). tools/render_slides.js turns the film into a slide deck.

Spec format: see course/video/lessons/README.md.
"""
import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_ASSETS = ROOT / "course" / "video" / "assets"
DUR = dict(poster=8, dossier=12, cover=6, split=9, gallery=7, themes=10, research=10, idea=9, band=7,
           character=8, bignum=7, timeline=11, summary=11, closer=9,
           open=5, labels=4, title=9, hook=9, image=8, red=8, list=10, scene=8, compare=10, story=11, recap=9,
           grunge=7, card=5, steps=10, mission=8, close=11, question=8, stats=10, radial=10)

WEEKS = {1: "Claim the Throne", 2: "Build the Fortress", 3: "Enter the Laboratory",
         4: "Command the Room", 5: "Build the Empire", 6: "Become Dangerous"}


def esc(s):
    return html.escape(s, quote=False).replace("'", "’")


def mark(s):
    """*word* turns red, _word_ turns grey; a trailing full stop turns red."""
    s = esc(s)
    s = re.sub(r"\*(.+?)\*", r'<span class="redt">\1</span>', s)
    s = re.sub(r"_(.+?)_", r'<span class="grey">\1</span>', s)
    return s


def dot(s):
    """Anton headline line: red final full stop."""
    m = mark(s)
    if m.endswith("."):
        m = m[:-1] + '<span class="dot">.</span>'
    elif m.endswith(".</span>"):
        pass
    return m


def a(cls, t, anim, inner, style=""):
    st = f' style="{style}"' if style else ""
    return f'<div class="{cls} a" data-in="{t}" data-anim="{anim}"{st}>{inner}</div>'


def rise_lines(lines, t0=1.0, step=0.3, last_style=""):
    out = []
    for i, ln in enumerate(lines):
        st = f' style="{last_style}"' if (last_style and i == len(lines) - 1) else ""
        out.append(f'<span class="mask"><span class="a" data-in="{t0 + i * step:.1f}" data-anim="rise"{st}>{dot(ln)}</span></span>')
    return "".join(out)


def bg(img, shift=0):
    style = f' style="left:{shift}px;right:{-shift}px"' if shift else ""
    return (f'<div class="kb"{style} data-kb="in"><div class="bg" style="background-image:url({img})"></div>'
            '<div class="shade left"></div></div>')


def hud(on):
    """Board-style HUD frame: corner brackets, a crosshair tick and small tracked readouts."""
    if not on:
        return ""
    lab = on if isinstance(on, str) else "SYS / ONLINE"
    return ('<div class="hudf a" data-in="0.2" data-anim="fade"><i class="c tl"></i><i class="c tr"></i><i class="c bl"></i><i class="c br"></i>'
            f'<span class="hl">{esc(lab)}</span><i class="xh"></i></div>')


def cap(n, title):
    return f'<div class="cap a" data-in="0.6" data-anim="fade"><span class="cn">{n:02d}</span>{esc(title)}</div>'


OPEN_ABS = re.compile(r'<div class="abs" style="([^"]*)">')
OUTER_PROPS = ("left", "right", "width")


def centre_blocks(html):
    """Centre each main text block vertically, so the space above it equals the space below."""
    for m in reversed(list(OPEN_ABS.finditer(html))):
        depth = 0
        for t in re.finditer(r"<div\b|</div>", html[m.start():]):
            depth += -1 if t.group(0) == "</div>" else 1
            if depth == 0:
                close = m.start() + t.start()
                break
        props = [x.strip() for x in m.group(1).split(";") if x.strip()]
        outer = ";".join(x for x in props if x.split(":")[0] in OUTER_PROPS)
        inner = ";".join(x for x in props if x.split(":")[0] not in OUTER_PROPS + ("top",))
        html = (html[:m.start()] + f'<div class="abs vc" style="{outer}"><div style="{inner}">'
                + html[m.end():close] + "</div>" + html[close:])
    return html



# ---- Classy look (Edem, 1 Nov): Oswald Medium caps headlines, smaller; Inter Tight for questions, labels and body ----
CLASSY = True
HEAD_SCALE = 0.7
PROPER = {w.lower(): w for w in (
    "Doom I I'm I'll I've Monday Tuesday Wednesday Thursday Friday Saturday Sunday "
    "Daniel Amara Kwame Kofi Marcus Tunde Leila Priya Sofia Malik Omar Jamal Chen Mateo Aisha "
    "Council Doomsday Week Lesson").split()}
CASE_KEYS = ("lines", "headline", "a", "b", "big", "words", "t")


def sentence_case(text, start=True):
    """Turn an ALL CAPS display line into sentence case, keeping names and the red-mark syntax."""
    if not re.search(r"[A-Z]", text) or re.search(r"[a-z]", text):
        return text, text.rstrip().endswith((".", "?", "!"))
    out, cap_next = [], start
    for tok in re.split(r"(\s+)", text.lower()):
        core = re.sub(r"[^a-z’']", "", tok)
        if core in PROPER and core:
            tok = tok.replace(core, PROPER[core], 1)
        elif cap_next and core:
            i = re.search(r"[a-z]", tok).start()
            tok = tok[:i] + tok[i].upper() + tok[i + 1:]
        if tok.strip():
            cap_next = tok.rstrip("*_”\"").endswith((".", "?", "!", ":"))
        out.append(tok)
    return "".join(out), cap_next


def classy_spec(obj):
    if isinstance(obj, list):
        return [classy_spec(x) for x in obj]
    if not isinstance(obj, dict):
        return obj
    o = {}
    for k, v in obj.items():
        if k in CASE_KEYS and isinstance(v, str):
            v = sentence_case(v)[0]
        elif k in CASE_KEYS and isinstance(v, list) and all(isinstance(x, str) for x in v):
            nxt, res = True, []
            for x in v:
                y, nxt = sentence_case(x, nxt)
                res.append(y)
            v = res
        else:
            v = classy_spec(v)
        o[k] = v
    return o


def classy_sizes(h):
    return re.sub(r'(class="anton[^"]*"[^>]*?font-size:)(\d+)px',
                  lambda m: f"{m.group(1)}{round(int(m.group(2)) * HEAD_SCALE)}px", h)


CLASSY_CSS = """
@font-face { font-family: Osw; src: url(fonts/Oswald-500.ttf); font-weight: 500; }
.anton { font-family:Osw; font-weight:500; letter-spacing:.005em; text-transform:uppercase; line-height:1.06 !important; }
.kick { font-weight:500; font-size:18px; letter-spacing:.02em !important; text-transform:none; color:#9a9a9e; }
.kick::before { content:""; display:inline-block; width:9px; height:9px; background:var(--red); margin-right:14px; vertical-align:2px; }
.onred .kick::before { background:#0a0a0a; }
.cap { font-weight:500; font-size:15px; letter-spacing:.02em; text-transform:none; color:#8c8c90; border-top-color:rgba(237,237,237,.12); }
#hud { font-weight:600; font-size:15px; letter-spacing:.02em; text-transform:none; color:#8c8c90; }
.row .t { font-family:Osw; font-weight:500; font-size:44px; letter-spacing:.005em; text-transform:uppercase; }
.row .n { font-weight:500; font-size:16px; letter-spacing:.04em; }
.row .d { font-size:22px; }
.strike { top:22px; height:3px; }
.row { border-top-color:rgba(237,237,237,.12); padding:22px 0; }
.trk { font-weight:400; letter-spacing:.3em; margin-right:-.3em; }
.bold { font-family:Osw; font-weight:500; font-size:120px; text-transform:uppercase; }
.give { font-size:34px; font-weight:500; letter-spacing:-.01em; }
.qbig { font-size:96px; letter-spacing:-.035em; }
.qlead { font-size:26px; color:#9a9a9e; }
.qsub { font-size:24px; }
.d2 { font-size:28px; }
.ct { font-weight:600; font-size:16px; letter-spacing:.12em; }
.small { font-size:22px; }
.col { border-top-color:rgba(237,237,237,.16); } .col.hot { border-top:1px solid var(--red); }
.lbl { font-family:Osw; font-weight:500; letter-spacing:.005em; font-size:100px; text-transform:uppercase; }
.fd { font-size:22px; border-bottom-color:rgba(237,237,237,.1); }
.fd > span { font-size:14px; letter-spacing:.14em; }
.ml { font-size:15px; letter-spacing:.14em; font-weight:500; }
.hudf { opacity:.55; }
"""


def fix(style, inner):
    """A positioned block that keeps its own placement (not vertically centred)."""
    return f'<div class="abs fix" style="{style}">{inner}</div>'


def pitch_html(sc, n, img, meta):
    """Film pitch deck layouts (Edem's reference, 1 Nov): quiet type, corner labels, split frames."""
    k = sc["kind"]
    corner = a("kick", 0.2, "fade", esc(sc.get("kicker", "")), "position:absolute;left:150px;top:44px") if sc.get("kicker") else ""
    if k == "cover":
        return (f'<div class="kb" data-kb="in" style="left:760px"><div class="bg" style="background-image:url({img(sc["img"])});background-size:cover"></div></div>'
                '<div class="abs fix" style="inset:0;background:linear-gradient(90deg,#050505 38%,rgba(5,5,5,0) 70%)"></div>' + corner
                + fix("left:0;right:0;bottom:200px;text-align:center", a("osw", 0.6, "fadeup", dot(sc["title"]), "font-size:84px")
                      + a("pl2", 1.2, "fade", esc(sc["text"]), "margin:22px auto 0;max-width:820px;text-align:center")) + cap(n, sc["cap"]))
    if k == "split":
        return (f'<div class="kb" data-kb="in" style="left:960px"><div class="bg" style="background-image:url({img(sc["img"])});background-size:cover;background-position:center"></div></div>' + corner
                + '<div class="abs" style="left:150px;width:660px">' + a("osw", 0.6, "fadeup", dot(sc["headline"]), f'font-size:{sc.get("size", 64)}px')
                + a("pl2", 1.4, "fade", mark(sc["text"]), "margin-top:30px") + "</div>" + cap(n, sc["cap"]))
    if k == "gallery":
        im = sc["imgs"]
        cells = [("150px", "130px", "540px", "830px"), ("720px", "130px", "520px", "400px"), ("1270px", "130px", "500px", "400px"),
                 ("720px", "560px", "520px", "400px"), ("1270px", "560px", "500px", "400px")]
        tiles = "".join(f'<div class="abs fix a" data-in="{0.3 + i * 0.25:.2f}" data-anim="fade" style="left:{x};top:{y};width:{w};height:{h};background:url({img(im[i])}) center/cover"></div>'
                        for i, (x, y, w, h) in enumerate(cells[:len(im)]))
        return corner + tiles + cap(n, sc["cap"])
    if k == "themes":
        items = "".join(a("th", 0.8 + i * 0.5, "fadeup", f'<div class="tht">{esc(t["t"])}</div><div class="pl2">{esc(t["d"])}</div>') for i, t in enumerate(sc["items"]))
        return (corner + fix("left:150px;right:150px;bottom:190px", (a("osw", 0.4, "fadeup", dot(sc["headline"]), "font-size:64px;margin-bottom:60px") if sc.get("headline") else "")
                + f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:56px 120px">{items}</div>') + cap(n, sc["cap"]))
    if k == "research":
        items = "".join(a("th", 1.0 + i * 0.5, "fadeup", f'<div class="tht">{esc(t["t"])}</div><div class="pl2">{esc(t["d"])}</div>') for i, t in enumerate(sc["items"]))
        pics = (f'<div class="abs fix a" data-in="0.4" data-anim="fade" style="left:1160px;top:130px;width:610px;height:400px;background:url({img(sc["imgs"][0])}) center/cover"></div>'
                f'<div class="abs fix a" data-in="0.7" data-anim="fade" style="left:1160px;top:560px;width:610px;height:400px;background:url({img(sc["imgs"][1])}) center/cover"></div>')
        return (corner + pics + fix("left:150px;top:130px;width:820px", a("pl2", 0.3, "fade", mark(sc["intro"]), "max-width:640px"))
                + fix("left:150px;bottom:150px;width:880px", f'<div style="display:grid;gap:40px">{items}</div>') + cap(n, sc["cap"]))
    if k == "idea":
        return (bg(img(sc["img"]), 0).replace('class="shade left"', 'class="shade right"') + corner
                + fix("right:150px;bottom:170px;width:860px;text-align:right", "".join(
                    a("idea", 0.8 + i * 1.2, "fadeup", mark(x), "margin-top:36px" if i else "") for i, x in enumerate(sc["paras"]))) + cap(n, sc["cap"]))
    if k == "band":
        return (corner + fix("left:150px;right:150px;top:150px;text-align:center", a("osw", 0.4, "fadeup", dot(sc["headline"]), f'font-size:{sc.get("size", 120)}px'))
                + f'<div class="abs fix a" data-in="0.9" data-anim="fade" style="left:150px;right:150px;top:380px;height:560px;background:url({img(sc["img"])}) center 40%/cover"></div>' + cap(n, sc["cap"]))
    if k == "character":
        return (f'<div class="kb" data-kb="in" style="left:960px"><div class="bg" style="background-image:url({img(sc["img"])});background-size:cover;background-position:center 30%"></div></div>' + corner
                + fix("left:150px;top:150px;width:700px", a("osw", 0.5, "fadeup", dot(sc["name"]), "font-size:72px"))
                + fix("left:150px;bottom:170px;width:620px", a("idea", 1.2, "fadeup", mark(sc["line"]), "text-align:left")) + cap(n, sc["cap"]))
    if k == "bignum":
        return (f'<div class="kb" data-kb="in" style="right:960px"><div class="bg" style="background-image:url({img(sc["img"])});background-size:cover;background-position:center;filter:grayscale(1) contrast(1.05)"></div></div>' + corner
                + fix("left:1060px;bottom:170px", a("osw", 0.6, "fadeup", esc(sc["n"]), "font-size:260px;line-height:.9")
                      + a("pl2", 1.2, "fade", esc(sc["label"]), "margin-top:18px")) + cap(n, sc["cap"]))
    if k == "timeline":
        cols = "".join(a("th", 0.6 + i * 0.4, "fadeup", f'<div class="tht" style="font-size:40px">{esc(c["t"])}</div><div class="pl2">{esc(c["d"])}</div>') for i, c in enumerate(sc["cols"]))
        ph = "".join(a("ph", 2.0 + i * 0.5, "fadeup", f'<i class="pd"></i><div class="phl">{esc(p["t"])}</div><div class="pl2" style="font-size:20px">{esc(p["d"])}</div>') for i, p in enumerate(sc["phases"]))
        return (corner + fix("left:150px;right:150px;top:150px", f'<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:70px">{cols}</div>')
                + fix("left:150px;right:150px;bottom:170px", a("tht", 1.6, "fade", esc(sc.get("line", "Timeline")), "color:var(--red)")
                      + '<div class="beam a" data-in="1.8" data-anim="beam" style="position:relative;left:0;top:0;width:100%;height:1px;border-radius:0;background:rgba(237,237,237,.25);box-shadow:none;margin-top:22px"></div>'
                      + f'<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:70px;margin-top:-6px">{ph}</div>') + cap(n, sc["cap"]))
    if k == "summary":
        rows = "".join(a("sr", 0.5 + i * 0.15, "fade", f'<span>{esc(l)}</span><div>{mark(v)}</div>') for i, (l, v) in enumerate(sc["rows"]))
        return corner + '<div class="abs" style="left:150px;width:1500px">' + rows + "</div>" + cap(n, sc["cap"])
    if k == "closer":
        return (f'<div class="kb" data-kb="in" style="left:860px"><div class="bg" style="background-image:url({img(sc["img"])});background-size:cover"></div></div>'
                '<div class="abs fix" style="inset:0;background:linear-gradient(90deg,#050505 40%,rgba(5,5,5,0) 75%)"></div>' + corner
                + fix("left:150px;bottom:170px;width:760px", a("pl2", 0.4, "fade", esc(sc["lead"]))
                      + a("osw", 0.8, "fadeup", dot(sc["headline"]), "font-size:56px;margin-top:22px")
                      + a("idea", 1.6, "fadeup", mark(sc["text"]), "text-align:left;margin-top:18px")) + cap(n, sc["cap"]))
    return None


PITCH_CSS = """
.osw { font-family:Osw; font-weight:500; letter-spacing:.005em; text-transform:uppercase; line-height:1.06; }
.pl2 { font-size:24px; line-height:1.45; color:#9a9a9e; }
.tht { font-family:Osw; font-weight:500; font-size:34px; text-transform:uppercase; margin-bottom:12px; }
.idea { font-size:36px; line-height:1.35; font-weight:400; color:#EDEDED; }
.shade.right { position:absolute; inset:0; background:linear-gradient(270deg, rgba(5,5,5,.9) 0%, rgba(5,5,5,.55) 40%, rgba(5,5,5,0) 70%); }
.sr { display:flex; gap:40px; padding:13px 0; border-bottom:1px solid rgba(237,237,237,.08); font-size:22px; color:#d8d8da; }
.sr > span { width:300px; flex:0 0 300px; font-weight:500; font-size:15px; letter-spacing:.12em; text-transform:uppercase; color:#8c8c90; padding-top:5px; }
.ph { position:relative; padding-top:26px; } .pd { position:absolute; left:0; top:-7px; width:13px; height:13px; border-radius:50%; background:var(--red); }
.phl { font-weight:600; font-size:16px; letter-spacing:.12em; text-transform:uppercase; margin-bottom:10px; }
"""


def scene_html(sc, n, img, meta):
    k = sc["kind"]
    ph = pitch_html(sc, n, img, meta)
    if ph is not None:
        return ph
    if k == "open" and sc.get("img"):
        # Board-style title poster: image, widely tracked BECOMING DOOM, thin red rule
        return (bg(img(sc["img"]), sc.get("shift", 0)).replace('class="shade left"', 'class="shade under"')
                + '<div class="abs" style="left:0;right:0;top:300px;text-align:center">'
                + a("trk", 0.6, "fade", 'BECOMING<span class="gap"></span>DOOM<span class="dot">.</span>')
                + '<div class="beam a" data-in="1.4" data-anim="beam" style="position:relative;left:0;top:0;width:240px;height:3px;border-radius:0;background:var(--red);box-shadow:none;margin:34px auto 0"></div>'
                + a("kick", 2.0, "fade", esc(sc.get("line", "Six weeks. One mission. Become dangerous.")), "margin-top:34px;letter-spacing:.5em")
                + "</div>")
    if k == "poster":
        # Minimal premium poster: image, one widely tracked word or line, a thin rule and a quiet line
        side = sc.get("align", "left")
        pos = "left:150px;width:1150px" if side == "left" else "left:0;right:0;text-align:center"
        rule = "margin:34px 0 0" if side == "left" else "margin:34px auto 0"
        back = bg(img(sc["img"]), sc.get("shift", 0))
        if side != "left":
            back = back.replace('class="shade left"', 'class="shade under"')
        return (back + hud(sc.get("hud"))
                + f'<div class="abs" style="top:300px;{pos}">'
                + (a("kick", 0.4, "fade", esc(sc["kicker"]), "letter-spacing:.42em") if sc.get("kicker") else "")
                + a("trk", 0.9, "fade", "<br>".join(dot(x) for x in sc["lines"]), f'font-size:{sc.get("size", 96)}px;margin-top:30px')
                + f'<div class="beam a" data-in="1.8" data-anim="beam" style="position:relative;left:0;top:0;width:180px;height:3px;border-radius:0;background:var(--red);box-shadow:none;{rule}"></div>'
                + (a("pline", 2.4, "fade", mark(sc["text"])) if sc.get("text") else "")
                + "</div>" + cap(n, sc["cap"]))
    if k == "dossier":
        # Character file: portrait on the left, a framed data sheet with meters on the right
        bars = "".join(a("meter", 1.6 + i * 0.6, "fadeup",
                         f'<div class="ml"><span>{esc(m["t"])}</span><b{" class=hot" if i == sc.get("hot") else ""}>{m["v"]}%</b></div>'
                         f'<div class="mb"><i class="a{" hot" if i == sc.get("hot") else ""}" data-in="{2.0 + i * 0.6:.1f}" data-anim="beam" style="width:{m["v"]}%"></i></div>'
                         f'<div class="md">{esc(m["d"])}</div>') for i, m in enumerate(sc["meters"]))
        fields = "".join(f'<div class="fd"><span>{esc(k2)}</span><div>{mark(v)}</div></div>' for k2, v in sc["fields"])
        return ('<div class="kb" data-kb="in" style="right:960px"><div class="bg" style="background-image:url(' + img(sc["img"]) + ');background-size:cover;background-position:center 30%"></div></div>'
                + '<div class="abs dossier-edge"></div>' + hud(sc.get("hud", "SUBJECT FILE / 001"))
                + '<div class="abs" style="left:1060px;top:200px;width:710px">'
                + a("kick", 0.3, "fade", esc(sc["kicker"]), "letter-spacing:.42em")
                + a("anton", 0.6, "fadeup", dot(sc["headline"]), f'font-size:{sc.get("size", 96)}px;margin-top:22px')
                + a("fields", 1.0, "fade", fields) + bars + "</div>" + cap(n, sc["cap"]))
    if k == "open":
        # Logo option A: spaced BECOMING over a large DOOM, red full stop, red rule
        return ('<div class="abs" style="left:150px;top:300px">'
                + a("logo-top", 0.6, "fade", "BECOMING")
                + a("anton", 1.0, "punch", 'DOOM<span class="dot">.</span>', "font-size:300px;line-height:.86;margin-top:8px")
                + '<div class="beam a" data-in="1.6" data-anim="beam" style="position:relative;left:0;top:0;width:100%;height:14px;border-radius:0;background:var(--red);box-shadow:none;margin-top:26px"></div>'
                + a("kick", 2.2, "fade", esc(sc.get("line", "Six weeks. One mission. Become dangerous.")), "margin-top:40px")
                + "</div>")
    if k == "labels":
        cls = ["grey", "red", "ink"]
        name = sc.get("img", "life")
        back = bg(img(name), sc.get("shift", 200)) if (OUT_ASSETS / meta["id"] / f"{name}.png").exists() else ""
        return (back + '<div class="abs" style="left:150px;top:330px">'
                + "<br>".join(a(f"lbl {cls[i % 3]}", 0.2 + i * 0.5, "slam", esc(w)) for i, w in enumerate(sc["words"]))
                + "</div>")
    if k == "title":
        return (hud(sc.get("hud")) + bg(img(sc["img"]), sc.get("shift", 180))
                + '<div class="abs" style="left:150px;top:330px;width:1100px">'
                + a("kick", 0.8, "fade", f'Week {meta["week"]} &nbsp;/&nbsp; {WEEKS[meta["week"]]} &nbsp;/&nbsp; Lesson {meta["lesson"]:02d}')
                + f'<div class="anton" style="font-size:{sc.get("size", 180)}px;margin-top:30px">{rise_lines(sc["lines"], 1.2)}</div></div>'
                + cap(n, sc["cap"]))
    if k == "hook":
        return (hud(sc.get("hud")) + bg(img(sc["img"]), sc.get("shift", 240))
                + '<div class="abs" style="left:150px;top:300px;width:860px">'
                + a("kick", 0.5, "fade", mark(sc["lead"]), "font-size:30px;color:#b4b4b8;letter-spacing:0;text-transform:none")
                + a("anton", 2.2, "fadeup", dot(sc["headline"]), f'font-size:{sc.get("size", 140)}px;margin-top:30px')
                + "</div>" + cap(n, sc["cap"]))
    if k == "image":
        return (hud(sc.get("hud")) + bg(img(sc["img"]), sc.get("shift", 260))
                + '<div class="abs" style="left:150px;top:310px;width:900px">'
                + a("kick", 0.5, "fade", esc(sc["kicker"]))
                + f'<div class="anton" style="font-size:{sc.get("size", 150)}px;margin-top:30px">{rise_lines(sc["lines"])}</div></div>'
                + cap(n, sc["cap"]))
    if k == "red":
        return ('<div class="abs redpanel a" data-in="0" data-anim="wipe"></div>'
                '<div class="abs" style="left:150px;top:200px;width:1600px;color:#0a0a0a">'
                + a("kick", 0.6, "fade", esc(sc["kicker"]), "color:#0a0a0a")
                + f'<div class="anton" style="font-size:{sc.get("size", 150)}px;margin-top:30px;color:#0a0a0a">'
                + rise_lines(sc["lines"], 0.9, 0.3, "color:#fff") + "</div></div>" + cap(n, sc["cap"]))
    if k == "list":
        rows = []
        for i, it in enumerate(sc["items"]):
            t = 1.4 + i
            strike = a("strike", 5.2 + i * 0.5, "strike", "") if i in sc.get("strike", []) else ""
            title = (a("t", 6.3, "tored", esc(it["t"])) if i == sc.get("hot") else f'<div class="t">{esc(it["t"])}</div>')
            rows.append(a("row", t, "fadeup", f'<div class="n">{i + 1:02d}</div><div style="position:relative">{title}<div class="d">{esc(it["d"])}</div>{strike}</div>'))
        return ('<div class="abs" style="left:150px;top:260px;width:640px">' + a("kick", 0.3, "fade", esc(sc["kicker"]))
                + a("anton", 0.7, "fadeup", dot(sc["headline"]), f'font-size:{sc.get("size", 120)}px;margin-top:30px') + "</div>"
                + '<div class="abs" style="left:950px;top:280px;width:820px">' + "".join(rows) + "</div>" + cap(n, sc["cap"]))
    if k == "scene":
        return (hud(sc.get("hud")) + bg(img(sc["img"]), sc.get("shift", 120))
                + '<div class="abs" style="left:150px;top:300px;width:900px">' + a("kick", 0.6, "fade", esc(sc["kicker"]))
                + a("anton", 1.4, "fadeup", "<br>".join(dot(x) for x in sc["a"]), "font-size:124px;margin-top:30px;line-height:.95")
                + a("anton", 3.0, "fadeup", "<br>".join(dot(x) for x in sc["b"]), "font-size:124px;margin-top:24px;line-height:.95")
                + "</div>" + cap(n, sc["cap"]))
    if k == "compare":
        cols = []
        for i, c in enumerate(sc["cols"]):
            hot = i == sc.get("hot", len(sc["cols"]) - 1)
            big = dot(c["big"]) if hot else esc(c["big"])
            cols.append(a("col" + (" hot" if hot else ""), 0.9 + i * 1.1, "fadeup",
                          f'<div class="anton" style="font-size:{c.get("size", 110)}px{"" if hot else ";color:#3a3a3d"}">{big}</div>'
                          f'<div class="ct">{esc(c["title"])}</div><div class="small"{" style=\"color:#c8c8ca\"" if hot else ""}>{esc(c["text"])}</div>'))
        q = a("quote", 5.0, "fadeup", "“" + esc(sc["quote"]) + "”") if sc.get("quote") else ""
        return ('<div class="abs" style="left:150px;top:200px;width:1620px">' + a("kick", 0.3, "fade", esc(sc["kicker"]))
                + f'<div style="display:grid;grid-template-columns:repeat({len(cols)},1fr);gap:56px;margin-top:60px">' + "".join(cols) + "</div>"
                + q + "</div>" + cap(n, sc["cap"]))
    if k == "grunge":
        return ('<div class="abs" style="left:0;right:0;top:110px;text-align:center">'
                + a("anton grunge", 0.3, "punch", "<br>".join(esc(x) for x in sc["lines"]), f'font-size:{sc.get("size", 300)}px;line-height:.9;color:#9E0B0B')
                + "</div>" + a("abs side", 1.4, "fade", f'{esc(sc["side"])}<br><span>{esc(sc["note"])}</span>', "right:150px;top:790px")
                + cap(n, sc["cap"]))
    if k == "card":
        w = sc["words"]
        return ('<div class="abs" style="left:150px;top:300px"><div class="bold">'
                + "".join(a("red2" if i == len(w) - 1 else "", 0.2 + i * 0.5, "pop", esc(x)) for i, x in enumerate(w))
                + "</div></div>")
    if k == "steps":
        rows = "".join(a("row", 1.6 + i * 0.7, "fadeup", f'<div class="n">{i + 1:02d}</div><div class="d2">{esc(x)}</div>') for i, x in enumerate(sc["items"]))
        return ('<div class="abs" style="left:150px;top:180px;width:1620px">' + a("kick", 0.3, "fade", esc(sc["kicker"]))
                + a("anton", 0.7, "fadeup", dot(sc["headline"]), "font-size:150px;margin-top:26px")
                + f'<div style="display:grid;grid-template-columns:1fr 1fr;column-gap:90px;margin-top:50px">{rows}</div></div>' + cap(n, sc["cap"]))
    if k == "mission":
        rows = "".join(a("row", 1.4 + i * 0.8, "fadeup", f'<div class="n" style="width:200px;flex:0 0 200px">{esc(l)}</div><div class="d2">{esc(t)}</div>')
                       for i, (l, t) in enumerate(sc["rows"]))
        return ('<div class="abs" style="left:150px;top:260px;width:1620px;display:grid;grid-template-columns:640px 1fr;gap:90px">'
                + "<div>" + a("kick", 0.3, "fade", f'Day {meta["day"]} / Workbook {meta["workbook"]}')
                + a("anton", 0.7, "fadeup", 'TODAY’S<br><span class="redt">MISSION.</span>', "font-size:180px;margin-top:26px") + "</div>"
                + f'<div style="padding-top:30px">{rows}</div></div>' + cap(n, sc["cap"]))
    if k == "close":
        return (hud(sc.get("hud")) + bg(img(sc["img"]), sc.get("shift", 0))
                + '<div class="abs" style="left:150px;top:300px;width:1050px">'
                + f'<div class="anton" style="font-size:{sc.get("size", 130)}px">{rise_lines(sc["lines"])}</div>'
                + a("give", 3.2, "fadeup", esc(sc["give"]))
                + a("kick", 5.3, "fade", esc(sc["next"]), "margin-top:46px") + "</div>" + cap(n, sc["cap"]))
    if k == "question":
        sub = a("qsub", 3.2, "fade", esc(sc["sub"])) if sc.get("sub") else ""
        return ('<div class="abs" style="left:200px;right:200px;top:250px;text-align:center">'
                + a("qlead", 0.3, "fade", esc(sc["lead"]))
                + a("qbig", 1.0, "fadeup", mark(sc["question"])) + sub + "</div>" + cap(n, sc["cap"]))
    if k == "stats":
        items = "".join(a("stat", 1.2 + i * 1.0, "fadeup",
                          f'<div class="sn{" hot" if i == sc.get("hot") else ""}">{esc(s["n"])}</div><div class="sl{" hot" if i == sc.get("hot") else ""}">{esc(s["label"])}</div><div class="sc">{esc(s["text"])}</div>')
                        for i, s in enumerate(sc["items"]))
        return ('<div class="abs" style="left:150px;top:180px;width:760px">' + a("kick", 0.2, "fade", esc(sc["kicker"]))
                + a("light", 0.5, "fadeup", mark(sc["headline"]), "margin-top:40px") + "</div>"
                + f'<div class="abs" style="left:1060px;top:170px;width:700px">{items}</div>' + cap(n, sc["cap"]))
    if k == "radial":
        pills = sc["pills"]
        pos = [(1080, 250), (1430, 190), (1500, 410), (1440, 650), (1100, 800), (900, 560), (1330, 880)]
        ph = "".join(a("pill", 1.4 + i * 0.35, "fade", esc(p), f"left:{pos[i][0]}px;top:{pos[i][1]}px") for i, p in enumerate(pills[:7]))
        rings = "".join(f'<div class="ring a" data-in="{0.2 + i * 0.2:.1f}" data-anim="fade" style="width:{r * 2}px;height:{r * 2}px;left:{1400 - r}px;top:{540 - r}px"></div>' for i, r in enumerate([220, 400, 580, 760]))
        return ('<div class="abs glow a" data-in="0" data-anim="fade"></div>' + rings + ph
                + a("pill core", 1.0, "fade", esc(sc["core"]), "left:1260px;top:510px")
                + '<div class="abs" style="left:150px;top:380px;width:760px">'
                + a("light", 0.5, "fadeup", "<br>".join(mark(x) for x in sc["lines"]))
                + a("small", 2.4, "fade", esc(sc["text"]), "margin-top:36px;max-width:620px") + "</div>" + cap(n, sc["cap"]))
    if k == "story":
        beats = "".join(a("beat", 1.4 + i * 1.2, "fadeup", f'<div class="kick" style="color:var(--red)">{esc(b["t"])}</div><div class="bt">{esc(b["d"])}</div>')
                        for i, b in enumerate(sc["beats"]))
        return ('<div class="abs" style="left:150px;top:200px;width:1620px">' + a("kick", 0.3, "fade", esc(sc["kicker"]))
                + a("anton", 0.7, "fadeup", dot(sc["headline"]), f'font-size:{sc.get("size", 120)}px;margin-top:26px')
                + f'<div style="display:grid;grid-template-columns:repeat({len(sc["beats"])},1fr);gap:64px;margin-top:64px">{beats}</div></div>'
                + cap(n, sc["cap"]))
    if k == "recap":
        rows = "".join(a("row", 1.2 + i * 0.8, "fadeup", f'<div class="n">{i + 1:02d}</div><div class="rc">{mark(x)}</div>') for i, x in enumerate(sc["items"]))
        return ('<div class="abs" style="left:150px;top:300px;width:560px">' + a("kick", 0.3, "fade", esc(sc.get("kicker", "Before you start")))
                + a("anton", 0.6, "fadeup", dot(sc.get("headline", "KEEP THESE.")), "font-size:150px;margin-top:26px") + "</div>"
                + f'<div class="abs" style="left:820px;top:300px;width:950px">{rows}</div>' + cap(n, sc["cap"]))
    raise ValueError(f"unknown kind {k}")


EXTRA_CSS = """
.lbl { font-family:Anton; font-size:140px; letter-spacing:.01em; padding:6px 26px 10px; }
.bold { font-weight:500; }
.logo-top { font-weight:600; font-size:44px; letter-spacing:.62em; margin-left:8px; }
.bt { font-size:34px; font-weight:400; line-height:1.3; margin-top:18px; color:#d8d8da; }
.rc { font-size:46px; font-weight:400; line-height:1.15; letter-spacing:-.01em; }
.shade.under { position:absolute; inset:0; background:radial-gradient(ellipse at 50% 46%, rgba(3,3,3,.62) 0%, rgba(3,3,3,.35) 45%, rgba(3,3,3,.85) 100%); }
.trk { font-weight:600; font-size:96px; letter-spacing:.42em; line-height:1.15; text-transform:uppercase; margin-right:-.42em; }
.trk .gap { display:inline-block; width:.9em; }
.pline { font-size:30px; font-weight:400; line-height:1.4; color:#b4b4b8; margin-top:34px; max-width:760px; }
.hudf { position:absolute; inset:40px 60px; z-index:18; pointer-events:none; }
.hudf .c { position:absolute; width:46px; height:46px; border:2px solid rgba(237,237,237,.55); }
.hudf .tl { left:0; top:0; border-right:0; border-bottom:0; } .hudf .tr { right:0; top:0; border-left:0; border-bottom:0; }
.hudf .bl { left:0; bottom:0; border-right:0; border-top:0; } .hudf .br { right:0; bottom:0; border-left:0; border-top:0; }
.hudf .hl, .hudf .hr { position:absolute; top:14px; font-weight:600; font-size:15px; letter-spacing:.34em; color:rgba(237,237,237,.7); }
.hudf .hl { left:70px; } .hudf .hr { right:70px; } .hudf .hr b { color:var(--red); font-weight:400; }
.hudf .xh { position:absolute; right:-1px; top:50%; width:22px; height:2px; background:rgba(237,237,237,.55); }
.dossier-edge { left:960px; top:0; bottom:0; width:2px; background:var(--red); }
.fields { margin-top:34px; border-top:1px solid #1c1c1e; }
.fd { display:flex; gap:28px; padding:14px 0; border-bottom:1px solid #1c1c1e; font-size:26px; }
.fd > span { width:170px; flex:0 0 170px; font-weight:600; font-size:16px; letter-spacing:.3em; color:var(--stone); padding-top:7px; }
.meter { margin-top:30px; }
.ml { display:flex; justify-content:space-between; font-weight:600; font-size:18px; letter-spacing:.3em; }
.ml b { font-weight:600; color:#b4b4b8; } .ml b.hot { color:var(--red); }
.mb { height:8px; background:#1d1b1a; margin-top:12px; } .mb i { display:block; height:100%; background:#b4b4b8; transform-origin:left; } .mb i.hot { background:var(--red); }
.md { font-size:22px; color:var(--stone); margin-top:10px; }
.vc { top:0; bottom:0; display:flex; flex-direction:column; justify-content:center; }
.grey { color:#6d6863; }
.onred .dot { color:#fff; }
.qlead { font-size:34px; font-weight:400; color:#b4b4b8; }
.qbig { font-size:128px; font-weight:500; line-height:1.08; letter-spacing:-.02em; margin-top:46px; }
.qsub { font-size:28px; color:var(--stone); margin:56px auto 0; max-width:900px; line-height:1.4; }
.light { font-size:84px; font-weight:400; line-height:1.08; letter-spacing:-.02em; }
.stat { margin-bottom:46px; }
.sn { font-size:96px; font-weight:400; line-height:1; letter-spacing:-.02em; }
.sl { font-size:44px; font-weight:400; text-transform:uppercase; margin-top:6px; }
.sn.hot, .sl.hot { color:var(--red); }
.sc { font-size:22px; color:var(--stone); margin-top:10px; max-width:560px; line-height:1.35; }
.glow { inset:0; background:radial-gradient(circle at 1600px 540px, rgba(232,35,26,.55) 0, rgba(140,20,14,.28) 26%, rgba(6,6,6,0) 58%); }
.ring { position:absolute; border-radius:50%; border:1px solid rgba(255,90,70,.28); }
.pill { position:absolute; padding:12px 26px; border-radius:40px; font-size:24px; color:#EDEDED; background:rgba(60,12,9,.75); border:1px solid rgba(255,90,70,.45); white-space:nowrap; }
.pill.core { font-size:32px; padding:16px 34px; background:rgba(120,20,14,.85); border-color:rgba(255,120,100,.7); }
"""


def build(spec_path):
    spec = json.loads(Path(spec_path).read_text())
    if CLASSY:
        spec = classy_spec(spec)
    lid = spec["id"]
    meta = dict(id=spec.get("assets", lid), week=spec.get("week") or int(lid[1:3]), lesson=spec.get("lesson") or int(lid[-2:]),
                day=spec["day"], workbook=spec["workbook"])
    img = lambda name: f"../assets/{meta['id']}/{name}.png"
    tpl = (ROOT / "tools/film_template.html").read_text()
    head = tpl.split("<div id=\"stage\">")[0]
    tail = "<div id=\"grain\">" + tpl.split("<div id=\"grain\">")[1]
    head = re.sub(r"<title>.*?</title>", f"<title>Becoming Doom {lid}</title>", head)
    head = head.replace("</style>", EXTRA_CSS + (CLASSY_CSS if CLASSY else "") + PITCH_CSS + "</style>")
    if CLASSY:
        tail = tail.replace('<div id="hud">BECOMING DOOM<b>.</b></div>', '<div id="hud">Becoming Doom</div>')
    secs, t, n = [], 0.0, 0
    for sc in spec["scenes"]:
        if "cap" in sc:
            n += 1
        d = sc.get("dur", DUR[sc["kind"]])
        cls = "onred" if sc["kind"] == "red" else ""
        secs.append(f'<section class="scene {cls}" data-start="{t:g}" data-dur="{d:g}" data-kind="{sc["kind"]}">' + (classy_sizes if CLASSY else str)(centre_blocks(scene_html(sc, n, img, meta))) + "</section>")
        t += d
    tail = re.sub(r"TOTAL=\d+(\.\d+)?", f"TOTAL={t:g}", tail)
    out = head + '<div id="stage">\n' + "\n".join(secs) + "\n\n" + tail
    (ROOT / f"course/video/film/{lid}.html").write_text(out)
    write_script(spec, meta)
    print(f"{lid}: {len(secs)} scenes, {t:g}s")


def plain(s):
    return re.sub(r"[*_]", "", s)


def onscreen(sc):
    k = sc["kind"]
    if k in ("title", "image", "red", "close"):
        return " ".join(plain(x) for x in sc["lines"])
    if k == "hook":
        return plain(sc["lead"]) + " " + plain(sc["headline"])
    if k in ("list", "steps"):
        return plain(sc["headline"])
    if k == "scene":
        return " ".join(plain(x) for x in sc["a"] + sc["b"])
    if k in ("compare",):
        return sc["kicker"]
    if k == "grunge":
        return " ".join(sc["lines"])
    if k == "card":
        return " ".join(sc["words"])
    if k == "labels":
        return " / ".join(sc["words"])
    if k == "question":
        return plain(sc["question"])
    if k in ("stats", "radial"):
        return plain(sc.get("headline", " ".join(sc.get("lines", []))))
    if k == "poster":
        return " ".join(plain(x) for x in sc["lines"])
    if k == "dossier":
        return plain(sc["headline"])
    if k == "mission":
        return "Today's mission"
    return "Becoming Doom"


def write_script(spec, meta):
    lid = spec["id"]
    L = [f"# {lid}: {spec['title']}", "",
         f"Video {spec['number']} of 18 • Week {meta['week']}: {WEEKS[meta['week']]}", "",
         f"- **Principles:** {spec['principles']}",
         f"- **Model:** {spec.get('model', 'none new')}",
         f"- **Leads to:** workbook page {meta['workbook']} (Day {meta['day']})",
         f"- **Evidence:** {spec['evidence']}",
         f"- **Protagonist:** {spec['cast']}",
         "- **Recording format:** presenter to camera with full-screen slide cutaways. Each block is one slide. **Say** is the teleprompter script and sits in the slide's speaker notes.",
         "", "---", ""]
    i = 0
    for sc in spec["scenes"]:
        if not sc.get("say"):
            continue
        i += 1
        L += [f"## Slide {i} | {sc['kind']}", "", f"**On screen:** {onscreen(sc)}"]
        if sc.get("img"):
            L.append(f"**Visual:** {sc['img']}")
        L += ["", "**Say:**", ""]
        for p in sc["say"]:
            L += [p, ""]
    words = sum(len(p.split()) for sc in spec["scenes"] for p in sc.get("say", []))
    L += ["---", "", f"Spoken words: about {words}, roughly {round(words / 140)} minutes at a steady pace plus pauses.", ""]
    if spec.get("notes"):
        L += ["## Production notes", ""] + [f"- {x}" for x in spec["notes"]] + [""]
    (ROOT / f"course/video/{lid}.md").write_text("\n".join(L))


if __name__ == "__main__":
    for p in sys.argv[1:]:
        build(p)
