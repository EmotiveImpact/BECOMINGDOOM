#!/usr/bin/env python3
"""Build an editable Slides-artifact deck (project/deck.json + project/slides/*.html)
from a Becoming Doom lesson script (course/lessons/Wxx-Lyy.md).

Usage:
    python3 tools/build_slides_artifact.py W01-L01 <out_root> [--images images.json]
    python3 tools/build_slides_artifact.py --dump            # print parsed items for review

The look follows the locked component system in the "Becoming Doom Layouts" deck:
Inter Tight only (headlines 500, sentence case, tight tracking; labels 600 spaced caps),
red full stops, near-black backgrounds, one red accent, content vertically centred,
and every even slide a real-life scene image with the words set over it.
Scene images that do not exist yet are left as empty image frames (fill them in the
editor with Add image) and carry the image brief in their alt text and speaker notes.
"""
import html
import json
import os
import re
import sys
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LESSONS = os.path.join(ROOT, "course", "lessons")
OVERRIDES = os.path.join(ROOT, "course", "slides", "overrides.json")

FONT = "'Inter Tight', Arial, sans-serif"
BG_IMG = "#070707"
BG = "#0B0B0C"
RED = "#D90D0D"
WHITE = "#EDEDED"
SOFT = "#D8D8DA"
GREY = "#9A9A9E"
DIM = "#8C8C90"
DARK = "#5A5A5E"
LINE = "#2A2A2E"
FOOT = "#6E6E72"

ORDER = [
    "W01-L01", "W01-L02", "W01-L03", "W02-L01", "W02-L02", "W02-L03",
    "W03-L01", "W03-L02", "W03-L03", "W04-L01", "W04-L02", "W04-L03",
    "W05-L01", "W05-L02", "W05-L03", "W06-L01", "W06-L02", "W06-L03",
]
WEEKS = {1: "Claim the Throne", 2: "Build the Fortress", 3: "Enter the Laboratory",
         4: "Command the Room", 5: "Build the Empire", 6: "Become Dangerous"}
PRINCIPLES = {
    1: "Put yourself above all people", 2: "Accept that there is no inherent meaning",
    3: "Develop your killer instinct", 4: "Hold a vision and be ruthless",
    5: "Build your empire", 6: "Believe in your fucking self", 7: "Vow to become a master",
    8: "Burn the bridge of permission", 9: "Radical accountability is absolute power",
    10: "Manipulate chaos into currency", 11: "Master the art of the tactical withdrawal",
    12: "Treat your body as the ultimate weapon", 13: "Despise comfort and seek the friction",
    14: "Embrace your finite nature",
}
TOOLS = {1: "Opportunity cost", 2: "Control and influence", 3: "First principles",
         4: "Inversion", 5: "Incentives", 6: "Second-order consequences", 7: "Leverage",
         8: "Feedback loops", 9: "Probabilistic thinking", 10: "Margin of safety"}
NUMWORDS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7,
            "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13,
            "fourteen": 14}
ORDINAL_TOOL = {"first": 1, "second": 2, "third": 3, "fourth": 4, "fifth": 5, "sixth": 6,
                "seventh": 7, "eighth": 8, "ninth": 9, "tenth": 10}

PROPER = """Daniel Amara Nadia Ama Lewis Ravi Grace Jun Marcus Lucia Andre Tom Zara Omar Ben Mei
Tunde Winston Chloe Diego Ella Claire Rhys Priya Jamal Sam Aisha Kofi Leah Paul Ngozi Arif Kieran
Sophie Doom Doomsday Doombot Doombots Council Monday Tuesday Wednesday Thursday Friday Saturday
Sunday January February March April June July October December GCSE GCSEs I I'm I'll I'd CEO AI
A4 A3 Vietnamese West African""".split()
PROPER_MAP = {w.lower(): w for w in PROPER}


# ---------------------------------------------------------------- parsing

def parse_lesson(lid):
    text = open(os.path.join(LESSONS, lid + ".md"), encoding="utf-8").read()
    head, rest = text.split("\n---\n", 1)
    body = rest.split("\n---\n")[0]
    meta = {"id": lid}
    m = re.search(r"^# (W\d\d-L\d\d): (.+)$", head, re.M)
    meta["title"] = m.group(2).strip()
    m = re.search(r"Video (\d+) of 18 • Week (\d): (.+?) •", head)
    meta["video"], meta["week"], meta["theme"] = int(m.group(1)), int(m.group(2)), m.group(3)
    for key in ["Principles", "Model", "Leads to", "Evidence", "Lead case", "Second case",
                "Hooded figure"]:
        m = re.search(r"\*\*" + re.escape(key) + r":\*\* (.+)", head)
        meta[key.lower().replace(" ", "_")] = m.group(1).strip() if m else ""
    meta["principle_nums"] = [int(x) for x in re.findall(r"P(\d\d)", meta["principles"])]
    meta["new_tool"] = None
    m = re.search(r"M(\d\d) [^;(]+\(new\)", meta["model"])
    if m:
        meta["new_tool"] = int(m.group(1))
    m = re.search(r"(W0\d-D0\d) \(Day (\d+)\)", meta["leads_to"])
    meta["workbook"], meta["day"] = (m.group(1), int(m.group(2))) if m else ("", 0)

    slides = []
    for block in re.split(r"\n(?=## Slide \d+ \| )", "\n" + body):
        block = block.strip()
        if not block.startswith("## Slide"):
            continue
        m = re.match(r"## Slide (\d+) \| (\w+)", block)
        s = {"n": int(m.group(1)), "kind": m.group(2)}
        mo = re.search(r"\*\*On screen:\*\* (.+)", block)
        s["onscreen"] = mo.group(1).strip() if mo else ""
        mv = re.search(r"\*\*Visual:\*\* (.+)", block)
        s["visual"] = mv.group(1).strip() if mv else ""
        ms = re.search(r"\*\*Say:\*\*\n(.*)", block, re.S)
        say = ms.group(1).strip() if ms else ""
        s["paras"] = [p.strip() for p in say.split("\n\n") if p.strip()]
        slides.append(s)
    return meta, slides


# ---------------------------------------------------------------- text helpers

def typo(t):
    """Typographic apostrophes and quotes."""
    t = re.sub(r'"([^"]*)"', "“\\1”", t)
    t = re.sub(r"(\w)'(\w)", "\\1’\\2", t)
    t = re.sub(r"(\w)'", "\\1’", t)
    t = re.sub(r"'(\w)", "‘\\1", t)
    return t


def esc(t):
    return html.escape(typo(t), quote=False)


def is_caps(t):
    letters = [c for c in t if c.isalpha()]
    return letters and sum(c.isupper() for c in letters) / len(letters) > 0.8


def sentence_case(t):
    if not is_caps(t):
        return t
    low = t.lower()
    out, cap_next = [], True
    for ch in low:
        if cap_next and ch.isalpha():
            out.append(ch.upper())
            cap_next = False
        else:
            out.append(ch)
        if ch in ".?!":
            cap_next = True
    s = "".join(out)

    def fix(mo):
        w = mo.group(0)
        key = w.lower()
        if key in PROPER_MAP:
            return PROPER_MAP[key]
        return w
    s = re.sub(r"[A-Za-z][A-Za-z']*", fix, s)
    s = re.sub(r"\b(w0\d-d0\d)\b", lambda mo: mo.group(1).upper(), s, flags=re.I)
    return s


def red_stops(t, last_line_red=False):
    """Escape and colour terminal punctuation red."""
    sentences = re.findall(r"[^.?!]+[.?!]+|[^.?!]+$", t)
    parts = []
    for i, snt in enumerate(sentences):
        snt = snt.strip()
        mm = re.match(r"^(.*?)([.?!]+)$", snt)
        if last_line_red and i == len(sentences) - 1:
            parts.append(f'<span style="color:{RED}">{esc(snt)}</span>')
        elif mm:
            parts.append(f'{esc(mm.group(1))}<span style="color:{RED}">{esc(mm.group(2))}</span>')
        else:
            parts.append(esc(snt))
    return parts


def headline(t, stack_ok=True):
    """Return (html, length) for a headline; stacks 2 to 4 short sentences."""
    t = sentence_case(t)
    sentences = [x.strip() for x in re.findall(r"[^.?!]+[.?!]+|[^.?!]+$", t) if x.strip()]
    if stack_ok and 2 <= len(sentences) <= 4 and all(len(x.split()) <= 4 for x in sentences):
        parts = red_stops(t, last_line_red=len(sentences) >= 3)
        return "<br>".join(parts), max(len(x) for x in sentences), len(sentences)
    return " ".join(red_stops(t)), len(t), 1


def head_size(length, lines, width):
    """Pick a headline size from the deck's type scale so it fits the column."""
    for size in (120, 102, 88, 72, 64):
        per_line = width / (size * 0.46)
        est_lines = max(lines, -(-length // max(1, int(per_line)))) if lines == 1 else lines
        if lines == 1:
            est_lines = -(-length // max(1, int(per_line)))
        if est_lines * size * 1.08 <= 560 and (lines == 1 or length <= per_line):
            if lines == 1 and est_lines > 4:
                continue
            return size
    return 56


def sentences_of(p):
    return [x.strip() for x in re.findall(r"[^.?!]+[.?!]+[”\"]?|[^.?!]+$", p) if x.strip()]


def short_body(rest, cap=150):
    ss = sentences_of(rest)
    if not ss:
        return ""
    out = ss[0]
    if (len(out) < 55 and len(ss) > 1 and len(out) + len(ss[1]) < cap
            and len(ss[1].split()) >= 4):
        out += " " + ss[1]
    return out


def term_items(paras, max_items=5, max_words=6):
    items = []
    for p in paras:
        p2 = re.sub(r"^(And|But|Then) (the |a )?", lambda m: (m.group(2) or "").capitalize(), p)
        p2 = p2[0].upper() + p2[1:] if p2 else p2
        mm = re.match(r"^([^.?!:]{1,48}?)([.?!:]) (.+)$", p2, re.S)
        if not mm:
            continue
        term, rest = mm.group(1).strip(), mm.group(3).strip()
        if mm.group(2) == "?":
            term += "?"
        if len(term.split()) > max_words or term.lower().startswith(("here is", "that is", "this is", "so ", "notice", "look at", "most ")):
            continue
        items.append([term, short_body(rest)])
        if len(items) >= max_items:
            break
    return items


def step_items(paras):
    items = []
    for p in paras:
        mm = re.match(r"^(One|Two|Three|Four|Five)\. (.+)$", p, re.S)
        if mm:
            items.append(short_body(mm.group(2), cap=120))
    return items


def minutes_label(paras):
    joined = " ".join(paras)
    mm = re.search(r"(?:give it|Take|write them\.) (\w+) minutes", joined) or re.search(r"(\w+) minutes", joined)
    return (mm.group(1).lower() + " minutes") if mm else "five minutes"


# ---------------------------------------------------------------- slide furniture

def section(sid, inner, bg=BG, justify="center", align=None, gap=32, notes="", pad="144px 128px",
            extra=""):
    a = f"align-items:{align};" if align else ""
    style = (f"background:{bg};color:{WHITE};font-family:{FONT};padding:{pad};display:flex;"
             f"flex-direction:column;justify-content:{justify};{a}gap:{gap}px{extra}")
    notes_html = f"\n<aside>{html.escape(typo(notes), quote=False)[:3990]}</aside>" if notes else ""
    return f'<section id="{sid}" data-transition="fade" style="{style}">\n{inner}{notes_html}\n</section>\n'


def footer(meta, n, on_image=False):
    col = GREY if on_image else FOOT
    w, l = meta["week"], int(meta["id"][-2:])
    return (f'<p style="position:absolute;left:128px;bottom:64px;width:1100px;font-size:24px;color:{col}">'
            f'Week {w} / Lesson {l:02d} / {esc(meta["title"])}</p>\n'
            f'<p style="position:absolute;right:128px;bottom:64px;width:200px;text-align:right;font-size:24px;color:{RED}">{n:02d}</p>\n')


def image_layer(img, alt, scrim="left", tag_top=64):
    src = f' src="{img}"' if img else ""
    scrims = {
        "left": "linear-gradient(90deg, rgba(5,5,5,0.94) 0%, rgba(5,5,5,0.72) 38%, rgba(5,5,5,0.08) 70%)",
        "full": "radial-gradient(ellipse at 50% 45%, rgba(5,5,5,0.55) 0%, rgba(5,5,5,0.88) 100%)",
        "right": "linear-gradient(270deg, rgba(5,5,5,0.92) 0%, rgba(5,5,5,0.6) 40%, rgba(5,5,5,0) 70%)",
    }
    out = (f'<img{src} alt="{html.escape(alt)}" style="position:absolute;left:0px;top:0px;width:1920px;'
           f'height:1080px;object-fit:cover;background:#121214">\n'
           f'<div style="position:absolute;left:0px;top:0px;width:1920px;height:1080px;background:{scrims[scrim]}"></div>\n')
    if not img:
        out += (f'<p style="position:absolute;right:128px;top:{tag_top}px;width:600px;text-align:right;font-size:24px;'
                f'font-weight:600;letter-spacing:4px;text-transform:uppercase;color:{DARK}">Image to come</p>\n')
    return out


def logo_box(pinned=True):
    if pinned:
        return (f'<p style="position:absolute;left:1592px;top:64px;width:200px;padding:10px 0px;text-align:center;'
                f'font-size:24px;font-weight:600;letter-spacing:6px;color:{DARK};border:1px dashed {DARK}">LOGO</p>\n')
    return (f'<p style="width:240px;padding:12px 0px;text-align:center;font-size:24px;font-weight:600;'
            f'letter-spacing:6px;color:{DARK};border:1px dashed {DARK}">LOGO</p>\n')


def eyebrow(text, on_image=False, width=None):
    w = f"width:{width}px;" if width else ""
    return (f'<p style="{w}font-size:24px;color:{GREY}"><span style="color:{RED}">—</span>  {esc(text)}</p>\n')


def h(tag, inner, size, width=None, align=None, color=None, lh=1.05):
    w = f"width:{width}px;" if width else ""
    a = f"text-align:{align};" if align else ""
    c = f"color:{color};" if color else ""
    ls = -3 if size >= 80 else -2
    return (f'<{tag} style="{w}{a}{c}font-family:{FONT};font-size:{size}px;font-weight:500;'
            f'line-height:{lh};letter-spacing:{ls}px">{inner}</{tag}>\n')


def para(text, size=28, color=GREY, width=None, align=None, raw=False):
    w = f"width:{width}px;" if width else ""
    a = f"text-align:{align};" if align else ""
    t = text if raw else esc(text)
    return f'<p style="{w}{a}font-size:{size}px;line-height:1.4;color:{color}">{t}</p>\n'


# ---------------------------------------------------------------- slide builders

def notes_for(s, brief=None):
    n = "\n\n".join(s["paras"])
    if brief:
        n += f"\n\n[Image: {brief}]"
    return n


def brief_of(s, meta):
    v = s["visual"]
    if not v:
        return ""
    if v.startswith("hood"):
        return f"title image: the hooded figure, {meta['hooded_figure']}"
    if v.startswith("close"):
        return "end card: " + re.sub(r"^close \((.*)\)$", r"\1", v)
    v = re.sub(r"^scene[: ]*\(?", "", v).rstrip(")")
    return v


def case_label(s, meta):
    """Name and role when a cast member is in the visual or the narration."""
    cast = {}
    for key in ("lead_case", "second_case"):
        val = meta[key]
        name = val.split(",")[0].strip()
        role = ""
        parts = [p.strip() for p in val.split(",")]
        for p in parts[1:]:
            if not re.search(r"\b(man|woman|early|mid|late|beard|hair|stubble|head|athletic)\b", p) and "(" not in p:
                role = p
                break
        cast[name] = role
    hay = s["visual"] + " " + " ".join(s["paras"][:2])
    for name, role in cast.items():
        if re.search(r"\b" + re.escape(name) + r"\b", hay):
            return name + (f" / {role}" if role else "")
    return ""


def b_title(meta, s, sid, img):
    title = sentence_case(s["onscreen"])
    head_html, length, lines = headline(meta["title"], stack_ok=False)
    size = 120 if len(meta["title"]) <= 24 else (102 if len(meta["title"]) <= 32 else 88)
    pr = " / ".join(f"Principle {p:02d}" for p in meta["principle_nums"][:1])
    sub = PRINCIPLES[meta["principle_nums"][0]] if meta["principle_nums"] else ""
    tool = f"Thinking tool {meta['new_tool']:02d} / {TOOLS[meta['new_tool']]}" if meta["new_tool"] else ""
    inner = image_layer(img, brief_of(s, meta) or "The hooded figure", tag_top=140)
    inner += logo_box()
    inner += eyebrow(f"Week {meta['week']} / {meta['theme']} / Lesson {int(meta['id'][-2:]):02d}")
    inner += h("h1", head_html + ("" if head_html.endswith("</span>") else f'<span style="color:{RED}">.</span>'), size, width=980)
    lines_sub = []
    if sub:
        lines_sub.append(f'<span style="color:{WHITE}">{pr}</span>  {esc(sub)}')
    if tool:
        lines_sub.append(f'<span style="color:{WHITE}">{esc(tool.split(" / ")[0])}</span>  {esc(tool.split(" / ")[1])}')
    inner += para("<br>".join(lines_sub), size=26, color=GREY, width=900, raw=True)
    inner += footer(meta, s["n"], on_image=True)
    return section(sid, inner, bg=BG_IMG, gap=28, notes=notes_for(s, brief_of(s, meta)))


def b_scene(meta, s, sid, img, label=None):
    hh, length, lines = headline(s["onscreen"])
    size = head_size(length, lines, 960)
    lab = label if label is not None else case_label(s, meta)
    inner = image_layer(img, brief_of(s, meta) or s["onscreen"])
    if lab:
        inner += eyebrow(lab)
    inner += h("h1", hh, size, width=1000)
    inner += footer(meta, s["n"], on_image=True)
    return section(sid, inner, bg=BG_IMG, gap=28, notes=notes_for(s, brief_of(s, meta)))


def b_question(meta, s, sid):
    q = sentence_case(s["onscreen"])
    words = q.split(" ")
    last = words[-1]
    body = esc(" ".join(words[:-1]))
    hh = f'{body} <span style="color:{RED}">{esc(last)}</span>'
    size = 120 if len(q) <= 28 else (102 if len(q) <= 50 else 88)
    inner = h("h1", hh, size, width=1500, align="center", lh=1.08)
    inner += footer(meta, s["n"])
    return section(sid, inner, align="center", gap=40, notes=notes_for(s))


def principle_for(s, meta):
    on = s["onscreen"].rstrip(".").lower()
    for n, name in PRINCIPLES.items():
        if on == name.lower() or on == name.lower().replace(" and ", ". "):
            return n
    joined = " ".join(s["paras"][:2])
    mm = re.search(r"[Pp]rinciple (\w+)", joined)
    if mm and mm.group(1).lower() in NUMWORDS:
        return NUMWORDS[mm.group(1).lower()]
    return None


def b_red(meta, s, sid):
    text = sentence_case(s["onscreen"])
    joined = " ".join(s["paras"][:2])
    label = ""
    mt = re.search(r"The (\w+)(?: and final)? thinking tool", joined)
    if mt and mt.group(1).lower() in ORDINAL_TOOL:
        n = ORDINAL_TOOL[mt.group(1).lower()]
        label = f"Thinking tool {n:02d} / {TOOLS[n]}"
    elif "first of the ten thinking tools" in joined:
        label = f"Thinking tool 01 / {TOOLS[1]}"
    else:
        p = principle_for(s, meta)
        if p:
            label = f"Principle {p:02d}" + ("" if text.rstrip(".").lower() == PRINCIPLES[p].lower() else f" / {PRINCIPLES[p]}")
    size = 120 if len(text) <= 26 else (102 if len(text) <= 48 else (88 if len(text) <= 70 else 72))
    words = esc(text)
    # last word in bone on the red panel
    mm = re.match(r"^(.*\s)(\S+)$", words)
    hh = (f'{mm.group(1)}<span style="color:#F2F2F2">{mm.group(2)}</span>' if mm else words)
    inner = ""
    if label:
        inner += f'<p style="font-size:24px;font-weight:600;letter-spacing:4px;text-transform:uppercase;color:#0A0A0A">{esc(label)}</p>\n'
    inner += h("h1", hh, size, width=1500, color="#0A0A0A")
    w, l = meta["week"], int(meta["id"][-2:])
    inner += (f'<p style="position:absolute;left:128px;bottom:64px;width:1100px;font-size:24px;color:#0A0A0A">'
              f'Week {w} / Lesson {l:02d} / {esc(meta["title"])}</p>\n'
              f'<p style="position:absolute;right:128px;bottom:64px;width:200px;text-align:right;font-size:24px;color:#F2F2F2">{s["n"]:02d}</p>\n')
    return section(sid, inner, bg=RED, gap=28, notes=notes_for(s))


def rows_html(items, numbered=True, highlight_last=False, term_size=40, width=None):
    out = []
    for i, it in enumerate(items):
        term, body = (it if isinstance(it, (list, tuple)) else (it, ""))
        tcol = RED if (highlight_last and i == len(items) - 1) else WHITE
        num = f'<p style="width:60px;font-size:24px;color:{RED}">{i+1:02d}</p>' if numbered else ""
        b = f'<p style="font-size:24px;line-height:1.4;color:{DIM}">{esc(body)}</p>' if body else ""
        out.append(
            f'<div style="display:flex;flex-direction:row;gap:36px;padding:24px 0px;border-top:1px solid {LINE}">{num}'
            f'<div style="flex:1;display:flex;flex-direction:column;gap:6px">'
            f'<h3 style="font-family:{FONT};font-size:{term_size}px;font-weight:500;line-height:1.1;letter-spacing:-1px;color:{tcol}">{esc(term)}</h3>{b}</div></div>')
    w = f"width:{width}px;" if width else ""
    return f'<div style="{w}display:flex;flex-direction:column">' + "".join(out) + "</div>\n"


def b_list(meta, s, sid, items, label=None):
    hh, length, lines = headline(s["onscreen"], stack_ok=True)
    size = 88 if length <= 22 else (72 if length <= 44 else 64)
    left = '<div style="width:620px;display:flex;flex-direction:column;gap:24px">'
    if label:
        left += eyebrow(label)
    left += h("h2", hh, size, width=620) + "</div>"
    term_size = 40 if len(items) <= 3 else 34
    right = rows_html(items, term_size=term_size, highlight_last=len(items) == 3, width=920)
    inner = (f'<div style="display:flex;flex-direction:row;gap:124px;align-items:center">{left}{right}</div>\n')
    inner += footer(meta, s["n"])
    return section(sid, inner, notes=notes_for(s))


def b_compare(meta, s, sid, items):
    cols = []
    for i, (term, body) in enumerate(items[:3]):
        win = i == len(items[:3]) - 1
        rule = RED if win else LINE
        tcol = WHITE if win else "#6A6A6E"
        bcol = SOFT if win else DIM
        stop = f'<span style="color:{RED}">.</span>' if win else "."
        cols.append(
            f'<div style="display:flex;flex-direction:column;gap:18px;border-top:2px solid {rule};padding:32px 0px 0px 0px">'
            f'<p style="font-size:24px;color:{RED if win else DIM}">{i+1:02d}</p>'
            f'<h2 style="font-family:{FONT};font-size:56px;font-weight:500;line-height:1.05;letter-spacing:-2px;color:{tcol}">{esc(term)}{stop}</h2>'
            f'<p style="font-size:26px;line-height:1.4;color:{bcol}">{esc(body)}</p></div>')
    inner = eyebrow(sentence_case(s["onscreen"]))
    inner += f'<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:64px">{"".join(cols)}</div>\n'
    inner += footer(meta, s["n"])
    return section(sid, inner, gap=56, notes=notes_for(s))


def b_story(meta, s, sid, sub=None):
    hh, length, lines = headline(s["onscreen"], stack_ok=False)
    size = 102 if length <= 40 else (88 if length <= 70 else 72)
    lab = case_label(s, meta)
    inner = ""
    if lab:
        inner += eyebrow(lab)
    inner += h("h1", hh, size, width=1400)
    if sub:
        inner += para(sub, size=30, color=GREY, width=1100)
    inner += footer(meta, s["n"])
    return section(sid, inner, gap=32, notes=notes_for(s))


def b_steps(meta, s, sid, items):
    hh, length, lines = headline(s["onscreen"], stack_ok=False)
    size = 102 if length <= 30 else 88
    cells = []
    for i, t in enumerate(items[:4]):
        cells.append(
            f'<div style="display:flex;flex-direction:row;gap:32px;padding:26px 0px;border-top:1px solid {LINE}">'
            f'<p style="width:50px;font-size:24px;color:{RED}">{i+1:02d}</p>'
            f'<p style="flex:1;font-size:30px;line-height:1.35;color:{WHITE}">{esc(t)}</p></div>')
    inner = (f'<div style="display:flex;flex-direction:column;gap:20px">'
             + eyebrow(f"Pause the video / {minutes_label(s['paras'])}")
             + h("h1", hh, size) + "</div>\n")
    inner += f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:0px 90px">{"".join(cells)}</div>\n'
    inner += footer(meta, s["n"])
    return section(sid, inner, gap=48, notes=notes_for(s))


def mission_rows(meta, s):
    paras = s["paras"]
    focus = ""
    mm = re.search(r"W0\d-D0\d, ([^.]+)\.", paras[0]) if paras else None
    if mm:
        focus = mm.group(1).strip()
    do = ""
    for p in paras[1:]:
        if not p.lower().startswith(("that is your evidence", "nobody")):
            do = short_body(p, cap=150)
            break
    rows = [("Workbook", f"{meta['workbook']} / Day {meta['day']}" + (f" / {focus[0].upper() + focus[1:]}" if focus else "")),
            ("Do", do), ("Evidence", meta["evidence"])]
    return [r for r in rows if r[1]]


def b_mission(meta, s, sid, img, with_image):
    rows = mission_rows(meta, s)
    row_html = "".join(
        f'<div style="display:flex;flex-direction:row;gap:36px;padding:24px 0px;border-top:1px solid {LINE}">'
        f'<p style="width:170px;font-size:24px;font-weight:600;letter-spacing:2px;text-transform:uppercase;color:{RED}">{esc(k)}</p>'
        f'<p style="flex:1;font-size:28px;line-height:1.35;color:{WHITE}">{esc(v)}</p></div>' for k, v in rows)
    title = f'Today’s<br><span style="color:{RED}">mission.</span>'
    if with_image:
        src = f' src="{img}"' if img else ""
        inner = (f'<img{src} alt="{html.escape(brief_of(s, meta) or "Mission image")}" style="position:absolute;left:1160px;top:0px;'
                 f'width:760px;height:1080px;object-fit:cover;background:#121214">\n'
                 f'<div style="position:absolute;left:1160px;top:0px;width:760px;height:1080px;background:linear-gradient(90deg, rgba(11,11,12,1) 0%, rgba(11,11,12,0) 30%)"></div>\n')
        if not img:
            inner += (f'<p style="position:absolute;right:128px;top:64px;width:500px;text-align:right;font-size:24px;'
                      f'font-weight:600;letter-spacing:4px;text-transform:uppercase;color:{DARK}">Image to come</p>\n')
        inner += (f'<div style="width:940px;display:flex;flex-direction:column;gap:44px">'
                  f'{h("h1", title, 102, lh=1.02)}'
                  f'<div style="display:flex;flex-direction:column">{row_html}</div></div>\n')
    else:
        inner = (f'<div style="display:flex;flex-direction:row;gap:100px;align-items:center">'
                 f'<div style="width:560px">{h("h1", title, 102, lh=1.02)}</div>'
                 f'<div style="flex:1;display:flex;flex-direction:column">{row_html}</div></div>\n')
    inner += footer(meta, s["n"], on_image=False)
    return section(sid, inner, gap=40, notes=notes_for(s, brief_of(s, meta) if with_image else None))


def next_line(meta):
    i = ORDER.index(meta["id"])
    if i == len(ORDER) - 1:
        return "Next / Doomsday"
    nid = ORDER[i + 1]
    nmeta, _ = parse_lesson(nid)
    if nmeta["week"] != meta["week"]:
        return f"Next / Week {nmeta['week']} / {nmeta['theme']} / {nmeta['title']}"
    return f"Next / Lesson {int(nid[-2:]):02d} / {nmeta['title']}"


def b_close(meta, s, sid):
    hh, length, lines = headline(s["onscreen"])
    size = head_size(length, lines, 1400)
    inner = h("h1", hh, size, width=1400)
    inner += f'<p style="font-size:26px;color:{GREY}">{esc(next_line(meta))}</p>\n'
    inner += footer(meta, s["n"])
    return section(sid, inner, gap=40, notes=notes_for(s))


def b_endcard(meta, s, sid, img, next_text=None):
    t = sentence_case(s["onscreen"])
    hh = " ".join(red_stops(t))
    inner = image_layer(img, brief_of(s, meta) or "The hooded figure", scrim="full")
    inner += h("h1", hh, 120 if len(t) <= 24 else 102, width=1500, align="center")
    inner += f'<div style="width:200px;height:3px;background:{RED}"></div>\n'
    if next_text:
        inner += f'<p style="font-size:26px;text-align:center;color:{GREY}">{esc(next_text)}</p>\n'
    inner += logo_box(pinned=False)
    inner += footer(meta, s["n"], on_image=True)
    return section(sid, inner, bg=BG_IMG, align="center", gap=36, notes=notes_for(s, brief_of(s, meta)))


def b_image_statement(meta, s, sid, img):
    return b_scene(meta, s, sid, img, label="The Doom lens")


def b_poster(meta, s, sid, img, sub=None):
    hh, length, lines = headline(s["onscreen"])
    size = head_size(length, lines, 1100)
    inner = image_layer(img, brief_of(s, meta) or s["onscreen"])
    inner += h("h1", hh, size, width=1100)
    inner += f'<div style="width:180px;height:3px;background:{RED}"></div>\n'
    if sub:
        inner += para(sub, size=28, color="#B4B4B8", width=760)
    inner += footer(meta, s["n"], on_image=True)
    return section(sid, inner, bg=BG_IMG, gap=32, notes=notes_for(s, brief_of(s, meta)))


def b_themes(meta, s, sid, items):
    hh, _, _ = headline(s["onscreen"])
    cols = "".join(
        f'<div style="display:flex;flex-direction:column;gap:14px;border-top:{"2px solid " + RED if i == len(items) - 1 else "1px solid " + LINE};padding:30px 0px 0px 0px">'
        f'<h3 style="font-family:{FONT};font-size:44px;font-weight:600;letter-spacing:2px;text-transform:uppercase;color:{RED if i == len(items) - 1 else WHITE}">{esc(t)}</h3>'
        f'<p style="font-size:26px;line-height:1.4;color:{GREY}">{esc(b)}</p></div>'
        for i, (t, b) in enumerate(items))
    inner = eyebrow("Three voices")
    inner += h("h1", hh, 88)
    inner += f'<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:64px">{cols}</div>\n'
    inner += footer(meta, s["n"])
    return section(sid, inner, gap=48, notes=notes_for(s))


def b_radial(meta, s, sid, title, sub):
    words = [w.strip(" .") for w in s["onscreen"].split(".") if w.strip(" .")]
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 1080" style="position:absolute;left:880px;top:0px;width:1000px;height:1080px">'
           '<circle cx="500" cy="540" r="150" fill="none" stroke="#FF5A46" stroke-opacity="0.45" stroke-width="2"/>'
           '<circle cx="500" cy="540" r="300" fill="none" stroke="#FF5A46" stroke-opacity="0.25" stroke-width="2"/>'
           '<circle cx="500" cy="540" r="450" fill="none" stroke="#FF5A46" stroke-opacity="0.12" stroke-width="2"/></svg>\n')
    inner = (f'<div style="position:absolute;left:880px;top:0px;width:1000px;height:1080px;'
             f'background:radial-gradient(circle, rgba(160,14,10,0.5) 0%, rgba(11,11,12,0) 62%)"></div>\n' + svg)
    pos = [(1380 - 120, 510, 240, "#78140E", "#FF7864", 30), (1380 - 110, 510 - 300, 220, "#3C0C09", "#A0302A", 26),
           (1380 + 260, 510 + 330, 220, "#3C0C09", "#A0302A", 26)]
    for (x, y, w, bg, bd, fs), word in zip(pos, words):
        inner += (f'<p style="position:absolute;left:{x}px;top:{y}px;width:{w}px;padding:12px 20px;text-align:center;'
                  f'font-size:{fs}px;color:{WHITE};background:{bg};border:1px solid {bd};border-radius:40px">{esc(word)}</p>\n')
    inner += h("h2", title, 80, width=700)
    inner += para(sub, size=26, color=DIM, width=640)
    inner += footer(meta, s["n"])
    return section(sid, inner, gap=32, notes=notes_for(s))


def b_recap(meta, s, sid, items):
    hh, _, _ = headline(s["onscreen"], stack_ok=False)
    left = '<div style="width:560px;display:flex;flex-direction:column;gap:24px">' + eyebrow("Three things to keep") + h("h2", hh, 88, width=560) + "</div>"
    right = rows_html([(t, "") for t in items], term_size=36, width=1000)
    inner = f'<div style="display:flex;flex-direction:row;gap:104px;align-items:center">{left}{right}</div>\n'
    inner += footer(meta, s["n"])
    return section(sid, inner, notes=notes_for(s))


# ---------------------------------------------------------------- deck assembly

def load_overrides():
    if os.path.exists(OVERRIDES):
        return json.load(open(OVERRIDES, encoding="utf-8"))
    return {}


def plan_slide(meta, s, ov):
    """Decide the builder and its content; returns (builder_name, data)."""
    key = f"{meta['id']}:{s['n']}"
    o = ov.get(key, {})
    k = s["kind"]
    if k == "list":
        items = o.get("items") or term_items(s["paras"])
        return "list", {"items": items, "label": o.get("label")}
    if k == "compare":
        items = o.get("items") or term_items(s["paras"], max_items=3)
        return "compare", {"items": items}
    if k == "steps":
        return "steps", {"items": o.get("items") or step_items(s["paras"])}
    if k == "recap":
        return "recap", {"items": o.get("items")}
    if k == "dossier":
        return "themes", {"items": o.get("items")}
    if k == "radial":
        return "radial", {"title": o.get("title", ""), "sub": o.get("sub", "")}
    if k == "story":
        return "story", {"sub": o.get("sub")}
    if k == "poster":
        return "poster", {"sub": o.get("sub")}
    return k, {}


def build(lid, out_root, images=None):
    meta, slides = parse_lesson(lid)
    ov = load_overrides()
    images = images or {}
    os.makedirs(os.path.join(out_root, "project", "slides"), exist_ok=True)
    order = []
    for s in slides:
        sid = f"s{s['n']:02d}"
        order.append(sid)
        img = images.get(str(s["n"]))
        kind, d = plan_slide(meta, s, ov)
        even = s["n"] % 2 == 0
        if kind == "title":
            out = b_title(meta, s, sid, img)
        elif kind == "question":
            out = b_question(meta, s, sid)
        elif kind == "red":
            out = b_red(meta, s, sid)
        elif kind == "list":
            out = b_list(meta, s, sid, d["items"], d.get("label"))
        elif kind == "compare":
            out = b_compare(meta, s, sid, d["items"])
        elif kind == "steps":
            out = b_steps(meta, s, sid, d["items"])
        elif kind == "recap":
            out = b_recap(meta, s, sid, d["items"])
        elif kind == "themes":
            out = b_themes(meta, s, sid, d["items"])
        elif kind == "radial":
            out = b_radial(meta, s, sid, d["title"], d["sub"])
        elif kind == "story":
            out = b_story(meta, s, sid, d.get("sub"))
        elif kind == "poster":
            out = b_poster(meta, s, sid, img, d.get("sub"))
        elif kind == "mission" or (kind == "scene" and s["onscreen"].startswith("Today's mission")):
            out = b_mission(meta, s, sid, img, with_image=even or bool(s["visual"]))
        elif kind == "close" and even and s["visual"]:
            out = b_endcard(meta, s, sid, img, next_text=next_line(meta))
        elif kind == "close":
            out = b_close(meta, s, sid)
        elif kind == "image" and s["n"] == len(slides):
            out = b_endcard(meta, s, sid, img)
        elif kind == "image":
            out = b_image_statement(meta, s, sid, img)
        elif kind == "scene":
            out = b_scene(meta, s, sid, img)
        else:
            raise SystemExit(f"unknown kind {kind} in {lid} slide {s['n']}")
        open(os.path.join(out_root, "project", "slides", sid + ".html"), "w", encoding="utf-8").write(out)
    deck = {
        "v": 4,
        "createdOnFiles": {"v": 1, "at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")},
        "lists": "css",
        "title": f"Becoming Doom {lid}: {meta['title']}",
        "cover": order[0],
        "order": order,
        "sections": section_map(slides, order),
        "faces": {"inter-tight": {"family": "Inter Tight",
                                  "href": "https://fonts.googleapis.com/css2?family=Inter+Tight:wght@300..700&display=swap"}},
        "designSystems": [],
    }
    json.dump(deck, open(os.path.join(out_root, "project", "deck.json"), "w", encoding="utf-8"), ensure_ascii=False)
    return meta, order


def section_map(slides, order):
    """Outline: open, idea, case, mistakes, practice."""
    secs = {"s1": {"description": "Open: the hook and the question", "start": order[0]}}
    kinds = [s["kind"] for s in slides]
    idx = {}
    for i, s in enumerate(slides):
        if s["kind"] == "red" and "idea" not in idx:
            idx["idea"] = i
        if s["kind"] == "compare" and "case" not in idx:
            idx["case"] = i - 1 if i > 0 else i
        if s["kind"] == "steps" and "practice" not in idx:
            idx["practice"] = i
    if "idea" in idx:
        secs["s2"] = {"description": "The principle and the thinking tool", "start": order[idx["idea"]]}
    if "case" in idx and idx["case"] > idx.get("idea", 0):
        secs["s3"] = {"description": "The cases", "start": order[idx["case"]]}
    if "practice" in idx:
        secs["s4"] = {"description": "Practice, mission and close", "start": order[idx["practice"]]}
    return secs


def dump():
    ov = load_overrides()
    for lid in ORDER:
        meta, slides = parse_lesson(lid)
        for s in slides:
            kind, d = plan_slide(meta, s, ov)
            if kind in ("list", "compare", "steps", "recap", "themes", "radial"):
                src = "OV" if f"{lid}:{s['n']}" in ov else "auto"
                print(f"{lid}:{s['n']} {kind} [{src}] {s['onscreen']}")
                for it in d.get("items") or []:
                    print("     -", it)


if __name__ == "__main__":
    if sys.argv[1] == "--dump":
        dump()
    else:
        imgs = None
        if "--images" in sys.argv:
            imgs = json.load(open(sys.argv[sys.argv.index("--images") + 1]))
        m, o = build(sys.argv[1], sys.argv[2], imgs)
        print(m["id"], len(o), "slides")
