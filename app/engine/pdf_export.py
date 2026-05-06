"""
PDF character sheet export — Traveller Character Creator.

Layout pixel-matched to the reference character sheet (letter, 612×792 pts).
All coordinates are in reportlab's bottom-up system (y=0 at bottom of page).

Requires: reportlab  (pip install reportlab)
"""

from __future__ import annotations
import io
from typing import TYPE_CHECKING

from reportlab.lib.pagesizes import letter
from reportlab.lib.colors import HexColor
from reportlab.pdfgen import canvas as rl_canvas

if TYPE_CHECKING:
    from .character import Character

from . import rules as _rules, dice as _dice

# ── Palette ───────────────────────────────────────────────────────────────────
# Matches the reference PDF: light/white page, dark-brown headers, amber accents
PAGE_BG   = HexColor("#FFFFFF")   # white page background
HDR_BG    = HexColor("#2B1800")   # dark brown — header bars & identity bg
AMBER     = HexColor("#C8930A")   # amber/gold — labels, borders, accents
DIM       = HexColor("#888888")   # muted — DM labels, rank text, dim rows
BODY      = HexColor("#111111")   # near-black — main body text & numbers
FIELD_BG  = HexColor("#D8E8F5")   # light blue — input fields & notes area
SUCCESS   = HexColor("#1E7A1E")   # green — ACTIVE, allies, voluntary
DANGER    = HexColor("#8A1E1E")   # red  — mishap, debt, enemies
PURPLE    = HexColor("#7B4FBF")   # psionics

# ── Page layout (bottom-up coords) ───────────────────────────────────────────
PAGE_W, PAGE_H = letter  # 612 × 792

M = 28  # outer margin (all sides)

# Column geometry
COL_GAP = 10
COL_L_X = M             # left column  x-start =  28
COL_L_W = 228           # left column  width   → ends at 256
COL_R_X = M + COL_L_W + COL_GAP  # right column x-start = 266
COL_R_W = PAGE_W - M - COL_R_X   # right column width   = 318

# Section y positions (bottom edge of the rect, reportlab convention)
HDR_Y,  HDR_H  = 736, 28   # "TRAVELLER" title bar      → top at 764
ID_Y,   ID_H   = 670, 62   # identity band              → top at 732
CS_Y,   CS_H   = 652, 14   # CHARACTERISTICS header     → top at 666
BOX_H          = 38        # each stat box height
STR_Y          = CS_Y - BOX_H        # = 614  first stat row
INT_Y          = STR_Y - BOX_H       # = 576  second stat row
SK_Y,   SK_H   = INT_Y - 18, 14      # SKILLS header: 14 pt header + 4 pt gap below INT row
# Skills list descends from SK_Y to NT_Y+NT_H

NT_Y,   NT_H   = 140, 14   # NOTES section header
# Notes content area: y=M (28) to NT_Y (140), height 112 pt


# ── Drawing helpers ───────────────────────────────────────────────────────────

def _rect(c, x, y, w, h, fill=PAGE_BG, stroke=None, lw=0.5):
    c.setFillColor(fill)
    if stroke is not None:
        c.setStrokeColor(stroke)
        c.setLineWidth(lw)
        c.rect(x, y, w, h, fill=1, stroke=1)
    else:
        c.rect(x, y, w, h, fill=1, stroke=0)


def _section_hdr(c, x, y, w, h, text, font_size=7):
    """Dark brown header bar with amber ALL-CAPS label."""
    _rect(c, x, y, w, h, fill=HDR_BG)
    c.setFillColor(AMBER)
    c.setFont("Courier-Bold", font_size)
    c.drawString(x + 5, y + (h - font_size) / 2 + 1, text)


def _txt(c, x, y, txt, color=BODY, font="Courier", size=8, align="left"):
    c.setFillColor(color)
    c.setFont(font, size)
    s = str(txt)
    if align == "right":
        c.drawRightString(x, y, s)
    elif align == "center":
        c.drawCentredString(x, y, s)
    else:
        c.drawString(x, y, s)


def _hline(c, x, y, w, color=AMBER, lw=0.3):
    c.setStrokeColor(color)
    c.setLineWidth(lw)
    c.line(x, y, x + w, y)


def _clamp(txt: str, c, font: str, size: float, max_w: float) -> str:
    while txt and c.stringWidth(txt, font, size) > max_w:
        txt = txt[:-1]
    return txt


def _dm_str(score: int) -> str:
    return f"DM {_dice.characteristic_dm(score):+d}"


# ── Fixed page sections ───────────────────────────────────────────────────────

def _draw_page_bg(c):
    """White page with amber outer border rectangle."""
    _rect(c, 0, 0, PAGE_W, PAGE_H, fill=PAGE_BG)
    c.setStrokeColor(AMBER)
    c.setLineWidth(1)
    c.rect(M, M, PAGE_W - 2 * M, PAGE_H - 2 * M, fill=0, stroke=1)


def _draw_header(c, char):
    """Dark brown title bar: "TRAVELLER" left, terms/age right."""
    _rect(c, M, HDR_Y, PAGE_W - 2 * M, HDR_H, fill=HDR_BG)

    c.setFillColor(AMBER)
    c.setFont("Helvetica-Bold", 18)
    c.drawString(M + 8, HDR_Y + 6, "TRAVELLER")

    c.setFillColor(AMBER)
    c.setFont("Courier", 8)
    right = f"v{char.total_terms}  TERMS  ·  AGE {char.age}"
    c.drawRightString(M + PAGE_W - 2 * M - 8, HDR_Y + 10, right)


def _draw_identity(c, char):
    """
    Identity band:
      - Dark brown background for the whole band
      - Row 1: NAME / HOMEWORLD / UWP  labels + light-blue input boxes
      - Row 2: SPECIES and CREDITS bordered chips
    """
    full_w = PAGE_W - 2 * M
    _rect(c, M, ID_Y, full_w, ID_H, fill=HDR_BG)

    # ── Three label+field columns ──────────────────────────────────
    col_w   = full_w / 3
    field_h = 18
    # Label sits near the top of the band
    label_y = ID_Y + ID_H - 13
    # Field box sits below the label
    field_y = label_y - field_h - 1

    labels = ["NAME", "HOMEWORLD", "UWP"]
    values = [char.name or "", char.homeworld or "", char.homeworld_uwp or ""]

    for i, (lbl, val) in enumerate(zip(labels, values)):
        lx  = M + 4 + i * col_w
        fw  = col_w - 8

        # Label text
        _txt(c, lx, label_y, lbl, color=AMBER, font="Courier-Bold", size=7)

        # Light-blue field box
        _rect(c, lx, field_y, fw, field_h, fill=FIELD_BG)

        # Value inside the field
        if val:
            val_s = _clamp(val, c, "Helvetica-Bold", 10, fw - 6)
            _txt(c, lx + 3, field_y + 5, val_s, color=BODY, font="Helvetica-Bold", size=10)

    # ── Chips row at the bottom of identity band ───────────────────
    chip_y = ID_Y + 3
    chip_h = 13

    sp      = _rules.species().get(char.species_id, {})
    sp_name = sp.get("name", char.species_id or "Unknown")

    chips = [("SPECIES: " + sp_name, AMBER)]
    chips.append((f"CREDITS: Cr{char.credits:,}", AMBER))
    if char.pension_per_year:
        chips.append((f"PENSION: Cr{char.pension_per_year:,}/yr", SUCCESS))
    if char.medical_debt:
        chips.append((f"MED DEBT: Cr{char.medical_debt:,}", DANGER))
    if char.ship_shares:
        chips.append((f"SHIP SHARES: {char.ship_shares}", AMBER))

    x = M + 4
    font, fsize = "Courier-Bold", 7
    for chip_txt, col in chips:
        tw = c.stringWidth(chip_txt, font, fsize)
        cw = tw + 10
        if x + cw > PAGE_W - M - 4:
            break
        # bordered chip on dark background
        c.setFillColor(HDR_BG)
        c.setStrokeColor(AMBER)
        c.setLineWidth(0.6)
        c.rect(x, chip_y, cw, chip_h, fill=1, stroke=1)
        c.setFillColor(col)
        c.setFont(font, fsize)
        c.drawString(x + 5, chip_y + 3, chip_txt)
        x += cw + 6


def _draw_characteristics(c, char):
    """2 × 3 stat boxes in the left column."""
    _section_hdr(c, COL_L_X, CS_Y, COL_L_W, CS_H, "CHARACTERISTICS")

    box_w = COL_L_W / 3  # ≈ 76 pt
    for stats, row_y in [(("STR", "DEX", "END"), STR_Y),
                         (("INT", "EDU", "SOC"), INT_Y)]:
        for col_i, stat in enumerate(stats):
            bx = COL_L_X + col_i * box_w

            # Box with amber border
            _rect(c, bx, row_y, box_w, BOX_H, fill=PAGE_BG, stroke=AMBER, lw=0.5)

            val = char.characteristics.get(stat)

            # Stat name — small, dim, centred near top
            _txt(c, bx + box_w / 2, row_y + BOX_H - 11,
                 stat, color=DIM, font="Courier-Bold", size=7, align="center")

            # Value — large, dark, centred
            _txt(c, bx + box_w / 2, row_y + BOX_H - 27,
                 str(val), color=BODY, font="Helvetica-Bold", size=18, align="center")

            # DM — small, dim, centred near bottom
            _txt(c, bx + box_w / 2, row_y + 3,
                 _dm_str(val), color=DIM, font="Courier", size=7, align="center")

    # PSI if tested
    if getattr(char, "psi", None):
        _txt(c, COL_L_X + 4, INT_Y - 12,
             f"PSI  {char.psi}   DM {_dice.characteristic_dm(char.psi):+d}",
             color=PURPLE, size=7)


def _draw_skills(c, char):
    """Skills list below characteristics, left column."""
    _section_hdr(c, COL_L_X, SK_Y, COL_L_W, SK_H, "SKILLS")

    row_h = 10
    y     = SK_Y - row_h + 2          # first row baseline
    bot_y = NT_Y + NT_H + 2           # stop above notes header

    skills = sorted(
        char.skills,
        key=lambda s: (s.name.lower(), (s.speciality or "").lower()),
    )

    for sk in skills:
        if y < bot_y:
            break
        display = f"{sk.name} ({sk.speciality})" if sk.speciality else sk.name
        display = _clamp(display, c, "Courier", 8, COL_L_W - 20)

        _txt(c, COL_L_X + 4, y, display, color=BODY, size=8)
        _txt(c, COL_L_X + COL_L_W - 4, y, str(sk.level),
             color=BODY, font="Courier-Bold", size=8, align="right")
        _hline(c, COL_L_X, y - 2, COL_L_W)
        y -= row_h


def _draw_notes(c, char):
    """Full-width NOTES section at the bottom of the page."""
    _section_hdr(c, M, NT_Y, PAGE_W - 2 * M, NT_H, "NOTES")

    # Light-blue content area
    content_h = NT_Y - M
    _rect(c, M, M, PAGE_W - 2 * M, content_h, fill=FIELD_BG, stroke=AMBER, lw=0.5)

    notes = (char.user_notes or "").strip()
    if not notes:
        return

    c.setFont("Courier", 7)
    c.setFillColor(BODY)
    avail_w  = PAGE_W - 2 * M - 8
    max_char = int(avail_w / 4.2)
    y        = NT_Y - 10

    for raw_line in notes.split("\n"):
        line = raw_line
        while len(line) > max_char:
            c.drawString(M + 4, y, line[:max_char])
            line = line[max_char:]
            y -= 9
            if y < M + 4:
                return
        c.drawString(M + 4, y, line)
        y -= 9
        if y < M + 4:
            return


# ── Right column ──────────────────────────────────────────────────────────────

class _RC:
    """
    Stateful right-column renderer.
    Tracks current y position and draws sections from top down.
    """
    ROW_H = 11

    def __init__(self, c, top_y: float):
        self.c   = c
        self.y   = top_y
        self.bot = NT_Y + NT_H + 2   # stop above notes header

    # ── internal primitives ─────────────────────────────────────────

    def _hdr(self, text: str, h: int = 14) -> bool:
        """Draw a section header bar. Returns False if no room."""
        if self.y - h < self.bot:
            return False
        _section_hdr(self.c, COL_R_X, self.y - h, COL_R_W, h, text)
        self.y -= h
        return True

    def _row(self, label: str, value: str, val_color=BODY, dim_label: bool = True):
        """Single key/value row with trailing hairline."""
        if self.y < self.bot + self.ROW_H:
            return
        y = self.y - self.ROW_H + 3
        lc = DIM if dim_label else BODY
        _txt(self.c, COL_R_X + 4, y, str(label), color=lc, size=8)
        vs = _clamp(str(value), self.c, "Courier-Bold", 8, COL_R_W - 80)
        _txt(self.c, COL_R_X + COL_R_W - 4, y, vs,
             color=val_color, font="Courier-Bold", size=8, align="right")
        _hline(self.c, COL_R_X, y - 2, COL_R_W)
        self.y -= self.ROW_H

    def _line(self, text: str, color=DIM, indent: int = 4, size: float = 7):
        """Single free-text line with trailing hairline."""
        if self.y < self.bot + self.ROW_H:
            return
        t = _clamp(str(text), self.c, "Courier", size, COL_R_W - indent - 4)
        _txt(self.c, COL_R_X + indent, self.y - self.ROW_H + 3, t,
             color=color, size=size)
        _hline(self.c, COL_R_X, self.y - self.ROW_H, COL_R_W)
        self.y -= self.ROW_H

    def _gap(self, h: int = 4):
        self.y -= h

    # ── section renderers ───────────────────────────────────────────

    def careers(self, char):
        if not self._hdr("CAREER HISTORY"):
            return
        for cc in char.completed_careers:
            if self.y < self.bot + self.ROW_H * 2:
                break
            cd  = _rules.careers().get(cc.career_id, {})
            an  = (cd.get("assignments", {})
                     .get(cc.assignment_id, {})
                     .get("name", cc.assignment_id))
            cn  = cd.get("name", cc.career_id)
            col = DANGER if cc.left_due_to == "mishap" else BODY
            self._row(f"{cn} / {an}", f"{cc.terms_served}t",
                      val_color=col, dim_label=False)
            rt    = cc.final_rank_title or f"Rank {cc.final_rank}"
            leave = cc.left_due_to or "—"
            self._line(f"{rt}  —  {leave}", color=DIM, indent=8, size=7)

    def associates(self, char):
        if not self._hdr("ASSOCIATES"):
            return
        counts = {}
        for a in char.associates:
            counts[a.kind] = counts.get(a.kind, 0) + 1
        if not counts:
            self._line("No associates", color=DIM)
            return
        colors = {"ally": SUCCESS, "contact": BODY, "rival": AMBER, "enemy": DANGER}
        for kind in ("ally", "contact", "rival", "enemy"):
            n = counts.get(kind, 0)
            if n:
                self._row(kind.title() + ("s" if n != 1 else ""), str(n),
                          val_color=colors[kind])

    def equipment(self, char):
        items       = char.equipment
        ship_shares = getattr(char, "ship_shares", 0)
        if not items and not ship_shares:
            return
        if not self._hdr("EQUIPMENT"):
            return
        if ship_shares:
            n = ship_shares
            self._row(f"Ship Share{'s' if n != 1 else ''}", str(n),
                      val_color=AMBER, dim_label=False)
        for eq in items[:12]:
            note = eq.notes if eq.notes else "From mustering out"
            self._row(eq.name, note, val_color=DIM, dim_label=False)

    def species_traits(self, char):
        traits = char.traits
        if not traits:
            return
        if not self._hdr("SPECIES TRAITS"):
            return
        for t in traits:
            name = t.get("name", "") if isinstance(t, dict) else str(t)
            desc = t.get("description", "") if isinstance(t, dict) else ""
            self._line(name, color=AMBER, indent=4, size=8)
            if desc:
                words, line = desc.split(), ""
                max_w = COL_R_W - 16
                for word in words:
                    trial = (line + " " + word).strip()
                    if self.c.stringWidth(trial, "Courier", 7) > max_w:
                        if line:
                            self._line(line, color=DIM, indent=8, size=7)
                        line = word
                    else:
                        line = trial
                if line:
                    self._line(line, color=DIM, indent=8, size=7)

    def anagathics(self, char):
        if not getattr(char, "anagathics_active", False) and \
           not getattr(char, "anagathics_addicted", False):
            return
        if not self._hdr("ANAGATHICS"):
            return
        status = "ACTIVE" if char.anagathics_active else "STOPPED"
        col    = SUCCESS if char.anagathics_active else DANGER
        self._row("Status", status, val_color=col)
        self._row("Terms on treatment", str(char.anagathics_terms_used))
        self._row("Aging DM bonus", f"+{char.anagathics_terms_used}")
        if char.medical_debt and char.anagathics_terms_used:
            self._row("Accrued medical debt", f"Cr{char.medical_debt:,}",
                      val_color=DANGER)

    def psionics(self, char):
        if not getattr(char, "psi_tested", False):
            return
        if not self._hdr("PSIONICS"):
            return
        self._row("PSI", str(char.psi), val_color=PURPLE)
        for talent in getattr(char, "psi_trained_talents", []):
            self._line(f"  {talent}", color=PURPLE, size=7)

    def home_forces(self, char):
        if not getattr(char, "home_forces_enrolled", False):
            return
        if not self._hdr("HOME FORCES RESERVES"):
            return
        comp = (char.home_forces_component or "groundside").replace("_", " ").title()
        self._row("Component", comp)
        self._row("Reserve Rank", str(char.home_forces_rank))

    def solsec(self, char):
        if not getattr(char, "solsec_monitor", False):
            return
        if not self._hdr("SOLSEC MONITOR"):
            return
        self._row("Monitor Rank", str(char.solsec_monitor_rank))


# ── Main entry point ──────────────────────────────────────────────────────────

def generate_pdf(char: "Character") -> bytes:
    """Render the character sheet and return raw PDF bytes."""
    buf = io.BytesIO()
    c   = rl_canvas.Canvas(buf, pagesize=letter)

    _draw_page_bg(c)
    _draw_header(c, char)
    _draw_identity(c, char)
    _draw_characteristics(c, char)
    _draw_skills(c, char)
    _draw_notes(c, char)

    # Thin vertical divider between the two columns
    c.setStrokeColor(AMBER)
    c.setLineWidth(0.3)
    divider_x = COL_R_X - COL_GAP // 2
    c.line(divider_x, CS_Y + CS_H, divider_x, NT_Y + NT_H)

    # Right column — top aligned with CHARACTERISTICS header
    rc = _RC(c, CS_Y + CS_H)
    rc.careers(char)
    rc._gap(4)
    rc.associates(char)
    rc._gap(4)
    rc.equipment(char)
    rc._gap(4)
    rc.species_traits(char)
    rc._gap(4)
    rc.anagathics(char)
    rc._gap(4)
    rc.psionics(char)
    rc._gap(4)
    rc.home_forces(char)
    rc._gap(4)
    rc.solsec(char)

    c.save()
    return buf.getvalue()
