import sys, os
LANG = (sys.argv[1] if len(sys.argv) > 1 else "cz").lower()   # "cz" nebo "en"
def tr(cz, en): return en if LANG == "en" else cz
os.chdir(os.path.dirname(os.path.abspath(__file__)))   # fonts/ relativně ke skriptu
import math
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, Color
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

for n in ["Inter-Regular", "Inter-Medium", "Inter-SemiBold", "Inter-Bold", "InterDisplay-Black", "InterDisplay-Bold"]:
    pdfmetrics.registerFont(TTFont(n, f"fonts/{n}.ttf"))

OUT = sys.argv[2] if len(sys.argv) > 2 else "/home/claude/DSPi_samolepka_vika.pdf"

# --- víko (mm, počátek = levý přední roh, Y dozadu) ---
LID_W, LID_D, LID_R = 70.8, 68.8, 4.0
SCREWS = [(5.9, 5.9), (64.9, 5.9), (5.9, 62.9), (64.9, 62.9)]; CSK_D = 6.5
BTNS = [(42.4, 18.4), (58.4, 18.4)]; BTN_D = 12.0
USB_X = 21.9            # střed USB na zadní hraně
JACK_Y = 49.4           # střed jacku na pravé hraně

# --- hlavní samolepka ---
LX0, LY0, LW, LH = 10.0, 26.0, 50.8, 40.8
# --- volitelný proužek pod tlačítka ---
SX0, SY0, SW, SH = 33.4, 2.6, 27.8, 7.4
BLEED = 2.0

BG0, BG1 = HexColor("#0d1424"), HexColor("#1f3050")
TEAL, ORANGE, PINK = HexColor("#2ec4b6"), HexColor("#ff8a3d"), HexColor("#ff4f81")
WHITE, MUTED, GRID = HexColor("#f4f7fb"), HexColor("#9fb3c8"), HexColor("#ffffff")


def mix(a, b, t):
    return Color(a.red + (b.red - a.red) * t, a.green + (b.green - a.green) * t, a.blue + (b.blue - a.blue) * t)


def spaced(c, x, y, text, font, size, space=0.0, color=WHITE, anchor="l"):
    w = pdfmetrics.stringWidth(text, font, size) + space * (len(text) - 1)
    if anchor == "r": x -= w
    elif anchor == "c": x -= w / 2
    t = c.beginText(); t.setTextOrigin(x, y); t.setFont(font, size); t.setCharSpace(space); t.setFillColor(color)
    t.textOut(text); c.drawText(t)
    return w


def background(c, x, y, w, h):
    """Pozadí s přesahem (bleed) a gradientem."""
    c.saveState()
    p = c.beginPath(); p.rect(x - BLEED * mm, y - BLEED * mm, w + 2 * BLEED * mm, h + 2 * BLEED * mm)
    c.clipPath(p, stroke=0, fill=0)
    c.linearGradient(x, y + h, x + w, y, (BG1, BG0), extend=True)
    c.restoreState()


def eq_curve(f):
    """Ukázková korekční křivka (dB) – basy nahoru, středy dolů, výšky nahoru."""
    lf = math.log10(f)
    g = 7.0 / (1 + math.exp((lf - math.log10(90)) * 9))            # low shelf
    g += 5.0 * math.exp(-((lf - math.log10(55)) / 0.12) ** 2)       # peak 55 Hz
    g -= 3.0 * math.exp(-((lf - math.log10(900)) / 0.35) ** 2)      # mid dip
    g += 5.0 * math.exp(-((lf - math.log10(6500)) / 0.32) ** 2)     # presence/air
    return g


def draw_main(c, ox, oy):
    """Hlavní samolepka; ox, oy = levý dolní roh řezu (body)."""
    W, H = LW * mm, LH * mm
    background(c, ox, oy, W, H)
    X = lambda v: ox + v * mm
    Y = lambda v: oy + v * mm
    c.saveState()
    p = c.beginPath(); p.rect(ox - BLEED * mm, oy - BLEED * mm, W + 2 * BLEED * mm, H + 2 * BLEED * mm)
    c.clipPath(p, stroke=0, fill=0)

    # --- graf EQ ---
    gx0, gx1, gy0, gy1 = 4.0, LW - 4.0, 6.2, 16.4
    gmid = (gy0 + gy1) / 2 - 1.0
    c.setStrokeColor(GRID); c.setLineWidth(0.18)
    c.setStrokeAlpha(0.13)
    for fr in (20, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000):
        xx = gx0 + (math.log10(fr) - math.log10(20)) / 3 * (gx1 - gx0)
        c.line(X(xx), Y(gy0), X(xx), Y(gy1))
    for k in range(5):
        yy = gy0 + k * (gy1 - gy0) / 4
        c.line(X(gx0), Y(yy), X(gx1), Y(yy))
    c.setStrokeAlpha(0.35); c.setLineWidth(0.25)
    c.line(X(gx0), Y(gmid), X(gx1), Y(gmid))
    c.setStrokeAlpha(1)
    pts = []
    N = 160
    for i in range(N + 1):
        t = i / N
        f = 20 * 10 ** (3 * t)
        pts.append((gx0 + t * (gx1 - gx0), gmid + eq_curve(f) * 0.62))
    # výplň pod křivkou
    c.setFillColor(TEAL); c.setFillAlpha(0.16)
    path = c.beginPath(); path.moveTo(X(pts[0][0]), Y(gmid))
    for px, py in pts: path.lineTo(X(px), Y(py))
    path.lineTo(X(pts[-1][0]), Y(gmid)); path.close()
    c.drawPath(path, stroke=0, fill=1)
    c.setFillAlpha(1)
    # křivka s barevným přechodem
    c.setLineWidth(0.55); c.setLineCap(1)
    for i in range(N):
        t = i / N
        col = mix(TEAL, PINK, t / 0.55) if t < 0.55 else mix(PINK, ORANGE, (t - 0.55) / 0.45)
        c.setStrokeColor(col)
        c.line(X(pts[i][0]), Y(pts[i][1]), X(pts[i + 1][0]), Y(pts[i + 1][1]))
    # body pásem
    for fr, col in ((55, TEAL), (900, PINK), (6500, ORANGE)):
        t = math.log10(fr / 20) / 3
        xx = gx0 + t * (gx1 - gx0); yy = gmid + eq_curve(fr) * 0.62
        c.setFillColor(BG0); c.setStrokeColor(col); c.setLineWidth(0.35)
        c.circle(X(xx), Y(yy), 0.75 * mm, stroke=1, fill=1)
        c.setFillColor(col); c.circle(X(xx), Y(yy), 0.32 * mm, stroke=0, fill=1)
    # popisky os
    for fr, lab in ((100, "100"), (1000, "1k"), (10000, "10k")):
        xx = gx0 + (math.log10(fr) - math.log10(20)) / 3 * (gx1 - gx0)
        spaced(c, X(xx), Y(gy0 - 1.6), lab, "Inter-Medium", 4.0, 0.1, MUTED, "c")

    # --- název ---
    tx = 4.0
    tw = spaced(c, X(tx - 0.3), Y(26.6), "DSPi", "InterDisplay-Black", 30, -0.5, WHITE)
    assert tx - 0.3 + tw / mm < LW - 1.6 - 20.2 + 0.2, ("title overlaps jack pill", tw / mm)
    # barevný proužek pod názvem
    for i, col in enumerate((TEAL, PINK, ORANGE)):
        c.setFillColor(col); c.rect(X(tx + i * 4.2), Y(23.0), 3.6 * mm, 0.7 * mm, stroke=0, fill=1)
    spaced(c, X(tx), Y(19.0), "DIGITAL SIGNAL PROCESSOR", "Inter-SemiBold", 4.6, 0.55, MUTED)

    # --- USB (míří k zadní hraně) ---
    ux = USB_X - LX0
    pill_w, pill_h = 16.5, 4.0
    c.setFillColor(TEAL); c.roundRect(X(ux - pill_w / 2), Y(LH - 1.6 - pill_h), pill_w * mm, pill_h * mm, 2 * mm, stroke=0, fill=1)
    # šipka nahoru
    ax, ay = ux - pill_w / 2 + 2.6, LH - 1.6 - pill_h / 2
    c.setFillColor(BG0)
    p = c.beginPath(); p.moveTo(X(ax - 1.2), Y(ay - 0.7)); p.lineTo(X(ax + 1.2), Y(ay - 0.7)); p.lineTo(X(ax), Y(ay + 1.1)); p.close()
    c.drawPath(p, stroke=0, fill=1)
    ww = spaced(c, X(ax + 1.9), Y(ay - 0.72), "USB · PC", "Inter-Bold", 5.3, 0.2, BG0) / mm
    assert ax + 1.9 + ww < ux + pill_w / 2 - 1.0, ("usb text", ww)

    # --- STEREO OUT (míří k pravé hraně) ---
    jy = JACK_Y - LY0
    pw, ph = 20.2, 4.0
    px0 = LW - 1.6 - pw
    c.setFillColor(ORANGE); c.roundRect(X(px0), Y(jy - ph / 2), pw * mm, ph * mm, 2 * mm, stroke=0, fill=1)
    # ikona jacku (kroužek) + šipka doprava
    c.setStrokeColor(BG0); c.setLineWidth(0.45); c.setFillColor(ORANGE)
    c.circle(X(px0 + 2.2), Y(jy), 1.05 * mm, stroke=1, fill=0)
    c.setFillColor(BG0); c.circle(X(px0 + 2.2), Y(jy), 0.38 * mm, stroke=0, fill=1)
    ww = spaced(c, X(px0 + 4.0), Y(jy - 0.7), "STEREO OUT", "Inter-Bold", 5.3, 0.2, BG0) / mm
    assert px0 + 4.0 + ww < px0 + pw - 3.2, ("jack text", ww)
    axx = px0 + pw - 2.0
    p = c.beginPath(); p.moveTo(X(axx - 0.8), Y(jy + 1.2)); p.lineTo(X(axx - 0.8), Y(jy - 1.2)); p.lineTo(X(axx + 1.0), Y(jy)); p.close()
    c.drawPath(p, stroke=0, fill=1)

    # --- spodní řádek ---
    spaced(c, X(4.0), Y(2.2), "RASPBERRY PI PICO 2  ·  PCM5102A", "Inter-Medium", 4.1, 0.35, MUTED)
    spaced(c, X(LW - 4.0), Y(2.2), "24-BIT DAC", "Inter-Bold", 4.1, 0.35, TEAL, "r")
    c.restoreState()


def draw_strip(c, ox, oy):
    """Proužek s popisky tlačítek (až budou tlačítka)."""
    W, H = SW * mm, SH * mm
    background(c, ox, oy, W, H)
    X = lambda v: ox + v * mm; Y = lambda v: oy + v * mm
    items = ((BTNS[0][0] - SX0, "POWER", PINK, "c"), (BTNS[1][0] - SX0, "SPK / HP", TEAL, "r"))
    for cx, lab, col, anc in items:
        tx = cx if anc == "c" else SW - 1.4
        w = spaced(c, X(tx), Y(SH / 2 - 1.2), lab, "Inter-Bold", 5.4, 0.25, WHITE, anc) / mm
        assert (tx - (w / 2 if anc == "c" else w)) > 0.8 and (tx + (w / 2 if anc == "c" else 0)) < SW - 0.8, lab
        c.setFillColor(col)
        p = c.beginPath(); p.moveTo(X(cx - 1.1), Y(SH - 2.4)); p.lineTo(X(cx + 1.1), Y(SH - 2.4)); p.lineTo(X(cx), Y(SH - 0.9)); p.close()
        c.drawPath(p, stroke=0, fill=1)


def crop_marks(c, ox, oy, w, h, gap=1.0, length=4.0):
    c.saveState(); c.setStrokeColor(HexColor("#000000")); c.setLineWidth(0.2)
    g, L = (BLEED + gap) * mm, length * mm
    for x in (ox, ox + w):
        c.line(x, oy - g, x, oy - g - L); c.line(x, oy + h + g, x, oy + h + g + L)
    for y in (oy, oy + h):
        c.line(ox - g, y, ox - g - L, y); c.line(ox + w + g, y, ox + w + g + L, y)
    c.restoreState()


def lid_outline(c, ox, oy, show_label=True):
    """Víko 1:1 s otvory a zahloubeními (pohled shora, přední hrana dole)."""
    X = lambda v: ox + v * mm; Y = lambda v: oy + v * mm
    c.saveState()
    c.setFillColor(HexColor("#d9dce1")); c.setStrokeColor(HexColor("#555b66")); c.setLineWidth(0.4)
    c.roundRect(X(0), Y(0), LID_W * mm, LID_D * mm, LID_R * mm, stroke=1, fill=1)
    c.setFillColor(HexColor("#ffffff"))
    for sx, sy in SCREWS: c.circle(X(sx), Y(sy), CSK_D / 2 * mm, stroke=1, fill=1)
    c.setDash(1.2, 1.0)
    for bx, by in BTNS: c.circle(X(bx), Y(by), BTN_D / 2 * mm, stroke=1, fill=1)
    c.setDash()
    c.restoreState()
    if show_label:
        c.saveState()
        p = c.beginPath(); p.rect(X(LX0), Y(LY0), LW * mm, LH * mm); c.clipPath(p, stroke=0, fill=0)
        draw_main(c, X(LX0), Y(LY0)); c.restoreState()
        c.saveState()
        p = c.beginPath(); p.rect(X(SX0), Y(SY0), SW * mm, SH * mm); c.clipPath(p, stroke=0, fill=0)
        draw_strip(c, X(SX0), Y(SY0)); c.restoreState()


def note(c, x, y, text, size=8, font="Inter-Regular", color=HexColor("#333333")):
    c.setFont(font, size); c.setFillColor(color); c.drawString(x, y, text)


c = canvas.Canvas(OUT, pagesize=A4)
c.setTitle(tr("DSPi – samolepka na víko", "DSPi – lid sticker")); c.setAuthor(tr("DSPi krabička", "DSPi enclosure"))
PW, PH = A4

# ===== strana 1: tiskový arch =====
note(c, 15 * mm, PH - 15 * mm, tr("DSPi – samolepka na víko krabičky", "DSPi – enclosure lid sticker"), 13, "Inter-Bold", HexColor("#111111"))
note(c, 15 * mm, PH - 21 * mm, tr("Tiskněte ve SKUTEČNÉ VELIKOSTI (100 %, bez „Přizpůsobit stránce“). Ověřte měřítkem dole: musí mít přesně 50 mm.", "Print at ACTUAL SIZE (100 %, no \"Fit to page\"). Check with the scale bar below: it must be exactly 50 mm."), 8)
note(c, 15 * mm, PH - 25.5 * mm, tr("Řežte podle značek v rozích – barva přesahuje 2 mm za řez, takže drobná nepřesnost nevadí. Hlavní samolepka 50,8 × 40,8 mm,", "Cut along the corner marks – the colour bleeds 2 mm past the cut, so small inaccuracies do not matter. Main sticker 50.8 × 40.8 mm,"), 8)
note(c, 15 * mm, PH - 30 * mm, tr("proužek pod tlačítka 27,8 × 7,4 mm (lepte až po osazení tlačítek). Několik kusů navíc pro případ pokaženého řezu.", "button strip 27.8 × 7.4 mm (apply after fitting the buttons). Spare copies in case of a bad cut."), 8)

cols = [15, 80, 145]
row_y = [PH / mm - 95, PH / mm - 155]
for ry in row_y:
    for cx in cols:
        ox, oy = cx * mm + 6 * mm, ry * mm
        draw_main(c, ox, oy); crop_marks(c, ox, oy, LW * mm, LH * mm)
sy = PH / mm - 185
for cx in cols:
    ox, oy = cx * mm + 6 * mm, sy * mm
    draw_strip(c, ox, oy); crop_marks(c, ox, oy, SW * mm, SH * mm)
# měřítko
bx, by = 15 * mm, 60 * mm
c.setStrokeColor(HexColor("#000000")); c.setLineWidth(0.4)
c.line(bx, by, bx + 50 * mm, by)
for k in range(6):
    hgt = 3 if k % 5 == 0 else 1.8
    c.line(bx + k * 10 * mm, by, bx + k * 10 * mm, by + hgt * mm)
note(c, bx + 52 * mm, by - 0.8 * mm, tr("kontrolní měřítko 50 mm", "50 mm scale bar"), 8)
note(c, 15 * mm, 50 * mm, tr("Tip: tiskněte na samolepicí fotopapír nebo samolepicí fólii; matný papír přetřete lakem nebo přelepte průhlednou fólií.", "Tip: print on self-adhesive photo paper or vinyl; varnish matte paper or cover it with clear film."), 8)
note(c, 15 * mm, 45.5 * mm, tr("Umístění na víko ukazuje strana 2 (také 1:1 – můžete ji vystřihnout a použít jako šablonu).", "Page 2 shows the placement on the lid (also 1:1 – you can cut it out and use it as a template)."), 8)
c.showPage()

# ===== strana 2: umístění na víku =====
note(c, 15 * mm, PH - 15 * mm, tr("Umístění na víko (měřítko 1:1, pohled shora, přední hrana dole)", "Placement on the lid (1:1, top view, front edge at the bottom)"), 13, "Inter-Bold", HexColor("#111111"))
note(c, 15 * mm, PH - 21 * mm, tr("Hlavní samolepka: 10 mm od levé hrany víka, 2 mm od zadní hrany. Šipka USB pak míří přesně na USB, šipka STEREO OUT na jack.", "Main sticker: 10 mm from the left edge of the lid, 2 mm from the back edge. The USB arrow then points at USB, STEREO OUT at the jack."), 8)
note(c, 15 * mm, PH - 25.5 * mm, tr("Proužek pod tlačítka lepte až po provrtání otvorů pro tlačítka (čárkované kruhy).", "Apply the button strip only after drilling the button holes (dashed circles)."), 8)
ox, oy = (PW - LID_W * mm) / 2, PH - 120 * mm
lid_outline(c, ox, oy)
# popisky okolí
note(c, ox + USB_X * mm - 8 * mm, oy + LID_D * mm + 4 * mm, tr("zadní stěna – USB", "back wall – USB"), 8, "Inter-SemiBold")
c.saveState(); c.translate(ox + LID_W * mm + 4 * mm, oy + JACK_Y * mm - 10 * mm); c.rotate(90)
note(c, 0, 0, tr("pravá stěna – jack", "right wall – jack"), 8, "Inter-SemiBold"); c.restoreState()
note(c, ox + 18 * mm, oy - 7 * mm, tr("přední hrana", "front edge"), 8, "Inter-SemiBold")
c.setStrokeColor(HexColor("#2ec4b6")); c.setLineWidth(0.8)
c.line(ox + USB_X * mm, oy + LID_D * mm + 0.5 * mm, ox + USB_X * mm, oy + LID_D * mm + 3.2 * mm)
c.setStrokeColor(HexColor("#ff8a3d"))
c.line(ox + LID_W * mm + 0.5 * mm, oy + JACK_Y * mm, ox + LID_W * mm + 3.2 * mm, oy + JACK_Y * mm)
c.showPage()
c.save()
print(OUT)
