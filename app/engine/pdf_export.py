"""
PDF character sheet export — Traveller Character Creator.

All coordinates are pixel-matched to the reference character sheet via
pdfplumber extraction (letter = 612×792 pts).

Coordinate system: reportlab bottom-up (y=0 at page bottom).
Reference rect y-values come from pdfplumber's PDF-native bottom-up coords.

Requires: reportlab>=4.2.0  (pip install reportlab)
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
PAGE_BG  = HexColor("#FFFFFF")   # white page background
HDR_BG   = HexColor("#2B1800")   # dark brown — header bars & identity fill
AMBER    = HexColor("#C8930A")   # amber/gold — labels, borders, accents
DIM      = HexColor("#888888")   # muted grey — DM labels, sub-rows
BODY     = HexColor("#111111")   # near-black — main body text & values
FIELD_BG = HexColor("#D8E8F5")   # light blue — input fields & notes area
SUCCESS  = HexColor("#1E7A1E")   # green — ACTIVE, allies, voluntary leave
DANGER   = HexColor("#8A1E1E")   # red  — mishap, debt, enemies
PURPLE   = HexColor("#7B4FBF")   # psionics

# ── Pixel-exact layout constants (RL bottom-up coords) ────────────────────────
# All y-values measured directly from the reference PDF via pdfplumber.
PAGE_W, PAGE_H = letter   # 612 × 792

M = 28   # outer margin (all four sides)

# Fixed section positions — bottom edge (RL y) and height
HDR_Y,  HDR_H  = 740, 24   # "TRAVELLER" title bar        → top at 764
ID_Y,   ID_H   = 682, 52   # identity band                → top at 734
# Chip row inside identity: y=691, h=12 (exact from ref)
CHIP_Y, CHIP_H = 691, 12

CS_Y,   CS_H   = 660, 14   # CHARACTERISTICS section hdr  → top at 674
BOX_H          = 36        # each stat box height
STR_Y          = 624       # STR/DEX/END boxes             → top at 660
INT_Y          = 588       # INT/EDU/SOC boxes             → top at 624

SK_Y,   SK_H   = 568, 14   # SKILLS section header         → top at 582
# Skills content: SK_Y (568) down to NT_Y+NT_H (344) = 224 pt ≈ 17 rows

NT_Y,   NT_H   = 330, 14   # NOTES section header          → top at 344
# Notes content: M (28) up to NT_Y (330) = 302 pt

ROW_H = 13   # content row height (measured from skill line spacing in ref)

# Column geometry (exact from pdfplumber rect extraction)
COL_L_X = M          # left column  x-start  = 28
COL_L_W = 228        # left column  width     → ends at 256
COL_R_X = 266        # right column x-start
COL_R_W = 318        # right column width     → ends at 584

# Identity column x-start positions (from word x0 in reference)
_ID_COL_X = [36, 246, 386]   # label x for NAME / HOMEWORLD / UWP
_ID_COL_W = [210, 136, 198]  # approx widths (sum=544, fits 28→572 with margins)


# ── Low-level helpers ─────────────────────────────────────────────────────────

def _filled_rect(c, x, y, w, h, fill=PAGE_BG, stroke_color=None, lw=0.5):
    c.setFillColor(fill)
    if stroke_color is not None:
        c.setStrokeColor(stroke_color)
        c.setLineWidth(lw)
        c.rect(x, y, w, h, fill=1, stroke=1)
    else:
        c.rect(x, y, w, h, fill=1, stroke=0)


def _section_hdr(c, x, y, w, h, text, font_size=7):
    """Dark-brown header bar with amber ALL-CAPS label."""
    _filled_rect(c, x, y, w, h, fill=HDR_BG)
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
    """Truncate txt until it fits within max_w pts."""
    while txt and c.stringWidth(txt, font, size) > max_w:
        txt = txt[:-1]
    return txt


def _dm_str(score: int) -> str:
    return f"DM {_dice.characteristic_dm(score):+d}"


# ── Fixed page sections ───────────────────────────────────────────────────────

def _draw_page_bg(c):
    """White page background + amber outer border rectangle."""
    _filled_rect(c, 0, 0, PAGE_W, PAGE_H, fill=PAGE_BG)
    c.setStrokeColor(AMBER)
    c.setLineWidth(1)
    c.rect(M, M, PAGE_W - 2 * M, PAGE_H - 2 * M, fill=0, stroke=1)


def _draw_header(c, char):
    """Dark-brown title bar: TRAVELLER left, terms/age right."""
    _filled_rect(c, M, HDR_Y, PAGE_W - 2 * M, HDR_H, fill=HDR_BG)
    # Title
    c.setFillColor(AMBER)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(M + 8, HDR_Y + 5, "TRAVELLER")
    # Right-aligned stats
    c.setFillColor(AMBER)
    c.setFont("Courier", 7)
    right_txt = f"v{char.total_terms}  TERMS  ·  AGE {char.age}"
    c.drawRightString(M + PAGE_W - 2 * M - 6, HDR_Y + 9, right_txt)


def _draw_identity(c, char):
    """
    Identity band (y=682-734):
      row 1 — labels NAME / HOMEWORLD / UWP (amber, small)
      row 2 — light-blue field boxes with values
      row 3 — species/credits/debt chips (exact y from reference: 691, h=12)
    """
    _filled_rect(c, M, ID_Y, PAGE_W - 2 * M, ID_H, fill=HDR_BG)

    labels = ["NAME", "HOMEWORLD", "UWP"]
    values = [char.name or "", char.homeworld or "", char.homeworld_uwp or ""]

    # Labels sit 5pt below identity top
    label_y = ID_Y + ID_H - 12   # ≈ 722  (matches word rl_y 722.7 from ref)
    # Field boxes: from just above chips to just below labels
    field_bot = CHIP_Y + CHIP_H + 2   # 703 + 2 = 705
    field_top = label_y - 1           # 721
    field_h   = field_top - field_bot  # 16

    for i, (lbl, val) in enumerate(zip(labels, values)):
        lx  = _ID_COL_X[i]
        fw  = _ID_COL_W[i] - 4   # small inset

        # Label (amber, bold, small)
        _txt(c, lx, label_y, lbl, color=AMBER, font="Courier-Bold", size=7)

        # Light-blue field box
        _filled_rect(c, lx - 2, field_bot, fw, field_h, fill=FIELD_BG)

        # Value inside field
        if val:
            val_s = _clamp(val, c, "Helvetica-Bold", 9, fw - 6)
            _txt(c, lx, field_bot + 4, val_s, color=BODY, font="Helvetica-Bold", size=9)

    # ── Chip buttons at bottom of band (exact y from reference) ──────────────
    sp      = _rules.species().get(char.species_id, {})
    sp_name = sp.get("name", char.species_id or "Unknown")

    chips = [("SPECIES: " + sp_name, AMBER)]
    chips.append((f"CREDITS: Cr{char.credits:,}", AMBER))
    if char.pension_per_year:
        chips.append((f"PENSION: Cr{char.pension_per_year:,}/yr", SUCCESS))
    if char.medical_debt:
        chips.append((f"MED DEBT: Cr{char.medical_debt:,}", DANGER))

    x   = _ID_COL_X[0]   # = 36, matches ref
    fnt, fsz = "Courier-Bold", 7
    for chip_txt, col in chips:
        tw = c.stringWidth(chip_txt, fnt, fsz)
        cw = tw + 10
        if x + cw > PAGE_W - M - 4:
            break
        # Dark-bg bordered chip
        c.setFillColor(HDR_BG)
        c.setStrokeColor(AMBER)
        c.setLineWidth(0.6)
        c.rect(x, CHIP_Y, cw, CHIP_H, fill=1, stroke=1)
        c.setFillColor(col)
        c.setFont(fnt, fsz)
        c.drawString(x + 5, CHIP_Y + 3, chip_txt)
        x += cw + 6


def _draw_characteristics(c, char):
    """2×3 stat boxes in the left column — exact reference positions."""
    _section_hdr(c, COL_L_X, CS_Y, COL_L_W, CS_H, "CHARACTERISTICS")

    box_w = COL_L_W / 3  # = 76 pt (exact match to reference)
    for stats, row_y in [(("STR", "DEX", "END"), STR_Y),
                         (("INT", "EDU", "SOC"), INT_Y)]:
        for col_i, stat in enumerate(stats):
            bx = COL_L_X + col_i * box_w

            # Box with amber border on white background
            _filled_rect(c, bx, row_y, box_w, BOX_H, fill=PAGE_BG,
                         stroke_color=AMBER, lw=0.5)

            val = char.characteristics.get(stat)

            # Stat name — small, dim, centred, top of box
            _txt(c, bx + box_w / 2, row_y + BOX_H - 11,
                 stat, color=DIM, font="Courier-Bold", size=7, align="center")

            # Value — large, dark, centred
            _txt(c, bx + box_w / 2, row_y + BOX_H - 26,
                 str(val), color=BODY, font="Helvetica-Bold", size=17,
                 align="center")

            # DM — small, dim, centred, bottom of box
            _txt(c, bx + box_w / 2, row_y + 3,
                 _dm_str(val), color=DIM, font="Courier", size=7, align="center")

    # PSI if tested
    if getattr(char, "psi", None):
        _txt(c, COL_L_X + 4, INT_Y - 11,
             f"PSI  {char.psi}   DM {_dice.characteristic_dm(char.psi):+d}",
             color=PURPLE, size=7)


def _draw_skills(c, char):
    """
    Skills list in the left column.
    Content area: SK_Y (568) down to NT_Y+NT_H (344) = 224 pt ≈ 17 rows.
    Row height 13 pt (measured from reference line spacing).
    """
    _section_hdr(c, COL_L_X, SK_Y, COL_L_W, SK_H, "SKILLS")

    bot_y  = NT_Y + NT_H        # 344 — stop above NOTES header
    y      = SK_Y - ROW_H + 3   # first row baseline (≈ 558 → matches ref 556.4)

    skills = sorted(
        char.skills,
        key=lambda s: (s.name.lower(), (s.speciality or "").lower()),
    )

    for sk in skills:
        if y < bot_y + 2:
            break
        display = f"{sk.name} ({sk.speciality})" if sk.speciality else sk.name
        display = _clamp(display, c, "Courier", 8, COL_L_W - 20)

        _txt(c, COL_L_X + 4, y, display, color=BODY, size=8)
        _txt(c, COL_L_X + COL_L_W - 4, y, str(sk.level),
             color=BODY, font="Courier-Bold", size=8, align="right")
        _hline(c, COL_L_X, y - ROW_H + 1, COL_L_W)   # separator below row
        y -= ROW_H


def _draw_notes(c, char):
    """Full-width NOTES section at the bottom."""
    _section_hdr(c, M, NT_Y, PAGE_W - 2 * M, NT_H, "NOTES")

    # Light-blue content area from bottom margin up to notes header
    _filled_rect(c, M, M, PAGE_W - 2 * M, NT_Y - M,
                 fill=FIELD_BG, stroke_color=AMBER, lw=0.5)

    notes = (getattr(char, "user_notes", None) or "").strip()
    if not notes:
        return

    c.setFont("Courier", 7)
    c.setFillColor(BODY)
    avail_w  = PAGE_W - 2 * M - 8
    max_char = int(avail_w / 4.15)
    y        = NT_Y - 10

    for raw in notes.split("\n"):
        line = raw
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


# ── Right column (dynamic, stacks sections top-down) ─────────────────────────

class _RC:
    """
    Right-column renderer.  Starts at y = CS_Y + CS_H (674) — same height as
    the CHARACTERISTICS header top — and renders sections downward.
    Each section header is 14pt; content rows are ROW_H (13pt) each.
    Stops before the NOTES header (NT_Y + NT_H = 344).
    """

    def __init__(self, c, top_y: float):
        self.c   = c
        self.y   = top_y           # current y (decrements as sections are drawn)
        self.bot = NT_Y + NT_H     # 344 — never draw below this

    # ── primitives ─────────────────────────────────────────────────────────

    def _hdr(self, text: str, h: int = 14) -> bool:
        if self.y - h < self.bot:
            return False
        _section_hdr(self.c, COL_R_X, self.y - h, COL_R_W, h, text)
        self.y -= h
        return True

    def _row(self, label: str, value: str, val_color=BODY, dim_label: bool = True):
        if self.y < self.bot + ROW_H:
            return
        y  = self.y - ROW_H + 3
        lc = DIM if dim_label else BODY
        _txt(self.c, COL_R_X + 4, y, str(label), color=lc, size=8)
        vs = _clamp(str(value), self.c, "Courier-Bold", 8, COL_R_W - 80)
        _txt(self.c, COL_R_X + COL_R_W - 4, y, vs,
             color=val_color, font="Courier-Bold", size=8, align="right")
        _hline(self.c, COL_R_X, y - ROW_H + 1, COL_R_W)
        self.y -= ROW_H

    def _line(self, text: str, color=DIM, indent: int = 4, size: float = 7):
        if self.y < self.bot + ROW_H:
            return
        t = _clamp(str(text), self.c, "Courier", size, COL_R_W - indent - 4)
        _txt(self.c, COL_R_X + indent, self.y - ROW_H + 3,
             t, color=color, size=size)
        _hline(self.c, COL_R_X, self.y - ROW_H + 1, COL_R_W)
        self.y -= ROW_H

    def _gap(self, h: int = 4):
        self.y -= h

    # ── section renderers ───────────────────────────────────────────────────

    def careers(self, char):
        if not self._hdr("CAREER HISTORY"):
            return
        for cc in char.completed_careers:
            if self.y < self.bot + ROW_H * 2:
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
            leave = cc.left_due_to or ""
            self._line(f"{rt}  ·  {leave}", color=DIM, indent=8, size=7)

    def associates(self, char):
        if not self._hdr("ASSOCIATES"):
            return
        counts: dict[str, int] = {}
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
            note = (eq.notes or "").strip() or "From mustering out"
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

    # Thin vertical divider between left and right columns
    c.setStrokeColor(AMBER)
    c.setLineWidth(0.3)
    divider_x = (COL_L_X + COL_L_W + COL_R_X) / 2   # midpoint of gap = 261
    c.line(divider_x, CS_Y + CS_H, divider_x, NT_Y + NT_H)

    # Right column — starts at same height as CHARACTERISTICS header top
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
