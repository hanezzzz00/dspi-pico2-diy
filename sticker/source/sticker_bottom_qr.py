import math, os, sys
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, Color, white
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.graphics.barcode.qr import QrCodeWidget
from reportlab.graphics.shapes import Drawing
from reportlab.graphics import renderPDF

HERE = os.path.dirname(os.path.abspath(__file__))
for n in ["Inter-Regular", "Inter-Medium", "Inter-SemiBold", "Inter-Bold", "InterDisplay-Black"]:
    pdfmetrics.registerFont(TTFont(n, os.path.join(HERE, "fonts", f"{n}.ttf")))
OUT = sys.argv[1] if len(sys.argv) > 1 else "/home/claude/DSPi_samolepka_spodek_QR.pdf"

URL = "https://github.com/hanezzzz00/dspi-pico2-diy"
URL1, URL2 = "github.com/hanezzzz00/", "dspi-pico2-diy"

# dno krabičky (mm), stejné obrysy jako víko; rohové výřezy 10 × 10 mm nechávají místo pro gumové nožičky
W, D = 70.8, 68.8
CUT_IN, CUT_NOTCH = 0.4, 10.0
FILM = 2.0
ART_IN, ART_NOTCH = CUT_IN + FILM, CUT_NOTCH + FILM

BG0, BG1 = HexColor("#f7fafd"), HexColor("#e2ecf6")
NAVY, INK2 = HexColor("#13203a"), HexColor("#55657d")
TEAL, PINK, ORANGE = HexColor("#13a89b"), HexColor("#e5446d"), HexColor("#f07a2a")
CUTC = HexColor("#8a9bb0")


def contour(inset, notch, w=W, d=D):
    return [(notch, inset), (w - notch, inset), (w - notch, notch), (w - inset, notch), (w - inset, d - notch),
            (w - notch, d - notch), (w - notch, d - inset), (notch, d - inset), (notch, d - notch), (inset, d - notch),
            (inset, notch), (notch, notch)]


def rounded_path(c, pts, r, X, Y):
    p = c.beginPath(); n = len(pts)
    def off(a, b, dd):
        dx, dy = b[0] - a[0], b[1] - a[1]; L = math.hypot(dx, dy); return (a[0] + dx / L * dd, a[1] + dy / L * dd)
    for i in range(n):
        prev, cur, nxt = pts[i - 1], pts[i], pts[(i + 1) % n]
        a = off(cur, prev, r); b = off(cur, nxt, r)
        if i == 0: p.moveTo(X(a[0]), Y(a[1]))
        else: p.lineTo(X(a[0]), Y(a[1]))
        k = 0.55
        p.curveTo(X(a[0] + (cur[0] - a[0]) * k), Y(a[1] + (cur[1] - a[1]) * k),
                  X(b[0] + (cur[0] - b[0]) * k), Y(b[1] + (cur[1] - b[1]) * k), X(b[0]), Y(b[1]))
    p.close(); return p


def txt(c, x, y, text, font, size, color=NAVY, anchor="l", space=0.0):
    w = pdfmetrics.stringWidth(text, font, size) + space * (len(text) - 1)
    if anchor == "r": x -= w
    elif anchor == "c": x -= w / 2
    t = c.beginText(); t.setTextOrigin(x, y); t.setFont(font, size); t.setCharSpace(space); t.setFillColor(color)
    t.textOut(text); c.drawText(t)
    return w / mm


def qr(c, x, y, size, quiet=True):
    """QR kód (vektorově) se světlou zónou; x, y = levý dolní roh včetně zóny, size = celková šířka (pt)."""
    w = QrCodeWidget(URL, barLevel="Q", barBorder=4 if quiet else 0)
    b = w.getBounds(); bw, bh = b[2] - b[0], b[3] - b[1]
    w.barWidth = w.barHeight = size
    w.barFillColor = NAVY
    d = Drawing(size, size); d.add(w)
    renderPDF.draw(d, c, x, y)


def bars(c, x, y, wbar=4.2, h=0.9, gap=1.2):
    for i, col in enumerate([TEAL, PINK, ORANGE]):
        c.setFillColor(col); c.roundRect(x + i * (wbar + gap) * mm, y, wbar * mm, h * mm, 0.3 * mm, stroke=0, fill=1)


def bottom_sticker(c, ox, oy, cut=True):
    X = lambda v: ox + v * mm; Y = lambda v: oy + v * mm
    art = contour(ART_IN, ART_NOTCH)
    # pozadí: svislý přechod
    c.saveState()
    c.clipPath(rounded_path(c, art, 2.0, X, Y), stroke=0, fill=0)
    N = 60
    for i in range(N):
        t = i / (N - 1)
        col = Color(BG1.red + (BG0.red - BG1.red) * t, BG1.green + (BG0.green - BG1.green) * t, BG1.blue + (BG0.blue - BG1.blue) * t)
        c.setFillColor(col); c.rect(X(0), Y(D * i / N), W * mm, D / N * mm + 0.6, stroke=0, fill=1)
    # barevná linka nahoře mezi výřezy
    c.setFillColor(TEAL); c.rect(X(ART_NOTCH), Y(D - ART_IN - 1.4), (W - 2 * ART_NOTCH) / 3 * mm, 1.4 * mm, stroke=0, fill=1)
    c.setFillColor(PINK); c.rect(X(ART_NOTCH + (W - 2 * ART_NOTCH) / 3), Y(D - ART_IN - 1.4), (W - 2 * ART_NOTCH) / 3 * mm, 1.4 * mm, stroke=0, fill=1)
    c.setFillColor(ORANGE); c.rect(X(ART_NOTCH + 2 * (W - 2 * ART_NOTCH) / 3), Y(D - ART_IN - 1.4), (W - 2 * ART_NOTCH) / 3 * mm, 1.4 * mm, stroke=0, fill=1)
    c.restoreState()

    # hlavička mezi horními výřezy (x 12 … 58.8)
    hx0, hx1 = ART_NOTCH + 1.2, W - ART_NOTCH - 1.2
    txt(c, X(hx0), Y(D - 12.6), "DSPi", "InterDisplay-Black", 21, NAVY)
    bars(c, X(hx0 + 0.3), Y(D - 15.0))
    txt(c, X(hx1), Y(D - 8.8), "NÁVOD · GUIDE", "Inter-Bold", 6.4, TEAL, "r", 0.5)
    txt(c, X(hx1), Y(D - 12.4), "CZ / EN", "Inter-SemiBold", 5.6, INK2, "r", 0.4)

    # QR na bílé dlaždici (dlaždice = světlá zóna 4 moduly)
    q = 34.0; qx, qy = ART_IN + 3.0, 15.6
    c.setFillColor(white); c.roundRect(X(qx), Y(qy), q * mm, q * mm, 2.2 * mm, stroke=0, fill=1)
    qr(c, X(qx), Y(qy), q * mm)

    # pravý sloupec
    rx = qx + q + 3.0
    y = qy + q - 3.2
    txt(c, X(rx), Y(y), "SCAN", "Inter-Bold", 7.2, PINK, space=0.6); y -= 4.6
    for line in ["návod a nastavení", "build & setup guide", "STL + Fusion", "samolepky / stickers"]:
        txt(c, X(rx), Y(y), line, "Inter-Medium", 5.4, NAVY); y -= 3.5
    y -= 2.4
    c.setStrokeColor(HexColor("#c4d2e2")); c.setLineWidth(0.4); c.line(X(rx), Y(y + 2.3), X(W - ART_IN - 2.2), Y(y + 2.3))
    for line in ["Raspberry Pi Pico 2", "PCM5102A · 24-bit DAC", "firmware DSPi (Weeb Labs)"]:
        txt(c, X(rx), Y(y - 0.4), line, "Inter-Regular", 4.6, INK2); y -= 3.1

    # URL dole mezi výřezy
    cx = W / 2
    txt(c, X(cx), Y(9.0), URL1, "Inter-SemiBold", 6.6, INK2, "c")
    txt(c, X(cx), Y(4.6), URL2, "Inter-Bold", 8.4, NAVY, "c")

    if cut:
        c.setStrokeColor(CUTC); c.setLineWidth(0.35); c.setDash(1.6, 1.2)
        c.drawPath(rounded_path(c, contour(CUT_IN, CUT_NOTCH), 1.2, X, Y), stroke=1, fill=0)
        c.setDash()


def mini(c, ox, oy, s=26.0, cut=True):
    """Malá samolepka: jen QR + krátký popis (pro jiné krabičky nebo kabel)."""
    X = lambda v: ox + v * mm; Y = lambda v: oy + v * mm
    h = s + 7.0
    c.setFillColor(white); c.roundRect(X(0), Y(0), s * mm, h * mm, 2.4 * mm, stroke=0, fill=1)
    c.setFillColor(TEAL); c.roundRect(X(0), Y(h - 1.4), s * mm, 1.4 * mm, 0.6 * mm, stroke=0, fill=1)
    qr(c, X(0.5), Y(6.0), (s - 1.0) * mm)
    txt(c, X(s / 2), Y(3.4), "DSPi · návod / guide", "Inter-Bold", 5.0, NAVY, "c")
    txt(c, X(s / 2), Y(1.1), "github.com/hanezzzz00", "Inter-Regular", 3.6, INK2, "c")
    if cut:
        c.setStrokeColor(CUTC); c.setLineWidth(0.35); c.setDash(1.6, 1.2)
        c.roundRect(X(-1.2), Y(-1.2), (s + 2.4) * mm, (h + 2.4) * mm, 3.2 * mm, stroke=1, fill=0)
        c.setDash()


c = canvas.Canvas(OUT, pagesize=A4)
c.setTitle("DSPi – samolepka na dno krabičky s QR kódem"); c.setAuthor("dspi-pico2-diy")
PW, PH = A4
txt(c, 15 * mm, PH - 16 * mm, "DSPi – samolepka na dno krabičky (QR kód na návod)", "Inter-Bold", 11, NAVY)
y0 = PH - 22 * mm
for i, s in enumerate([
        "Tiskněte ve SKUTEČNÉ VELIKOSTI (100 %), ne „přizpůsobit stránce“. Kontrolní měřítko dole musí mít přesně 50 mm.",
        "Velká samolepka má tvar dna krabičky (70,8 × 68,8 mm); rohové výřezy 10 × 10 mm jsou místo pro gumové nožičky.",
        "Potisk je 2 mm od řezu – okraj pro přesah laminovací fólie. Zalaminujte, pak stříhejte po přerušované čáře.",
        "QR kód má zvýšenou korekci chyb (Q), přečte se i přes lesklou fólii. Před nalepením ho vyzkoušejte telefonem.",
        "Malé samolepky dole: jen QR kód, např. na kabel, krabičku od dílů nebo do šuplíku."]):
    txt(c, 15 * mm, y0 - i * 4.4 * mm, s, "Inter-Regular", 7.6, INK2)

top = PH - 50 * mm - D * mm
bottom_sticker(c, 15 * mm, top)
bottom_sticker(c, (15 + W + 10) * mm, top)
my = top - 50 * mm
for i in range(6):
    mini(c, (17 + i * 30.5) * mm, my)

# měřítko 50 mm
bx, by = 15 * mm, 24 * mm
c.setStrokeColor(NAVY); c.setLineWidth(0.6); c.line(bx, by, bx + 50 * mm, by)
for k in range(6):
    c.line(bx + k * 10 * mm, by, bx + k * 10 * mm, by + (2.2 if k in (0, 5) else 1.2) * mm)
txt(c, bx + 52 * mm, by - 0.8 * mm, "kontrolní měřítko 50 mm", "Inter-Regular", 7, INK2)
txt(c, 15 * mm, 14 * mm, URL + "  ·  CC BY-SA 4.0", "Inter-Regular", 6.5, INK2)
c.showPage(); c.save(); print(OUT)
