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
DUR = dict(open=5, labels=4, title=9, hook=9, image=8, red=8, list=10, scene=8, compare=10,
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
    offs = [-42, 35, 21, 7, -7, -21, -35, 42, 28, 14, 0, -14]
    x0 = 1240 - shift
    sl = "".join(
        f'<i style="left:{x0 + i * 44}px;width:44px;background-image:url({img});background-position:{-(x0 + i * 44)}px 0" data-off="{o}"></i>'
        for i, o in enumerate(offs))
    return (f'<div class="kb"{style} data-kb="in"><div class="bg" style="background-image:url({img})"></div>'
            f'<div class="slices">{sl}</div><div class="shade left"></div></div>')


def cap(n, title):
    return f'<div class="cap a" data-in="0.6" data-anim="fade"><span class="cn">{n:02d}</span>{esc(title)}</div>'


def scene_html(sc, n, img, meta):
    k = sc["kind"]
    if k == "open":
        return ('<div class="beam a" data-in="0.3" data-anim="beam" style="left:150px;top:600px;width:1620px"></div>'
                '<div class="abs" style="left:150px;top:400px">'
                + a("anton", 1.2, "punch", 'BECOMING DOOM<span class="dot">.</span>', "font-size:190px")
                + a("kick", 2.2, "fade", esc(sc.get("line", "Six weeks. One mission. Become dangerous.")), "margin-top:70px")
                + "</div>")
    if k == "labels":
        cls = ["grey", "red", "ink"]
        return ('<div class="abs" style="left:150px;top:330px">'
                + "<br>".join(a(f"lbl {cls[i % 3]}", 0.2 + i * 0.5, "slam", esc(w)) for i, w in enumerate(sc["words"]))
                + "</div>")
    if k == "title":
        return (bg(img(sc["img"]), sc.get("shift", 0))
                + '<div class="abs" style="left:150px;top:330px;width:1100px">'
                + a("kick", 0.8, "fade", f'Week {meta["week"]} &nbsp;/&nbsp; {WEEKS[meta["week"]]} &nbsp;/&nbsp; Lesson {meta["lesson"]:02d}')
                + f'<div class="anton" style="font-size:{sc.get("size", 180)}px;margin-top:30px">{rise_lines(sc["lines"], 1.2)}</div></div>'
                + cap(n, sc["cap"]))
    if k == "hook":
        return (bg(img(sc["img"]), sc.get("shift", 0))
                + '<div class="abs" style="left:150px;top:300px;width:1000px">'
                + a("kick", 0.5, "fade", mark(sc["lead"]), "font-size:30px;color:#cfcac3;letter-spacing:0;text-transform:none")
                + a("anton", 2.2, "fadeup", dot(sc["headline"]), f'font-size:{sc.get("size", 140)}px;margin-top:30px')
                + "</div>" + cap(n, sc["cap"]))
    if k == "image":
        return (bg(img(sc["img"]), sc.get("shift", 260))
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
        return (bg(img(sc["img"]), sc.get("shift", 420))
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
                + "</div>" + a("abs side", 1.4, "fade", f'{esc(sc["side"])}<br><span>{esc(sc["note"])}</span>', "right:150px;top:470px")
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
        return (bg(img(sc["img"]), sc.get("shift", 0))
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
        pos = [(1180, 260), (1560, 210), (1680, 420), (1600, 640), (1220, 800), (980, 560), (1450, 880)]
        ph = "".join(a("pill", 1.4 + i * 0.35, "fade", esc(p), f"left:{pos[i][0]}px;top:{pos[i][1]}px") for i, p in enumerate(pills[:7]))
        rings = "".join(f'<div class="ring a" data-in="{0.2 + i * 0.2:.1f}" data-anim="fade" style="width:{r * 2}px;height:{r * 2}px;left:{1500 - r}px;top:{540 - r}px"></div>' for i, r in enumerate([220, 400, 580, 760]))
        return ('<div class="abs glow a" data-in="0" data-anim="fade"></div>' + rings + ph
                + a("pill core", 1.0, "fade", esc(sc["core"]), "left:1380px;top:510px")
                + '<div class="abs" style="left:150px;top:380px;width:760px">'
                + a("light", 0.5, "fadeup", "<br>".join(mark(x) for x in sc["lines"]))
                + a("small", 2.4, "fade", esc(sc["text"]), "margin-top:36px;max-width:620px") + "</div>" + cap(n, sc["cap"]))
    raise ValueError(f"unknown kind {k}")


EXTRA_CSS = """
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
.glow { inset:0; background:radial-gradient(circle at 1720px 540px, rgba(232,35,26,.55) 0, rgba(140,20,14,.28) 26%, rgba(6,6,6,0) 58%); }
.ring { position:absolute; border-radius:50%; border:1px solid rgba(255,90,70,.28); }
.pill { position:absolute; padding:12px 26px; border-radius:40px; font-size:24px; color:#f2efea; background:rgba(60,12,9,.75); border:1px solid rgba(255,90,70,.45); white-space:nowrap; }
.pill.core { font-size:32px; padding:16px 34px; background:rgba(120,20,14,.85); border-color:rgba(255,120,100,.7); }
"""


def build(spec_path):
    spec = json.loads(Path(spec_path).read_text())
    lid = spec["id"]
    meta = dict(week=int(lid[1:3]), lesson=int(lid[-2:]), day=spec["day"], workbook=spec["workbook"])
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
        secs.append(f'<section class="scene {cls}" data-start="{t:g}" data-dur="{d:g}" data-kind="{sc["kind"]}">' + scene_html(sc, n, img, meta) + "</section>")
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
