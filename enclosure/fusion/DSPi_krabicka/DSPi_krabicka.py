# DSPi enclosure – Raspberry Pi Pico 2 H + PCM5102A DAC module (GY-PCM5102)
# Autodesk Fusion script: Utilities > Add-Ins > Scripts and Add-Ins > + > (select this folder) > Run
# Creates a new design with two components (Krabicka = base, Viko = lid) and exports both STL files
# into this folder (DSPi_krabicka_spodek.stl = base, DSPi_krabicka_viko.stl = lid).
# All dimensions are in millimetres in the PARAMETRY (parameters) section below. Edit and run again.
# License: CC BY-SA 4.0
#
# DSPi krabička – Raspberry Pi Pico 2 H + modul DAC PCM5102A
# Skript pro Autodesk Fusion: Utilities > Add-Ins > Scripts and Add-Ins > + > (vyberte tuto složku) > Run
# Vytvoří nový dokument se dvěma komponentami (Krabicka, Viko) a do této složky uloží STL obou dílů.
# Všechny rozměry jsou v milimetrech v sekci PARAMETRY. Po úpravě skript jen spusťte znovu.

import adsk.core, adsk.fusion, traceback, os, math

# ======================= PARAMETRY (mm) =======================
WALL = 2.4          # tloušťka stěn
FLOOR = 2.0         # tloušťka dna
LID = 2.0           # tloušťka víka
IN_W = 66.0         # vnitřní šířka (osa X)
IN_D = 64.0         # vnitřní hloubka (osa Y, zadní stěna je na straně +Y)
IN_H = 30.0         # vnitřní výška (od dna po spodek víka)
R_OUT = 4.0         # zaoblení svislých hran

# Raspberry Pi Pico 2 H – součástkami nahoru, kolíky dolů, USB k zadní stěně
PICO_W, PICO_L, PICO_T = 21.0, 51.0, 1.0
PICO_X0 = 9.0                    # levý okraj desky od vnitřní levé stěny
PICO_GAP_BACK = 1.2              # mezera okraj desky – vnitřní zadní stěna
PICO_POST_H = 22.0               # výška spodní strany desky nade dnem (místo pro piny a dutinky Dupont)
# Lůžko místo šroubů: podpěry pod oběma kratšími konci desky (mezi řadami pinů) + dorazy, deska se přilepí
PICO_PIN_ROW = 1.61              # osa řady pinů od dlouhé hrany desky
PICO_PIN_CLEAR = 2.3             # volný pruh pro lištu a dutinky od osy řady pinů ke středu desky
PICO_SUPPORT_L = 4.0             # délka podpěry pod koncem desky
PICO_FIT = 0.25                  # vůle desky v lůžku (na každou stranu)
PICO_STOP_T = 1.2                # tloušťka dorazů
PICO_STOP_UP = 0.8               # o kolik dorazy přečnívají nad horní stranu desky
USB_Z_ABOVE_PCB = 1.4            # střed micro-USB nad horní stranou desky
USB_OPEN_W, USB_OPEN_H, USB_OPEN_R = 12.5, 8.5, 1.5   # otvor pro koncovku kabelu

# Modul DAC GY-PCM5102 (32 × 17 mm) – jack vystupuje z DLOUHÉ hrany u konce naproti 6pinové liště.
# Modul leží u pravé boční stěny, jack míří ven pravou stěnou, lišta (SCK…VIN) je na předním konci.
DAC_W, DAC_L, DAC_T = 17.0, 32.0, 1.6   # šířka (osa X), délka (osa Y), tloušťka desky
DAC_GAP_SIDE = 1.5               # mezera hrana desky (strana jacku) – vnitřní pravá stěna
DAC_Y0 = 21.0                    # přední okraj desky od vnitřní přední stěny
DAC_Z = 2.5                      # výška podpěr pod deskou (pod jackem jsou vývody, deska nesmí ležet na dně)
JACK_FROM_END = 6.0              # střed jacku od zadního konce desky (ZMĚŘTE)
JACK_Z_ABOVE_PCB = 2.8           # střed jacku nad horní stranou desky (ZMĚŘTE)
JACK_HOLE_D = 8.0                # otvor s vůlí pro nos jacku (Ø5–6 mm)
JACK_CBORE_D, JACK_CBORE_LEFT = 11.0, 0.8   # zahloubení zvenku pro tlustší koncovky kabelu (zbylá stěna)

# Šrouby víka – sloupky v rozích
CPOST_D, CPOST_PILOT, CPOST_PILOT_DEPTH = 7.0, 2.5, 12.0   # samořezný šroub M3
LID_HOLE_D, LID_CSK_D = 3.4, 6.5

# Rezerva pro 2 mikrospínače 12×12 mm ve víku (zatím neprovrtáno)
BTN_POS = [(40.0, 16.0), (56.0, 16.0)]   # středy (X, Y) ve vnitřních souřadnicích
BTN_MARK_D = 12.0                # zahloubení shora, zůstane tenká stěna k provrtání
BTN_SKIN = 0.8
BTN_FRAME_IN, BTN_FRAME_WALL, BTN_FRAME_H = 12.3, 1.2, 3.0
BTN_BOSS_D, BTN_BOSS_PILOT, BTN_BOSS_H, BTN_BOSS_DY = 5.0, 1.7, 6.0, 11.0

EXPORT_STL = True
# ===============================================================

CM = 0.1   # Fusion API pracuje v centimetrech


def P(x, y, z):
    return adsk.core.Point3D.create(x * CM, y * CM, z * CM)


class Geo:
    def __init__(self):
        self.t = adsk.fusion.TemporaryBRepManager.get()

    def box(self, x0, y0, z0, x1, y1, z1):
        c = P((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)
        obb = adsk.core.OrientedBoundingBox3D.create(
            c, adsk.core.Vector3D.create(1, 0, 0), adsk.core.Vector3D.create(0, 1, 0),
            abs(x1 - x0) * CM, abs(y1 - y0) * CM, abs(z1 - z0) * CM)
        return self.t.createBox(obb)

    def cyl(self, p1, p2, d):
        return self.t.createCylinderOrCone(P(*p1), d / 2 * CM, P(*p2), d / 2 * CM)

    def cone(self, p1, d1, p2, d2):
        return self.t.createCylinderOrCone(P(*p1), d1 / 2 * CM, P(*p2), d2 / 2 * CM)

    def add(self, a, b):
        self.t.booleanOperation(a, b, adsk.fusion.BooleanTypes.UnionBooleanType)
        return a

    def sub(self, a, b):
        self.t.booleanOperation(a, b, adsk.fusion.BooleanTypes.DifferenceBooleanType)
        return a

    def rrect_z(self, x0, y0, x1, y1, z0, z1, r):
        """Hranol se zaoblenými svislými hranami."""
        r = max(min(r, (x1 - x0) / 2 - 0.01, (y1 - y0) / 2 - 0.01), 0.01)
        b = self.box(x0 + r, y0, z0, x1 - r, y1, z1)
        self.add(b, self.box(x0, y0 + r, z0, x1, y1 - r, z1))
        for cx, cy in ((x0 + r, y0 + r), (x1 - r, y0 + r), (x0 + r, y1 - r), (x1 - r, y1 - r)):
            self.add(b, self.cyl((cx, cy, z0), (cx, cy, z1), 2 * r))
        return b

    def rrect_y(self, x0, z0, x1, z1, y0, y1, r):
        """Hranol ve směru osy Y se zaoblenými hranami (otvor ve stěně)."""
        b = self.box(x0 + r, y0, z0, x1 - r, y1, z1)
        self.add(b, self.box(x0, y0, z0 + r, x1, y1, z1 - r))
        for cx, cz in ((x0 + r, z0 + r), (x1 - r, z0 + r), (x0 + r, z1 - r), (x1 - r, z1 - r)):
            self.add(b, self.cyl((cx, y0, cz), (cx, y1, cz), 2 * r))
        return b


def build_base(g):
    top = FLOOR + IN_H
    body = g.rrect_z(-WALL, -WALL, IN_W + WALL, IN_D + WALL, 0, top, R_OUT)
    g.sub(body, g.rrect_z(0, 0, IN_W, IN_D, FLOOR, top + 1, max(R_OUT - WALL, 0.5)))

    # rohové sloupky pro šrouby víka
    cr = CPOST_D / 2
    corners = [(cr, cr), (IN_W - cr, cr), (cr, IN_D - cr), (IN_W - cr, IN_D - cr)]
    for cx, cy in corners:
        g.add(body, g.cyl((cx, cy, FLOOR - 0.1), (cx, cy, top), CPOST_D))
        g.add(body, g.box(cx - cr if cx < IN_W / 2 else cx, cy - cr, FLOOR - 0.1,
                          cx if cx < IN_W / 2 else cx + cr, cy + cr, top))   # spojení se stěnou
        g.sub(body, g.cyl((cx, cy, top - CPOST_PILOT_DEPTH), (cx, cy, top + 1), CPOST_PILOT))

    # lůžko pro Pico – bez šroubů, deska se vloží a přilepí
    py1 = IN_D - PICO_GAP_BACK
    py0 = py1 - PICO_L
    pcx = PICO_X0 + PICO_W / 2
    px0, px1 = PICO_X0, PICO_X0 + PICO_W
    zb = FLOOR + PICO_POST_H                 # spodní strana desky
    zt = zb + PICO_T + PICO_STOP_UP          # vršek dorazů
    sx0 = px0 + PICO_PIN_ROW + PICO_PIN_CLEAR   # podpěry jen mezi řadami pinů
    sx1 = px1 - PICO_PIN_ROW - PICO_PIN_CLEAR
    # podpěry pod předním a zadním koncem desky (plocha pro lepidlo)
    g.add(body, g.box(sx0, py0, FLOOR - 0.1, sx1, py0 + PICO_SUPPORT_L, zb))
    g.add(body, g.box(sx0, py1 - PICO_SUPPORT_L, FLOOR - 0.1, sx1, py1, zb))
    # přední doraz přes celou šířku desky (je před deskou, takže nekoliduje s piny); zadní doraz tvoří zadní stěna
    g.add(body, g.box(px0 - PICO_FIT - PICO_STOP_T, py0 - PICO_FIT - PICO_STOP_T, FLOOR - 0.1,
                      px1 + PICO_FIT + PICO_STOP_T, py0 - PICO_FIT, zt))
    # boční dorazy u rohů desky (vně desky, mimo lišty s piny)
    for yy0, yy1 in ((py0 - PICO_FIT - PICO_STOP_T, py0 + PICO_SUPPORT_L), (py1 - PICO_SUPPORT_L, py1)):
        g.add(body, g.box(px0 - PICO_FIT - PICO_STOP_T, yy0, FLOOR - 0.1, px0 - PICO_FIT, yy1, zt))
        g.add(body, g.box(px1 + PICO_FIT, yy0, FLOOR - 0.1, px1 + PICO_FIT + PICO_STOP_T, yy1, zt))
    # otvor pro micro-USB v zadní stěně
    uz = FLOOR + PICO_POST_H + PICO_T + USB_Z_ABOVE_PCB
    g.sub(body, g.rrect_y(pcx - USB_OPEN_W / 2, uz - USB_OPEN_H / 2, pcx + USB_OPEN_W / 2, uz + USB_OPEN_H / 2,
                          IN_D - 1, IN_D + WALL + 1, USB_OPEN_R))

    # modul DAC u pravé stěny: podpěry + vodítko, deska se může posouvat v ose Y,
    # takže si polohu najde sama podle nosu jacku v otvoru
    dx1 = IN_W - DAC_GAP_SIDE            # hrana desky na straně jacku
    dx0 = dx1 - DAC_W                    # vnitřní hrana desky
    dy0 = DAC_Y0
    dy1 = dy0 + DAC_L
    top = FLOOR + DAC_Z
    # lišta pod vnitřní hranou (mimo pájené vývody lišty na předním konci)
    g.add(body, g.box(dx0 - 0.2, dy0 + 3.5, FLOOR - 0.1, dx0 + 1.8, dy1 - 1.0, top))
    # vodítko – drží desku u stěny, aby nos jacku nevyklouzl z otvoru
    g.add(body, g.box(dx0 - 1.8, dy0 + 3.5, FLOOR - 0.1, dx0 - 0.3, dy1 - 1.0, top + DAC_T + 1.2))
    # malá podpěra u hrany s jackem, na předním konci (jack má vývody na zadním konci)
    g.add(body, g.box(dx1 - 3.0, dy0 + 3.5, FLOOR - 0.1, dx1 - 0.5, dy0 + 7.0, top))

    # otvor pro jack v pravé stěně
    jy = dy1 - JACK_FROM_END
    jz = top + DAC_T + JACK_Z_ABOVE_PCB
    g.sub(body, g.cyl((IN_W - 1, jy, jz), (IN_W + WALL + 1, jy, jz), JACK_HOLE_D))
    if JACK_CBORE_D > JACK_HOLE_D:
        g.sub(body, g.cyl((IN_W + JACK_CBORE_LEFT, jy, jz), (IN_W + WALL + 1, jy, jz), JACK_CBORE_D))
    return body, corners


def build_lid(g, corners):
    z0 = FLOOR + IN_H
    z1 = z0 + LID
    lid = g.rrect_z(-WALL, -WALL, IN_W + WALL, IN_D + WALL, z0, z1, R_OUT)
    for cx, cy in corners:
        g.sub(lid, g.cyl((cx, cy, z0 - 1), (cx, cy, z1 + 1), LID_HOLE_D))
        csk = (LID_CSK_D - LID_HOLE_D) / 2
        g.sub(lid, g.cone((cx, cy, z1 - csk), LID_HOLE_D, (cx, cy, z1 + 0.01), LID_CSK_D))
    fo = BTN_FRAME_IN / 2 + BTN_FRAME_WALL
    fi = BTN_FRAME_IN / 2
    for bx, by in BTN_POS:
        # zahloubení shora = značka a tenká stěna k pozdějšímu provrtání
        g.sub(lid, g.cyl((bx, by, z0 + BTN_SKIN), (bx, by, z1 + 1), BTN_MARK_D))
        # rámeček pro tělo spínače zespodu
        frame = g.box(bx - fo, by - fo, z0 - BTN_FRAME_H, bx + fo, by + fo, z0 + 0.1)
        g.sub(frame, g.box(bx - fi, by - fi, z0 - BTN_FRAME_H - 1, bx + fi, by + fi, z0 + 0.05))
        g.add(lid, frame)
        # sloupky pro přišroubování destičky se spínačem
        for sy in (-1, 1):
            yy = by + sy * BTN_BOSS_DY
            g.add(lid, g.cyl((bx, yy, z0 - BTN_BOSS_H), (bx, yy, z0 + 0.1), BTN_BOSS_D))
            g.sub(lid, g.cyl((bx, yy, z0 - BTN_BOSS_H - 1), (bx, yy, z0 - 0.5), BTN_BOSS_PILOT))
    return lid


def add_component(root, name, tbody):
    occ = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    comp = occ.component
    comp.name = name
    bf = comp.features.baseFeatures.add()
    bf.startEdit()
    comp.bRepBodies.add(tbody, bf)
    bf.finishEdit()
    return occ


def run(context):
    app = adsk.core.Application.get()
    ui = app.userInterface
    try:
        app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        design = adsk.fusion.Design.cast(app.activeProduct)
        design.designType = adsk.fusion.DesignTypes.ParametricDesignType
        root = design.rootComponent
        g = Geo()
        base, corners = build_base(g)
        lid = build_lid(g, corners)
        occ_base = add_component(root, 'Krabicka', base)
        occ_lid = add_component(root, 'Viko', lid)
        msg = 'Krabička a víko vytvořeny.'
        if EXPORT_STL:
            folder = os.path.dirname(os.path.realpath(__file__))
            em = design.exportManager
            for occ, fn in ((occ_base, 'DSPi_krabicka_spodek.stl'), (occ_lid, 'DSPi_krabicka_viko.stl')):
                opt = em.createSTLExportOptions(occ, os.path.join(folder, fn))
                opt.meshRefinement = adsk.fusion.MeshRefinementSettings.MeshRefinementHigh
                em.execute(opt)
            msg += '\nSTL uloženy do: ' + folder
        app.activeViewport.fit()
        ui.messageBox(msg)
    except:
        if ui:
            ui.messageBox('Chyba:\n{}'.format(traceback.format_exc()))
