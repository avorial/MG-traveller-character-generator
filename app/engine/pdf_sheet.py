"""
Fillable PDF character sheet generator.

Produces a print-ready, US-Letter PDF that mirrors the web-UI character
sheet.  Name, Homeworld, UWP, and Notes are live AcroForm text fields so
players can edit them after printing to PDF / in Acrobat.
All other data is pre-populated from the character JSON.

Usage:
    from .pdf_sheet import generate_character_pdf
    pdf_bytes = generate_character_pdf(character)
"""

import io
import math
from typing import Optional

from reportlab.lib.pagesizes import letter
from reportlab.lib.colors import Color, HexColor, black, white
from reportlab.pdfgen import canvas as rl_canvas

from .character import Character

# ── palette (amber CRT aesthetic, print-safe) ────────────────────────────────
C_BG        = HexColor("#FDFAF5")   # off-white page background
C_PANEL     = HexColor("#2B1F12")   # dark amber-brown header bars
C_PANEL_MID = HexColor("#3D2F1F")   # mid-tone for sub-headers
C_ACCENT    = HexColor("#FFB347")   # amber accent
C_TEXT      = HexColor("#1A1208")   # near-black body text
C_MUTED     = HexColor("#7A6040")   # muted label text
C_BORDER    = HexColor("#C8A870")   # light amber border
C_DANGER    = HexColor("#C0392B")   # medical-debt red
C_SUCCESS   = HexColor("#2E7D32")   # positive green
C_FIELD_BG  = HexColor("#FFFBF0")   # very light amber for fillable fields

# ── page geometry ─────────────────────────────────────────────────────────────
W, H        = letter                 # 612 × 792 pt
MARGIN      = 28                     # outer margin (pt)
COL_GAP     = 10                     # gap between columns
COL_L_W     = 228                    # left-column width (skills / characteristics)
COL_R_W     = W - 2 * MARGIN - COL_L_W - COL_GAP   # right column fills the rest
ROW_H       = 13                     # standard row height
SECTION_PAD = 6                      # padding inside sections

# ── fonts ─────────────────────────────────────────────────────────────────────
FONT_BODY   = "Helvetica"
FONT_BOLD   = "Helvetica-Bold"
FONT_MONO   = "Courier"


# ── helper: Traveller DM ──────────────────────────────────────────────────────
def char_dm(score: int) -> int:
    if score <= 0:  return -3
    if score <= 2:  return -2
    if score <= 5:  return -1
    if score <= 8:  return  0
    if score <= 11: return  1
    if score <= 14: return  2
    return 3


def fmt_dm(dm: int) -> str:
    return f"+{dm}" if dm >= 0 else str(dm)


# ── noble title (Imperial only) ───────────────────────────────────────────────
_IMPERIAL_SPECIES = {
    "imperial_human", "imperial_aslan", "imperial_vargr", "imperial_bwap",
    "hierate_aslan", "frontier_human", "luriani", "jonkeereen",
}
_NOBLE_TITLES = {11: "Knight", 12: "Baronet", 13: "Baron", 14: "Marquis", 15: "Count"}


def noble_title(society_id: str, species_id: str, soc: int) -> Optional[str]:
    imperial = society_id in ("third_imperium", "") or species_id in _IMPERIAL_SPECIES
    if not imperial:
        return None
    if soc > 15:
        return "Archduke"
    return _NOBLE_TITLES.get(soc)


# ─────────────────────────────────────────────────────────────────────────────
# Drawing primitives
# ─────────────────────────────────────────────────────────────────────────────

class SheetCanvas:
    """Thin wrapper around ReportLab canvas with helpers for the sheet layout."""

    def __init__(self, buf: io.BytesIO, title: str = "Traveller Character Sheet"):
        self.c = rl_canvas.Canvas(buf, pagesize=letter)
        self.c.setTitle(title)
        self.c.setAuthor("Traveller Character Creator")
        self.c.setSubject("MgT 2e Character Sheet")
        # current y-position (top of page = H - MARGIN)
        self.y = H - MARGIN
        self._page = 1

    # ── page management ──────────────────────────────────────────────────────

    def new_page(self):
        self.c.showPage()
        self._page += 1
        self.y = H - MARGIN
        self._draw_page_bg()

    def _draw_page_bg(self):
        self.c.setFillColor(C_BG)
        self.c.rect(0, 0, W, H, stroke=0, fill=1)

    def save(self):
        self.c.save()

    # ── low-level drawing ────────────────────────────────────────────────────

    def rect_filled(self, x, y, w, h, fill: Color, stroke: Optional[Color] = None,
                    stroke_width: float = 0.5):
        self.c.setFillColor(fill)
        if stroke:
            self.c.setStrokeColor(stroke)
            self.c.setLineWidth(stroke_width)
            self.c.rect(x, y, w, h, stroke=1, fill=1)
        else:
            self.c.rect(x, y, w, h, stroke=0, fill=1)

    def line(self, x1, y1, x2, y2, color: Color = C_BORDER, width: float = 0.5):
        self.c.setStrokeColor(color)
        self.c.setLineWidth(width)
        self.c.line(x1, y1, x2, y2)

    def text(self, x, y, s: str, font=FONT_BODY, size=8, color: Color = C_TEXT,
             align="left", max_width: Optional[float] = None):
        """Draw a single text string. y is the baseline."""
        s = str(s)
        if max_width:
            # truncate to fit
            while self.c.stringWidth(s, font, size) > max_width and len(s) > 1:
                s = s[:-1]
            if len(s) < len(str(s)):
                s = s[:-1] + "…"
        self.c.setFont(font, size)
        self.c.setFillColor(color)
        if align == "right":
            self.c.drawRightString(x, y, s)
        elif align == "center":
            self.c.drawCentredString(x, y, s)
        else:
            self.c.drawString(x, y, s)

    def wrapped_text(self, x, y, s: str, max_width: float, font=FONT_BODY,
                     size: float = 8, color: Color = C_TEXT, line_height: float = 10) -> float:
        """Draw multi-line wrapped text. Returns the y after the last line."""
        from reportlab.lib.utils import simpleSplit
        lines = simpleSplit(s, font, size, max_width)
        self.c.setFont(font, size)
        self.c.setFillColor(color)
        for ln in lines:
            self.c.drawString(x, y, ln)
            y -= line_height
        return y

    # ── acroform fillable field ───────────────────────────────────────────────

    def text_field(self, name: str, x, y, w, h, value: str = "",
                   font_size: float = 9, multiline: bool = False):
        """Add a fillable AcroForm text field."""
        form = self.c.acroForm
        flags = "multiline" if multiline else ""
        form.textfield(
            name=name,
            tooltip=name,
            x=x, y=y,
            width=w, height=h,
            value=value,
            fontSize=font_size,
            fontName=FONT_BODY,
            fillColor=C_FIELD_BG,
            borderColor=C_BORDER,
            borderWidth=0.5,
            textColor=C_TEXT,
            fieldFlags=flags,
            relative=False,
        )

    # ── higher-level section primitives ──────────────────────────────────────

    def section_header(self, x, y, w, label: str) -> float:
        """Draw a dark header bar. Returns the y just below it."""
        BAR_H = 14
        self.rect_filled(x, y - BAR_H, w, BAR_H, C_PANEL)
        self.text(x + 5, y - BAR_H + 4, label.upper(), font=FONT_BOLD, size=7,
                  color=C_ACCENT)
        return y - BAR_H

    def row_pair(self, x, y, w, label: str, value: str,
                 label_w: float = 0.52, danger: bool = False,
                 value_color: Optional[Color] = None) -> float:
        """One label+value row inside a section. Returns the y after the row."""
        ROW = ROW_H
        # alternating row background handled by caller if desired
        lw = w * label_w
        self.text(x + 4, y - ROW + 3, label, font=FONT_BODY, size=7.5, color=C_MUTED,
                  max_width=lw - 6)
        vc = value_color or (C_DANGER if danger else C_TEXT)
        self.text(x + lw, y - ROW + 3, str(value), font=FONT_BOLD, size=7.5,
                  color=vc, max_width=w - lw - 4)
        self.line(x, y - ROW, x + w, y - ROW, C_BORDER, 0.3)
        return y - ROW

    def skill_row(self, x, y, w, label: str, level_or_right: str,
                  italic: bool = False) -> float:
        """Skill / career row with name left and level right. Returns y after."""
        ROW = ROW_H
        font = FONT_BODY
        label_w = w - 22
        self.text(x + 4, y - ROW + 3, label, font=font, size=7.5, color=C_TEXT,
                  max_width=label_w)
        self.text(x + w - 4, y - ROW + 3, str(level_or_right), font=FONT_BOLD,
                  size=7.5, color=C_TEXT, align="right")
        self.line(x, y - ROW, x + w, y - ROW, C_BORDER, 0.3)
        return y - ROW

    def ensure_space(self, needed: float, x: float, w: float,
                     col_x_r: float, col_w_r: float, right_y: float) -> float:
        """If self.y < needed, start a new page and reset y. Returns right_y unchanged."""
        if self.y < MARGIN + needed:
            self.new_page()
        return right_y


# ─────────────────────────────────────────────────────────────────────────────
# Main entry point
# ─────────────────────────────────────────────────────────────────────────────

def generate_character_pdf(char: Character) -> bytes:
    """Return the PDF as raw bytes."""
    buf = io.BytesIO()
    sheet = SheetCanvas(buf, title=f"{char.name or 'Traveller'} — Character Sheet")
    c = sheet.c

    # page background
    sheet._draw_page_bg()

    # ── master title bar ──────────────────────────────────────────────────────
    TITLE_H = 24
    sheet.rect_filled(MARGIN, H - MARGIN - TITLE_H, W - 2 * MARGIN, TITLE_H, C_PANEL)
    sheet.text(MARGIN + 8, H - MARGIN - TITLE_H + 8, "TRAVELLER", font=FONT_BOLD,
               size=14, color=C_ACCENT)
    sheet.text(W - MARGIN - 8, H - MARGIN - TITLE_H + 8,
               f"v{char.total_terms} TERMS  ·  AGE {char.age}",
               font=FONT_BODY, size=8, color=C_MUTED, align="right")

    # track y below the title bar
    y_top = H - MARGIN - TITLE_H - 6   # 6 pt gap

    # ── HEADER — name / homeworld / uwp / meta ────────────────────────────────
    HDR_H = 52
    sheet.rect_filled(MARGIN, y_top - HDR_H, W - 2 * MARGIN, HDR_H,
                      C_PANEL_MID, C_BORDER)

    # Name field (fillable)
    NAME_W = 200
    sheet.text(MARGIN + 8, y_top - 10, "NAME", font=FONT_BOLD, size=6.5, color=C_ACCENT)
    sheet.text_field("Name", MARGIN + 8, y_top - HDR_H + 22, NAME_W, 14,
                     value=char.name or "", font_size=10)

    # Homeworld field
    HW_X = MARGIN + 8 + NAME_W + 10
    HW_W = 130
    sheet.text(HW_X, y_top - 10, "HOMEWORLD", font=FONT_BOLD, size=6.5, color=C_ACCENT)
    sheet.text_field("Homeworld", HW_X, y_top - HDR_H + 22, HW_W, 14,
                     value=char.homeworld or "", font_size=9)

    # UWP field
    UWP_X = HW_X + HW_W + 10
    UWP_W = 96
    sheet.text(UWP_X, y_top - 10, "UWP", font=FONT_BOLD, size=6.5, color=C_ACCENT)
    sheet.text_field("UWP", UWP_X, y_top - HDR_H + 22, UWP_W, 14,
                     value=char.homeworld_uwp or "", font_size=9)

    # Meta pills (species / credits / noble title)
    meta_x = MARGIN + 8
    meta_y = y_top - HDR_H + 10
    species_name = _species_name(char.species_id)
    nt = noble_title(char.society_id, char.species_id, char.characteristics.SOC)
    pills = [
        f"SPECIES: {species_name}",
        f"CREDITS: Cr{char.credits:,}",
    ]
    if char.ship_shares:
        pills.append(f"SHIP SHARES: {char.ship_shares}×MCr1")
    if char.pension_per_year:
        pills.append(f"PENSION: Cr{char.pension_per_year:,}/yr")
    if nt:
        pills.append(f"TITLE: {nt}")
    for pill in pills:
        pw = c.stringWidth(pill, FONT_BOLD, 7) + 10
        sheet.rect_filled(meta_x, meta_y - 1, pw, 12, C_PANEL, C_BORDER, 0.3)
        sheet.text(meta_x + 5, meta_y + 2, pill, font=FONT_BOLD, size=7, color=C_ACCENT)
        meta_x += pw + 6

    y_cursor = y_top - HDR_H - 8   # gap below header

    # ── two-column layout ─────────────────────────────────────────────────────
    COL_L_X = MARGIN
    COL_R_X = MARGIN + COL_L_W + COL_GAP

    left_y  = y_cursor
    right_y = y_cursor

    # ════════════════════════════════════════════════════════
    # LEFT COLUMN — Characteristics + Skills
    # ════════════════════════════════════════════════════════

    # ── Characteristics ───────────────────────────────────────────────────────
    left_y = sheet.section_header(COL_L_X, left_y, COL_L_W, "Characteristics")

    stats_order = ["STR", "DEX", "END", "INT", "EDU", "SOC"]
    ch = char.characteristics
    STAT_BOX_W = COL_L_W / 3
    STAT_BOX_H = 36

    for i, stat in enumerate(stats_order):
        sx = COL_L_X + (i % 3) * STAT_BOX_W
        sy = left_y - (i // 3) * STAT_BOX_H
        val = getattr(ch, stat, 0)
        dm  = char_dm(val)

        # box background
        sheet.rect_filled(sx, sy - STAT_BOX_H, STAT_BOX_W, STAT_BOX_H,
                          C_BG, C_BORDER, 0.5)
        # stat label
        sheet.text(sx + STAT_BOX_W / 2, sy - 9, stat, font=FONT_BOLD, size=8,
                   color=C_MUTED, align="center")
        # value (large)
        sheet.text(sx + STAT_BOX_W / 2, sy - 23, str(val), font=FONT_BOLD, size=18,
                   color=C_TEXT, align="center")
        # DM
        sheet.text(sx + STAT_BOX_W / 2, sy - 33, f"DM {fmt_dm(dm)}", font=FONT_BODY,
                   size=7, color=C_MUTED, align="center")

    left_y -= 2 * STAT_BOX_H

    # PSI (if applicable)
    if char.psi > 0:
        PSI_W = COL_L_W
        PSI_H = 20
        left_y -= 2
        sheet.rect_filled(COL_L_X, left_y - PSI_H, PSI_W, PSI_H, C_PANEL_MID, C_BORDER, 0.5)
        psi_dm = char_dm(char.psi)
        sheet.text(COL_L_X + 10, left_y - PSI_H + 6,
                   f"PSI  {char.psi}  (DM {fmt_dm(psi_dm)})",
                   font=FONT_BOLD, size=9, color=C_ACCENT)
        if char.psi_trained_talents:
            talents = ", ".join(char.psi_trained_talents)
            sheet.text(COL_L_X + PSI_W - 6, left_y - PSI_H + 6,
                       f"Talents: {talents}", font=FONT_BODY, size=7.5,
                       color=C_MUTED, align="right")
        left_y -= PSI_H

    left_y -= 6

    # ── Skills ────────────────────────────────────────────────────────────────
    left_y = sheet.section_header(COL_L_X, left_y, COL_L_W, "Skills")

    if char.skills:
        sorted_skills = sorted(char.skills, key=lambda s: (s.name, s.speciality or ""))
        for sk in sorted_skills:
            label = f"{sk.name} ({sk.speciality})" if sk.speciality else sk.name
            left_y = sheet.skill_row(COL_L_X, left_y, COL_L_W, label, str(sk.level))
            if left_y < MARGIN + 80:
                # start new section in place — add a continuation note
                sheet.text(COL_L_X + 4, left_y - 8,
                           "… continued on next page", font=FONT_BODY, size=7,
                           color=C_MUTED)
                left_y -= 12
                break
    else:
        sheet.text(COL_L_X + 6, left_y - ROW_H + 3, "No skills yet",
                   font=FONT_BODY, size=7.5, color=C_MUTED)
        left_y -= ROW_H

    left_y -= 6

    # ════════════════════════════════════════════════════════
    # RIGHT COLUMN — Careers + Associates + Equipment
    # ════════════════════════════════════════════════════════

    # ── Careers ───────────────────────────────────────────────────────────────
    right_y = sheet.section_header(COL_R_X, right_y, COL_R_W, "Career History")

    if char.completed_careers:
        for cr in char.completed_careers:
            cname  = _career_label(cr.career_id, cr.assignment_id)
            rank_s = cr.final_rank_title or (f"Rank {cr.final_rank}" if cr.final_rank else "No rank")
            terms_s = f"{cr.terms_served}t"
            right_y = sheet.skill_row(COL_R_X, right_y, COL_R_W, cname, terms_s)
            sheet.text(COL_R_X + 10, right_y - 2, f"{rank_s} — {cr.left_due_to}",
                       font=FONT_BODY, size=6.5, color=C_MUTED,
                       max_width=COL_R_W - 14)
            right_y -= 8
    else:
        sheet.text(COL_R_X + 6, right_y - ROW_H + 3, "No careers yet",
                   font=FONT_BODY, size=7.5, color=C_MUTED)
        right_y -= ROW_H

    right_y -= 6

    # ── Associates ────────────────────────────────────────────────────────────
    right_y = sheet.section_header(COL_R_X, right_y, COL_R_W, "Associates")

    assoc_by_kind = {"contact": [], "ally": [], "rival": [], "enemy": []}
    for a in (char.associates or []):
        if a.kind in assoc_by_kind:
            assoc_by_kind[a.kind].append(a)

    KIND_LABELS = [("contact", "Contacts"), ("ally", "Allies"),
                   ("rival", "Rivals"), ("enemy", "Enemies")]
    any_assoc = any(assoc_by_kind[k] for k, _ in KIND_LABELS)

    if any_assoc:
        for kind, label in KIND_LABELS:
            items = assoc_by_kind[kind]
            if not items:
                continue
            # mini header
            sheet.rect_filled(COL_R_X, right_y - 11, COL_R_W, 11, C_PANEL_MID)
            sheet.text(COL_R_X + 4, right_y - 8, f"{label} ({len(items)})",
                       font=FONT_BOLD, size=7, color=C_ACCENT)
            right_y -= 11
            for a in items:
                desc = a.description or "(unnamed)"
                right_y = sheet.skill_row(COL_R_X, right_y, COL_R_W, desc, "")
    else:
        sheet.text(COL_R_X + 6, right_y - ROW_H + 3, "No associates",
                   font=FONT_BODY, size=7.5, color=C_MUTED)
        right_y -= ROW_H

    right_y -= 6

    # ── Equipment ─────────────────────────────────────────────────────────────
    right_y = sheet.section_header(COL_R_X, right_y, COL_R_W, "Equipment")

    if char.equipment:
        for eq in char.equipment:
            label = f"{eq.name}" + (f" ×{eq.quantity}" if eq.quantity > 1 else "")
            note  = eq.notes or ""
            right_y = sheet.skill_row(COL_R_X, right_y, COL_R_W, label,
                                      note[:18] if note else "")
    else:
        sheet.text(COL_R_X + 6, right_y - ROW_H + 3, "No equipment",
                   font=FONT_BODY, size=7.5, color=C_MUTED)
        right_y -= ROW_H

    right_y -= 6

    # ── Species Traits ────────────────────────────────────────────────────────
    if char.traits:
        right_y = sheet.section_header(COL_R_X, right_y, COL_R_W, "Species Traits")
        for tr in char.traits:
            name = tr.get("name", "Trait")
            desc = tr.get("description", "")
            right_y = sheet.skill_row(COL_R_X, right_y, COL_R_W, name, "")
            if desc:
                from reportlab.lib.utils import simpleSplit
                lines = simpleSplit(desc, FONT_BODY, 7, COL_R_W - 16)
                for ln in lines[:2]:   # cap at 2 description lines
                    sheet.text(COL_R_X + 12, right_y - 4, ln,
                               font=FONT_BODY, size=7, color=C_MUTED)
                    right_y -= 9
        right_y -= 6

    # ── Misc sections (SolSec, Home Forces, Anagathics, Medical Debt) ─────────
    right_y = _draw_misc_sections(sheet, char, COL_R_X, right_y, COL_R_W)

    # ════════════════════════════════════════════════════════
    # BOTTOM SECTION — full-width Notes
    # ════════════════════════════════════════════════════════
    bottom_y = min(left_y, right_y) - 10

    NOTES_LABEL_H = 14
    NOTES_FIELD_H = 60
    NOTES_TOTAL   = NOTES_LABEL_H + NOTES_FIELD_H + 6

    # If there isn't room, push to a new page
    if bottom_y < MARGIN + NOTES_TOTAL + 10:
        sheet.new_page()
        bottom_y = H - MARGIN - 10

    bottom_y = sheet.section_header(MARGIN, bottom_y, W - 2 * MARGIN, "Notes")
    sheet.text_field(
        "Notes",
        MARGIN + 2, bottom_y - NOTES_FIELD_H,
        W - 2 * MARGIN - 4, NOTES_FIELD_H,
        value=char.user_notes or "",
        font_size=9,
        multiline=True,
    )
    bottom_y -= NOTES_FIELD_H + 4

    # ── capsule description (if generated) ────────────────────────────────────
    if char.capsule_description:
        bottom_y -= 6
        bottom_y = sheet.section_header(MARGIN, bottom_y, W - 2 * MARGIN,
                                        "Career Narrative")
        from reportlab.lib.utils import simpleSplit
        for para in char.capsule_description.split("\n\n"):
            para = para.strip()
            if not para:
                continue
            lines = simpleSplit(para, FONT_BODY, 8, W - 2 * MARGIN - 10)
            for ln in lines:
                if bottom_y < MARGIN + 14:
                    sheet.new_page()
                    bottom_y = H - MARGIN - 10
                sheet.text(MARGIN + 5, bottom_y - 10, ln, font=FONT_BODY, size=8,
                           color=C_TEXT)
                bottom_y -= 11
            bottom_y -= 4

    sheet.save()
    buf.seek(0)
    return buf.read()


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _draw_misc_sections(sheet: SheetCanvas, char: Character,
                        x: float, y: float, w: float) -> float:
    """Draw optional sections into the right column. Returns updated y."""

    if char.medical_debt > 0:
        y = sheet.section_header(x, y, w, "⚠ Medical Debt")
        y = sheet.row_pair(x, y, w, "Amount owed",
                           f"Cr{char.medical_debt:,}", danger=True)
        y = sheet.row_pair(x, y, w, "Note",
                           "Deducted from cash rolls")
        y -= 6

    if char.anagathics_active:
        y = sheet.section_header(x, y, w, "Anagathics")
        y = sheet.row_pair(x, y, w, "Status", "ACTIVE",
                           value_color=HexColor("#2E7D32"))
        terms_u = char.anagathics_terms_used or 0
        y = sheet.row_pair(x, y, w, "Terms on treatment", str(terms_u))
        y = sheet.row_pair(x, y, w, "Aging DM bonus", f"+{terms_u}")
        y -= 6

    if char.home_forces_enrolled:
        y = sheet.section_header(x, y, w, "Home Forces Reserves")
        comp = (char.home_forces_component or "groundside").replace("_", " ")
        y = sheet.row_pair(x, y, w, "Component", comp.title())
        y = sheet.row_pair(x, y, w, "Reserve rank", str(char.home_forces_rank))
        y -= 6

    if char.solsec_monitor:
        y = sheet.section_header(x, y, w, "SolSec Monitor")
        y = sheet.row_pair(x, y, w, "Monitor rank", str(char.solsec_monitor_rank))
        note = "DM+1 adv · nat-2 → SolSec mishap · nat-12 → SolSec event"
        if char.solsec_monitor_rank >= 3:
            note += " · +1 benefit roll"
        sheet.text(x + 4, y - 9, note, font=FONT_BODY, size=6.5, color=C_MUTED,
                   max_width=w - 8)
        y -= 12
        y -= 6

    if char.pension_per_year > 0:
        y = sheet.section_header(x, y, w, "Retirement Pension")
        y = sheet.row_pair(x, y, w, "Annual pension",
                           f"Cr{char.pension_per_year:,}")
        y = sheet.row_pair(x, y, w, "Based on", f"{char.total_terms} terms served")
        y -= 6

    if char.ship_shares > 0 and not char.pension_per_year:
        # ship shares shown in pills in header but also here if notable
        pass  # already in header

    return y


def _species_name(species_id: str) -> str:
    """Best-effort human-readable species name from id."""
    mapping = {
        "imperial_human":   "Imperial Human",
        "solomani_human":   "Solomani Human",
        "solomani_mixed":   "Solomani Mixed",
        "solomani_racial":  "Solomani (racial)",
        "confederation_human": "Confederation Human",
        "frontier_human":   "Frontier Human",
        "imperial_aslan":   "Imperial Aslan",
        "hierate_aslan":    "Hierate Aslan",
        "imperial_vargr":   "Imperial Vargr",
        "extents_vargr":    "Extents Vargr",
        "imperial_bwap":    "Imperial Bwap",
        "sword_worlds_human": "Sword Worlds Human",
        "zhodani_human":    "Zhodani Human",
        "two_thousand_worlds_human": "2K-Worlds Human",
        "hiver_federation_human": "Hiver-Federation Human",
        "luriani":          "Luriani",
        "jonkeereen":       "Jonkeereen",
        "droashav":         "Droashav",
        "akeed":            "Akeed",
        "sydite":           "Sydite",
        "faar":             "Faar",
        "dolphin":          "Dolphin",
        "uplifted_orca":    "Uplifted Orca",
        "alpine_caprisap":  "Alpine Caprisap",
        "boar_caprisap":    "Boar Caprisap",
        "capry_big_male":   "Capry (Big Male)",
        "capry_female":     "Capry (Female)",
        "capry_small_male": "Capry (Small Male)",
    }
    return mapping.get(species_id, species_id.replace("_", " ").title())


def _career_label(career_id: str, assignment_id: str) -> str:
    """Human-readable career/assignment label."""
    career_map = {
        "navy":             "Navy",
        "marines":          "Marines",
        "army":             "Army",
        "scouts":           "Scouts",
        "merchant":         "Merchant",
        "agent":            "Agent",
        "noble":            "Noble",
        "drifter":          "Drifter",
        "entertainer":      "Entertainer",
        "scholar":          "Scholar",
        "rogue":            "Rogue",
        "citizen":          "Citizen",
        "prisoner":         "Prisoner",
        "solsec":           "SolSec",
        "confederation_navy":  "Confederation Navy",
        "confederation_army":  "Confederation Army",
        "solomani_marine":     "Solomani Marine",
        "party":               "Party",
        "dolphin_civilian":    "Dolphin Civilian",
        "dolphin_military":    "Dolphin Military",
        "philosopher_elder":   "Philosopher-Elder",
        "spirit_singer":       "Spirit Singer",
    }
    cname = career_map.get(career_id, career_id.replace("_", " ").title())
    aname = assignment_id.replace("_", " ").title() if assignment_id else ""
    if aname and aname.lower() != cname.lower():
        return f"{cname} / {aname}"
    return cname
