"""Slide-ready variants of the Gephi renders: Gephi PNG + legend panel + one-line caption (Pillow).

The network drawing is pasted unchanged (only scaled to fit); this script adds the legend and caption only.
Writes figures/<name>_slide.png at 3840x2160 (16:9).

Usage: python make_slides.py   (run from anywhere; paths are relative to this file)
Needs: Pillow (system Pillow 11.3.0 is fine).
"""
import csv
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
GEPHI = HERE.parent
FIG = GEPHI / "figures"
STATS = GEPHI / "stats"
W, H = 3840, 2160
PANEL_W = 1080
CAPTION_H = 230


def font(size, bold=False):
    names = (["Arial Bold.ttf", "Helvetica.ttc"] if bold else ["Arial.ttf", "Helvetica.ttc"])
    for n in names:
        for d in ("/System/Library/Fonts/Supplemental", "/System/Library/Fonts", "/Library/Fonts"):
            p = Path(d) / n
            if p.exists():
                return ImageFont.truetype(str(p), size)
    return ImageFont.load_default(size)


def top_classes(path, k=8):
    rows = list(csv.DictReader(open(path, encoding="utf-8")))
    return rows[:k]


def wrap(draw, text, f, width):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=f) <= width:
            cur = t
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def compose(src, out, title, items, caption, note=None):
    img = Image.open(FIG / src).convert("RGB")
    canvas = Image.new("RGB", (W, H), "white")
    box_w, box_h = W - PANEL_W - 60, H - CAPTION_H - 40
    scale = min(box_w / img.width, box_h / img.height)
    im = img.resize((int(img.width * scale), int(img.height * scale)), Image.LANCZOS)
    canvas.paste(im, (30 + (box_w - im.width) // 2, 20 + (box_h - im.height) // 2))
    d = ImageDraw.Draw(canvas)
    x0 = W - PANEL_W
    d.line([(x0 - 10, 60), (x0 - 10, H - CAPTION_H - 40)], fill="#DDDDDD", width=3)
    y = 90
    for line in wrap(d, title, font(56, True), PANEL_W - 80):
        d.text((x0 + 30, y), line, fill="#111111", font=font(56, True))
        y += 70
    y += 30
    for kind, colour, label in items:
        if kind == "dot":
            d.ellipse([x0 + 40, y + 6, x0 + 92, y + 58], fill=colour)
        elif kind == "line":
            w = label[1] if isinstance(label, tuple) else 14
            label = label[0] if isinstance(label, tuple) else label
            d.line([(x0 + 30, y + 32), (x0 + 110, y + 32)], fill=colour, width=w)
        elif kind == "head":
            d.text((x0 + 30, y + 10), label, fill="#333333", font=font(42, True))
            y += 70
            continue
        lines = wrap(d, label, font(42), PANEL_W - 190)
        for i, ln in enumerate(lines):
            d.text((x0 + 135, y + 8 + 50 * i), ln, fill="#222222", font=font(42))
        y += max(78, 50 * len(lines) + 28)
    if note:
        y += 20
        for ln in wrap(d, note, font(34), PANEL_W - 80):
            d.text((x0 + 30, y), ln, fill="#555555", font=font(34))
            y += 44
    d.rectangle([0, H - CAPTION_H, W, H], fill="#F4F4F4")
    cy = H - CAPTION_H + 30
    cap_lines = wrap(d, caption, font(44), W - 120)
    if len(cap_lines) > 3:
        print(f"WARNING: caption for {out} wraps to {len(cap_lines)} lines; only 3 fit")
    for ln in cap_lines[:3]:
        d.text((60, cy), ln, fill="#111111", font=font(44))
        cy += 58
    canvas.save(FIG / out, optimize=True)
    print(out, canvas.size)


def main():
    if (FIG / "type_network_lift.png").exists():
        compose("type_network_lift.png", "type_network_lift_slide.png",
                "Which replies follow which comments? (cscq)",
                [("dot", "#4D4D4D", "Comment kind (rule-based marker in the parent comment)"),
                 ("dot", "#009E73", "Reply kind (marker in the direct reply)"),
                 ("head", None, "Edge = lift vs unmarked comments"),
                 ("line", "#D55E00", ("lift >= 1.2 (reply kind clearly more common)", 16)),
                 ("line", "#8C8C8C", ("lift 1.0 to 1.2", 10)),
                 ("line", "#DADADA", ("lift < 1.0 (less common than baseline)", 8))],
                "Comment kind to reply kind in r/cscareerquestions (91,229 direct replies, Jan 2025 - Sep 2026). "
                "Edge thickness is proportional to lift; experience (own layoff story) to sympathy = 2.82x (5.11% vs 1.82%). "
                "Markers are rule-based and not yet human-checked. Gephi Toolkit 0.11.4 render.",
                "Lift = reply-kind share under this comment kind / share under unmarked comments. Edges into 'agree' are a marker artefact (the rule also fires on hostile 'This...' replies).")
    if (FIG / "r4_author_types.png").exists():
        compose("r4_author_types.png", "r4_author_types_slide.png",
                "Author types in the cscq reply network",
                [("dot", "#0072B2", "story-sharer (233)"), ("dot", "#D55E00", "blame-talker (577)"),
                 ("dot", "#009E73", "helper (1,770)"), ("dot", "#CC79A7", "other (8,198)")],
                "r/cscareerquestions reply network, Jan - Jun 2025: 10,778 profiled authors (>= 5 comments), 91,657 directed pairs. "
                "Colour = rule-based author type; size = Gephi PageRank. Typed authors are not at the edge or in separate regions; "
                "they sit slightly nearer the centre than other authors, probably because they are more active (N1, N4). "
                "ForceAtlas2; positions have no geographic or temporal meaning.",
                "Node size: 4 + 36 x sqrt(scaled PageRank). Edges at 6% opacity.")
    if (FIG / "r4_modularity.png").exists() and (STATS / "r4_modularity_group_sizes.csv").exists():
        rows = top_classes(STATS / "r4_modularity_group_sizes.csv")
        items = [("dot", r["hex"], f"class {r['modularity_class']}: {int(r['users']):,} ({float(r['share_pct']):.1f}%)") for r in rows]
        items.append(("dot", "#C8C8C8", f"all other {81 - len(rows)} classes (grey)"))
        compose("r4_modularity.png", "r4_modularity_slide.png", "Gephi Modularity groups (8 largest)", items,
                "Same cscq network and layout as the author-type figure; colour = Gephi Modularity class "
                "(weighted, resolution 1.0, randomize off; 81 classes, Q = 0.27 on this profiled subgraph). "
                "Groups cut across author types; class numbers have no topic meaning.",
                "Colours here are arbitrary group IDs, not author types.")
    if (FIG / "largest_component_communities.png").exists():
        rows = top_classes(STATS / "authors_lwcc_palette.csv")
        items = [("dot", r["hex"], f"group {r['modularity_class']}: {int(r['users']):,} users ({100 * int(r['users']) / 9330:.1f}%)") for r in rows]
        other = sum(int(r["users"]) for r in list(csv.DictReader(open(STATS / "authors_lwcc_palette.csv", encoding="utf-8")))[8:])
        items.append(("dot", "#C8C8C8", f"other 58 groups (grey): {other:,} users ({100 * other / 9330:.1f}%)"))
        compose("largest_component_communities.png", "largest_component_communities_slide.png",
                "Structural groups in the largest component", items,
                "Largest weak component of the selected layoff-related author reply network (9,330 users, 12,360 directed pairs). "
                "Node size represents retained replies received; colour represents the baseline modularity partition "
                "(Gephi Modularity, weighted, resolution 1.0, randomize off, 66 groups, Q = 0.813). "
                "Layout positions have no geographical or temporal meaning.",
                "Colours here are arbitrary group IDs, not author types.")
    if (FIG / "conversation_largest_components.png").exists():
        compose("conversation_largest_components.png", "conversation_largest_components_slide.png",
                "Conversation trees (30 largest components)",
                [("dot", "#56B4E9", "r/technology post or comment"), ("dot", "#009E73", "r/programming post or comment")],
                "Keyword-selected post/comment conversation network (13,866 records, 13,206 reply links); the 30 largest weak components. "
                "Node size = replies received. Each connected cluster is one thread (one post and its reply tree); "
                "each star is a heavily answered post or comment. No text is shown.",
                "cscq has no posts in the database, so it does not appear in this post-rooted network.")


if __name__ == "__main__":
    main()
