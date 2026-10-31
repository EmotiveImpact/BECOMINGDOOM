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
DUR = dict(poster=8, dossier=12,
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


def scene_html(sc, n, img, meta):
    k = sc["kind"]
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
        return ('<div class="kb" data-kb="in" style="right:960px"><div class="bg" style="background-image:url(' + img(sc["img"]) + ');background-size:cover;background-position:30% center"></div></div>'
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
                + a("kick", 0.5, "fade", mark(sc["lead"]), "font-size:30px;color:#cfcac3;letter-spacing:0;text-transform:none")
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
                          f'<div class="anton" style="font-size:{c.get("size", 110)}px{"" if hot else ";color:#4a4642"}">{big}</div>'
                          f'<div class="ct">{esc(c["title"])}</div><div class="small"{" style=\"color:#d6d1ca\"" if hot else ""}>{esc(c["text"])}</div>'))
        q = a("quote", 5.0, "fadeup", "“" + esc(sc["quote"]) + "”") if sc.get("quote") else ""
        return ('<div class="abs" style="left:150px;top:200px;width:1620px">' + a("kick", 0.3, "fade", esc(sc["kicker"]))
                + f'<div style="display:grid;grid-template-columns:repeat({len(cols)},1fr);gap:56px;margin-top:60px">' + "".join(cols) + "</div>"
                + q + "</div>" + cap(n, sc["cap"]))
    if k == "grunge":
        return ('<div class="abs" style="left:0;right:0;top:110px;text-align:center">'
                + a("anton grunge", 0.3, "punch", "<br>".join(esc(x) for x in sc["lines"]), f'font-size:{sc.get("size", 300)}px;line-height:.9;color:#b3231b')
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
.bt { font-size:34px; font-weight:400; line-height:1.3; margin-top:18px; color:#e2ddd6; }
.rc { font-size:46px; font-weight:400; line-height:1.15; letter-spacing:-.01em; }
.shade.under { position:absolute; inset:0; background:radial-gradient(ellipse at 50% 46%, rgba(6,6,6,.55) 0%, rgba(6,6,6,.25) 45%, rgba(6,6,6,.7) 100%); }
.trk { font-weight:600; font-size:96px; letter-spacing:.42em; line-height:1.15; text-transform:uppercase; margin-right:-.42em; }
.trk .gap { display:inline-block; width:.9em; }
.pline { font-size:30px; font-weight:400; line-height:1.4; color:#cfcac3; margin-top:34px; max-width:760px; }
.hudf { position:absolute; inset:40px 60px; z-index:18; pointer-events:none; }
.hudf .c { position:absolute; width:46px; height:46px; border:2px solid rgba(242,239,234,.55); }
.hudf .tl { left:0; top:0; border-right:0; border-bottom:0; } .hudf .tr { right:0; top:0; border-left:0; border-bottom:0; }
.hudf .bl { left:0; bottom:0; border-right:0; border-top:0; } .hudf .br { right:0; bottom:0; border-left:0; border-top:0; }
.hudf .hl, .hudf .hr { position:absolute; top:14px; font-weight:600; font-size:15px; letter-spacing:.34em; color:rgba(242,239,234,.7); }
.hudf .hl { left:70px; } .hudf .hr { right:70px; } .hudf .hr b { color:var(--red); font-weight:400; }
.hudf .xh { position:absolute; right:-1px; top:50%; width:22px; height:2px; background:rgba(242,239,234,.55); }
.dossier-edge { left:960px; top:0; bottom:0; width:2px; background:var(--red); }
.fields { margin-top:34px; border-top:1px solid #2a2724; }
.fd { display:flex; gap:28px; padding:14px 0; border-bottom:1px solid #2a2724; font-size:26px; }
.fd > span { width:170px; flex:0 0 170px; font-weight:600; font-size:16px; letter-spacing:.3em; color:var(--stone); padding-top:7px; }
.meter { margin-top:30px; }
.ml { display:flex; justify-content:space-between; font-weight:600; font-size:18px; letter-spacing:.3em; }
.ml b { font-weight:600; color:#cfcac3; } .ml b.hot { color:var(--red); }
.mb { height:8px; background:#1d1b1a; margin-top:12px; } .mb i { display:block; height:100%; background:#cfcac3; transform-origin:left; } .mb i.hot { background:var(--red); }
.md { font-size:22px; color:var(--stone); margin-top:10px; }
.vc { top:0; bottom:0; display:flex; flex-direction:column; justify-content:center; }
.grey { color:#6d6863; }
.onred .dot { color:#fff; }
.qlead { font-size:34px; font-weight:400; color:#cfcac3; }
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
.pill { position:absolute; padding:12px 26px; border-radius:40px; font-size:24px; color:#f2efea; background:rgba(60,12,9,.75); border:1px solid rgba(255,90,70,.45); white-space:nowrap; }
.pill.core { font-size:32px; padding:16px 34px; background:rgba(120,20,14,.85); border-color:rgba(255,120,100,.7); }
"""


def build(spec_path):
    spec = json.loads(Path(spec_path).read_text())
    lid = spec["id"]
    meta = dict(id=lid, week=int(lid[1:3]), lesson=int(lid[-2:]), day=spec["day"], workbook=spec["workbook"])
    img = lambda name: f"../assets/{lid}/{name}.png"
    tpl = (ROOT / "tools/film_template.html").read_text()
    head = tpl.split("<div id=\"stage\">")[0]
    tail = "<div id=\"grain\">" + tpl.split("<div id=\"grain\">")[1]
    head = re.sub(r"<title>.*?</title>", f"<title>Becoming Doom {lid}</title>", head)
    head = head.replace("</style>", EXTRA_CSS + "</style>")
    secs, t, n = [], 0.0, 0
    for sc in spec["scenes"]:
        if "cap" in sc:
            n += 1
        d = sc.get("dur", DUR[sc["kind"]])
        cls = "onred" if sc["kind"] == "red" else ""
        secs.append(f'<section class="scene {cls}" data-start="{t:g}" data-dur="{d:g}" data-kind="{sc["kind"]}">' + centre_blocks(scene_html(sc, n, img, meta)) + "</section>")
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
