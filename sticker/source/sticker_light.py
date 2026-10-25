import math
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, Color
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

for n in ["Inter-Regular", "Inter-Medium", "Inter-SemiBold", "Inter-Bold", "InterDisplay-Black", "InterDisplay-Bold"]:
    pdfmetrics.registerFont(TTFont(n, f"fonts/{n}.ttf"))
OUT = "/home/claude/DSPi_samolepka_vika_svetla.pdf"

# víko (mm; počátek levý přední roh, Y dozadu)
LID_W, LID_D, LID_R = 70.8, 68.8, 4.0
SCREWS = [(5.9, 5.9), (64.9, 5.9), (5.9, 62.9), (64.9, 62.9)]; CSK_D = 6.5
BTNS = [(42.4, 18.4), (58.4, 18.4)]; BTN_D = 12.0
USB_X, JACK_Y = 21.9, 49.4

CUT_IN, CUT_NOTCH = 0.4, 10.0     # řez: 0,4 mm od hrany víka, rohové výřezy 10 × 10 mm (šrouby)
FILM = 2.0                        # okraj laminovací fólie mezi potiskem a řezem
ART_IN, ART_NOTCH = CUT_IN + FILM, CUT_NOTCH + FILM

BG0, BG1 = HexColor("#f7fafd"), HexColor("#e2ecf6")
NAVY, INK2 = HexColor("#13203a"), HexColor("#55657d")
TEAL, PINK, ORANGE = HexColor("#13a89b"), HexColor("#e5446d"), HexColor("#f07a2a")


def mix(a, b, t):
    t = max(0, min(1, t))
    return Color(a.red + (b.red - a.red) * t, a.green + (b.green - a.green) * t, a.blue + (b.blue - a.blue) * t)


def tri(t):
    return mix(TEAL, PINK, t / 0.5) if t < 0.5 else mix(PINK, ORANGE, (t - 0.5) / 0.5)


def contour(inset, notch):
    W, D = LID_W, LID_D
    return [(notch, inset), (W - notch, inset), (W - notch, notch), (W - inset, notch), (W - inset, D - notch),
            (W - notch, D - notch), (W - notch, D - inset), (notch, D - inset), (notch, D - notch), (inset, D - notch),
            (inset, notch), (notch, notch)]


def rounded_path(c, pts, r, X, Y):
    p = c.beginPath(); n = len(pts)
    def off(a, b, d):
        dx, dy = b[0] - a[0], b[1] - a[1]; L = math.hypot(dx, dy); return (a[0] + dx / L * d, a[1] + dy / L * d)
    for i in range(n):
        prev, cur, nxt = pts[i - 1], pts[i], pts[(i + 1) % n]
        a = off(cur, prev, r); b = off(cur, nxt, r)
        if i == 0: p.moveTo(X(a[0]), Y(a[1]))
        else: p.lineTo(X(a[0]), Y(a[1]))
        k = 0.55
        p.curveTo(X(a[0] + (cur[0] - a[0]) * k), Y(a[1] + (cur[1] - a[1]) * k),
                  X(b[0] + (cur[0] - b[0]) * k), Y(b[1] + (cur[1] - b[1]) * k), X(b[0]), Y(b[1]))
    p.close(); return p


def spaced(c, x, y, text, font, size, space=0.0, color=NAVY, anchor="l"):
    w = pdfmetrics.stringWidth(text, font, size) + space * (len(text) - 1)
    if anchor == "r": x -= w
    elif anchor == "c": x -= w / 2
    t = c.beginText(); t.setTextOrigin(x, y); t.setFont(font, size); t.setCharSpace(space); t.setFillColor(color)
    t.textOut(text); c.drawText(t)
    return w / mm


def eq_curve(f):
    lf = math.log10(f)
    g = 7.0 / (1 + math.exp((lf - math.log10(90)) * 9))
    g += 5.0 * math.exp(-((lf - math.log10(55)) / 0.12) ** 2)
    g -= 3.0 * math.exp(-((lf - math.log10(900)) / 0.35) ** 2)
    g += 5.0 * math.exp(-((lf - math.log10(6500)) / 0.32) ** 2)
    return g


def draw_sticker(c, ox, oy, cut_line=True):
    """ox, oy = poloha levého předního rohu VÍKA na stránce."""
    X = lambda v: ox + v * mm; Y = lambda v: oy + v * mm
    art = contour(ART_IN, ART_NOTCH)
    # pozadí potisku
    c.saveState()
    c.clipPath(rounded_path(c, art, 1.6, X, Y), stroke=0, fill=0)
    c.linearGradient(X(0), Y(LID_D), X(LID_W), Y(0), (BG0, BG1), extend=True)
    # jemná barevná vlna na pozadí (jedna vlna s barevným přechodem)
    M = 120
    for i in range(M):
        xa, xb = i / M * LID_W, (i + 1) / M * LID_W + 0.05
        ya = 8.5 + 3.2 * math.sin(xa / LID_W * 2 * math.pi + 0.6)
        yb = 8.5 + 3.2 * math.sin(xb / LID_W * 2 * math.pi + 0.6)
        p = c.beginPath(); p.moveTo(X(xa), Y(0)); p.lineTo(X(xa), Y(ya)); p.lineTo(X(xb), Y(yb)); p.lineTo(X(xb), Y(0)); p.close()
        c.setFillColor(mix(HexColor('#ecf2f8'), tri(i / (M - 1)), 0.22)); c.drawPath(p, stroke=0, fill=1)
    c.setFillAlpha(1)
    # barevný proužek podél horní hrany potisku
    top = LID_D - ART_IN
    N = 60
    for i in range(N):
        x0 = ART_NOTCH + (LID_W - 2 * ART_NOTCH) * i / N
        c.setFillColor(tri(i / (N - 1)))
        c.rect(X(x0), Y(top - 0.9), (LID_W - 2 * ART_NOTCH) / N * mm + 0.2, 0.9 * mm, stroke=0, fill=1)

    L = ART_IN + 2.1            # levý okraj textu
    # --- USB ---
    pw, ph = 18.0, 4.2
    pt = top - 2.0
    c.setFillColor(TEAL); c.roundRect(X(USB_X - pw / 2), Y(pt - ph), pw * mm, ph * mm, 2.1 * mm, stroke=0, fill=1)
    ax, ay = USB_X - pw / 2 + 2.8, pt - ph / 2
    c.setFillColor(HexColor("#ffffff"))
    p = c.beginPath(); p.moveTo(X(ax - 1.25), Y(ay - 0.75)); p.lineTo(X(ax + 1.25), Y(ay - 0.75)); p.lineTo(X(ax), Y(ay + 1.15)); p.close()
    c.drawPath(p, stroke=0, fill=1)
    w = spaced(c, X(ax + 2.0), Y(ay - 0.75), "USB · PC", "Inter-Bold", 5.6, 0.2, HexColor("#ffffff"))
    assert ax + 2.0 + w < USB_X + pw / 2 - 1.2

    # --- název ---
    tb = 44.6
    tw = spaced(c, X(L - 0.4), Y(tb), "DSPi", "InterDisplay-Black", 40, -0.7, NAVY)
    assert tb + 40 * 0.3528 * 0.73 < LID_D - ART_NOTCH - 0.5, "title hits notch"
    for i, col in enumerate((TEAL, PINK, ORANGE)):
        c.setFillColor(col); c.rect(X(L + i * 5.0), Y(tb - 2.4), 4.3 * mm, 0.9 * mm, stroke=0, fill=1)
    spaced(c, X(L), Y(tb - 6.2), "DIGITAL SIGNAL PROCESSOR", "Inter-SemiBold", 5.4, 0.6, INK2)

    # --- STEREO OUT ---
    jw, jh = 22.5, 4.2
    jx0 = LID_W - ART_IN - 1.6 - jw
    assert L - 0.4 + tw < jx0 - 1.0, ("title vs jack", L + tw, jx0)
    c.setFillColor(ORANGE); c.roundRect(X(jx0), Y(JACK_Y - jh / 2), jw * mm, jh * mm, 2.1 * mm, stroke=0, fill=1)
    c.setStrokeColor(HexColor("#ffffff")); c.setLineWidth(0.5)
    c.circle(X(jx0 + 2.3), Y(JACK_Y), 1.1 * mm, stroke=1, fill=0)
    c.setFillColor(HexColor("#ffffff")); c.circle(X(jx0 + 2.3), Y(JACK_Y), 0.4 * mm, stroke=0, fill=1)
    w = spaced(c, X(jx0 + 4.2), Y(JACK_Y - 0.75), "STEREO OUT", "Inter-Bold", 5.6, 0.2, HexColor("#ffffff"))
    axx = jx0 + jw - 2.1
    assert jx0 + 4.2 + w < axx - 1.2
    p = c.beginPath(); p.moveTo(X(axx - 0.9), Y(JACK_Y + 1.25)); p.lineTo(X(axx - 0.9), Y(JACK_Y - 1.25)); p.lineTo(X(axx + 1.0), Y(JACK_Y)); p.close()
    c.drawPath(p, stroke=0, fill=1)

    # --- graf EQ ---
    gx0, gx1, gy0, gy1 = L, LID_W - ART_IN - 2.1, 28.0, 35.2
    gmid = (gy0 + gy1) / 2 - 0.7
    c.setStrokeColor(NAVY); c.setLineWidth(0.18); c.setStrokeAlpha(0.13)
    for fr in (20, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000):
        xx = gx0 + math.log10(fr / 20) / 3 * (gx1 - gx0); c.line(X(xx), Y(gy0), X(xx), Y(gy1))
    for k in range(5):
        yy = gy0 + k * (gy1 - gy0) / 4; c.line(X(gx0), Y(yy), X(gx1), Y(yy))
    c.setStrokeAlpha(0.35); c.setLineWidth(0.25); c.line(X(gx0), Y(gmid), X(gx1), Y(gmid)); c.setStrokeAlpha(1)
    Np = 180; pts = []
    for i in range(Np + 1):
        t = i / Np; pts.append((gx0 + t * (gx1 - gx0), gmid + eq_curve(20 * 10 ** (3 * t)) * 0.42))
    c.setFillColor(TEAL); c.setFillAlpha(0.18)
    pa = c.beginPath(); pa.moveTo(X(pts[0][0]), Y(gmid))
    for px, py in pts: pa.lineTo(X(px), Y(py))
    pa.lineTo(X(pts[-1][0]), Y(gmid)); pa.close(); c.drawPath(pa, stroke=0, fill=1); c.setFillAlpha(1)
    c.setLineWidth(0.7); c.setLineCap(1)
    for i in range(Np):
        c.setStrokeColor(tri(i / Np)); c.line(X(pts[i][0]), Y(pts[i][1]), X(pts[i + 1][0]), Y(pts[i + 1][1]))
    for fr, col in ((55, TEAL), (900, PINK), (6500, ORANGE)):
        t = math.log10(fr / 20) / 3; xx = gx0 + t * (gx1 - gx0); yy = gmid + eq_curve(fr) * 0.42
        c.setFillColor(HexColor("#ffffff")); c.setStrokeColor(col); c.setLineWidth(0.45)
        c.circle(X(xx), Y(yy), 0.85 * mm, stroke=1, fill=1)
        c.setFillColor(col); c.circle(X(xx), Y(yy), 0.36 * mm, stroke=0, fill=1)

    # --- tlačítka (místa pro pozdější provrtání) ---
    for (bx, by), lab, col in zip(BTNS, ("POWER", "SPK / HP"), (PINK, TEAL)):
        c.setStrokeColor(col); c.setLineWidth(0.7); c.setFillColor(HexColor("#ffffff")); c.setFillAlpha(0.55)
        c.circle(X(bx), Y(by), 6.4 * mm, stroke=1, fill=1); c.setFillAlpha(1)
        c.setLineWidth(0.3); c.setDash(0.8, 0.8); c.circle(X(bx), Y(by), 6.0 * mm, stroke=1, fill=0); c.setDash()
        w = spaced(c, X(bx), Y(by + 6.4 + 1.1), lab, "Inter-Bold", 5.0, 0.3, col, "c")
    # --- technické údaje vlevo dole ---
    lines = [("RASPBERRY PI PICO 2", "Inter-Bold", NAVY), ("PCM5102A · 24-BIT DAC", "Inter-SemiBold", INK2),
             ("USB AUDIO · PARAMETRIC EQ", "Inter-SemiBold", INK2)]
    yy = 22.0
    for txt, f, col in lines:
        w = spaced(c, X(L), Y(yy), txt, f, 4.6, 0.3, col)
        assert L + w < BTNS[0][0] - 6.4 - 1.0, txt
        yy -= 3.4
    assert yy + 3.4 > ART_NOTCH + 0.5
    c.restoreState()
    if cut_line:
        c.saveState(); c.setStrokeColor(HexColor("#7a8699")); c.setLineWidth(0.3); c.setDash(1.6, 1.0)
        p = c.beginPath(); cp = contour(CUT_IN, CUT_NOTCH)
        p.moveTo(X(cp[0][0]), Y(cp[0][1]))
        for q in cp[1:]: p.lineTo(X(q[0]), Y(q[1]))
        p.close(); c.drawPath(p, stroke=1, fill=0); c.restoreState()


def lid_bg(c, ox, oy):
    X = lambda v: ox + v * mm; Y = lambda v: oy + v * mm
    c.saveState(); c.setFillColor(HexColor("#c9ced6")); c.setStrokeColor(HexColor("#555b66")); c.setLineWidth(0.4)
    c.roundRect(X(0), Y(0), LID_W * mm, LID_D * mm, LID_R * mm, stroke=1, fill=1)
    c.setFillColor(HexColor("#ffffff"))
    for sx, sy in SCREWS: c.circle(X(sx), Y(sy), CSK_D / 2 * mm, stroke=1, fill=1)
    c.restoreState()


def note(c, x, y, text, size=8, font="Inter-Regular", color=HexColor("#333333")):
    c.setFont(font, size); c.setFillColor(color); c.drawString(x, y, text)


c = canvas.Canvas(OUT, pagesize=A4); c.setTitle("DSPi – samolepka na víko (světlá)")
PW, PH = A4
note(c, 15 * mm, PH - 15 * mm, "DSPi – samolepka na celé víko (světlá verze, pro laminování)", 13, "Inter-Bold", HexColor("#111111"))
for i, t in enumerate([
        "Tiskněte ve SKUTEČNÉ VELIKOSTI (100 %). Kontrolní měřítko dole musí mít přesně 50 mm.",
        "Po zalaminování stříhejte podle šedé přerušované čáry – mezi potiskem a čarou zůstane 2 mm fólie, která drží zatavená.",
        "Rohové výřezy 10 × 10 mm nechávají volné šrouby víka. Kruhy POWER / SPK / HP jsou nad zahloubeními pro tlačítka –",
        "po jejich provrtání otvor v samolepce prořízněte skalpelem (nebo děrovačkou Ø 12 mm)."]):
    note(c, 15 * mm, PH - (21 + i * 4.5) * mm, t, 8)
# dva kusy vedle sebe s mezerou (každý se laminuje/stříhá samostatně)
for k, ox in enumerate((22 * mm, 22 * mm + LID_W * mm + 25 * mm)):
    draw_sticker(c, ox, PH - 125 * mm)
# kontrolní měřítko
bx, by = 15 * mm, 40 * mm
c.setStrokeColor(HexColor("#000000")); c.setLineWidth(0.4); c.line(bx, by, bx + 50 * mm, by)
for k in range(6):
    c.line(bx + k * 10 * mm, by, bx + k * 10 * mm, by + (3 if k % 5 == 0 else 1.8) * mm)
note(c, bx + 52 * mm, by - 0.8 * mm, "kontrolní měřítko 50 mm", 8)
# náhled na víku
note(c, 15 * mm, PH - 140 * mm, "Náhled na víku (1:1, pohled shora, přední hrana dole; USB vzadu, jack vpravo)", 9, "Inter-SemiBold")
ox, oy = 22 * mm, PH - 225 * mm
lid_bg(c, ox, oy); draw_sticker(c, ox, oy, cut_line=False)
c.showPage(); c.save(); print(OUT)
