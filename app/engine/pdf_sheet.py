"""
Traveller Character Sheet PDF generator.

Produces a 2-page landscape (792×612) PDF matching the travellercc.avorial.com
reference design:
  - Steel blue-gray page background
  - Black section header bars with diagonal corner notch and white text
  - Pointy-top hexagonal stat boxes in a left characteristics strip
  - CORE CHARACTERISTICS (STR/DEX/END/INT/EDU/SOC) + OTHER CHARACTERISTICS
  - Page 1 sections: PERSONAL DATA FILE, CAREERS, SKILLS, FINANCES, ARMOUR,
    WEAPONS, AUGMENTS, EQUIPMENT
  - Page 2 sections: NOTES (fillable), ALLIES/CONTACTS/RIVALS/ENEMIES,
    PREVIOUS HISTORY, PERSONAL DATA FILE (brief), UCP hexes, WOUNDS

Usage:
    from .pdf_sheet import generate_character_pdf
    pdf_bytes = generate_character_pdf(character)
"""

import io
from typing import Optional

from reportlab.lib.colors import Color, white, black
from reportlab.pdfgen import canvas as rl_canvas

from .character import Character


# ─────────────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────────────

PW = 792.0   # page width  (landscape)
PH = 612.0   # page height (landscape)

# Palette
BG         = Color(1.0,  1.0,  1.0)   # white background
PANEL      = Color(1.0,  1.0,  1.0)   # white section panels
HDR_BG     = Color(0.08, 0.08, 0.08)  # near-black header bars
HDR_FG     = Color(1.0,  0.55, 0.0)   # orange header text
SIDEBAR_BG = Color(0.08, 0.08, 0.08)  # near-black stat sidebar
SIDEBAR_FG = Color(1.0,  0.55, 0.0)   # orange sidebar labels
ROW_RED    = Color(0.9,  0.0,  0.0)   # red (kept for compatibility)
HEX_FILL   = Color(1.0,  1.0,  1.0)   # white hex interior
HEX_STR    = Color(0.2,  0.2,  0.2)   # dark hex border
ROW_ALT    = Color(0.92, 0.92, 0.92)  # subtle alternating row tint
STAT_AREA  = Color(0.88, 0.88, 0.88)  # stat panel tint
LABEL_COL  = Color(0.35, 0.35, 0.35)  # muted label text
BODY_COL   = Color(0.08, 0.08, 0.08)  # near-black body text
RULE_COL   = Color(0.65, 0.65, 0.65)  # field rule lines
FIELD_BG   = Color(0.96, 0.97, 1.0)   # fillable field background
FIELD_BDR  = Color(0.50, 0.55, 0.65)  # fillable field border
COL_HDR_BG = Color(0.22, 0.22, 0.22)  # dark column-header row background
COL_HDR_FG = Color(0.82, 0.82, 0.82)  # light column-header text

# Fonts
F_HDR  = "Helvetica-Bold"       # section header title
F_REG  = "Courier"              # body text
F_BOLD = "Courier-Bold"         # bold body
F_OBOL = "Courier-BoldOblique"  # bold italic body
F_OBL  = "Courier-Oblique"      # italic body


# ─────────────────────────────────────────────────────────────────────────────
# Coordinate helpers
# ─────────────────────────────────────────────────────────────────────────────

def dy(display_y: float) -> float:
    """Display-y (0=top) → canvas-y (0=bottom)."""
    return PH - display_y


# ─────────────────────────────────────────────────────────────────────────────
# Stat / game helpers
# ─────────────────────────────────────────────────────────────────────────────

def stat_digits(val: int) -> tuple:
    v = max(0, min(99, int(val or 0)))
    return str(v // 10), str(v % 10)


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


def ucp_char(val: int) -> str:
    if val >= 10:
        return chr(ord('A') + val - 10)
    return str(max(0, val))


_NOBLE_TITLES = {11: "Knight", 12: "Baronet", 13: "Baron",
                 14: "Marquis", 15: "Count"}
_IMPERIAL_SPECIES = {
    "imperial_human", "imperial_aslan", "imperial_vargr", "imperial_bwap",
    "hierate_aslan", "frontier_human", "luriani", "jonkeereen",
}

def noble_title(char: Character) -> Optional[str]:
    imp = (char.society_id in ("third_imperium", "")
           or char.species_id in _IMPERIAL_SPECIES)
    if not imp:
        return None
    soc = char.characteristics.SOC
    if soc > 15:
        return "Archduke"
    return _NOBLE_TITLES.get(soc)


def species_name(sid: str) -> str:
    m = {
        "imperial_human": "Imperial Human", "solomani_human": "Solomani Human",
        "solomani_mixed": "Solomani Mixed", "solomani_racial": "Solomani",
        "frontier_human": "Frontier Human",
        "confederation_human": "Confederation Human",
        "drinax_palace_human": "Drinax (Palace)", "drinax_wasteland_human": "Drinax (Wasteland)",
        "asim_human": "Asim Human",
        "hiver_federation_human": "Hiver Federation Human",
        "two_thousand_worlds_human": "Two Thousand Worlds Human",
        "imperial_aslan": "Imperial Aslan", "hierate_aslan": "Hierate Aslan",
        "glorious_empire_aslan": "GE Aslan",
        "imperial_vargr": "Imperial Vargr", "extents_vargr": "Extents Vargr",
        "kkree": "K'kree",
        "imperial_bwap": "Imperial Bwap", "sword_worlds_human": "Sword Worlds Human",
        "zhodani_human": "Zhodani Human", "luriani": "Luriani",
        "jonkeereen": "Jonkeereen", "dolphin": "Dolphin",
        "uplifted_orca": "Uplifted Orca", "droashav": "Droashav",
        "akeed": "Akeed", "sydite": "Sydite", "faar": "Faar",
    }
    return m.get(sid, sid.replace("_", " ").title())


def career_label(career_id: str, assignment_id: str) -> str:
    m = {
        "navy": "Navy", "marines": "Marines", "army": "Army", "scouts": "Scouts",
        "merchant": "Merchant", "agent": "Agent", "noble": "Noble",
        "drifter": "Drifter", "entertainer": "Entertainer", "scholar": "Scholar",
        "rogue": "Rogue", "citizen": "Citizen", "prisoner": "Prisoner",
        "solsec": "SolSec", "confederation_navy": "Confederation Navy",
        "confederation_army": "Confederation Army",
        "solomani_marine": "Solomani Marine", "party": "Party",
        "dolphin_civilian": "Dolphin Civilian", "dolphin_military": "Dolphin Military",
        "philosopher_elder": "Philosopher-Elder", "spirit_singer": "Spirit Singer",
    }
    cname = m.get(career_id, career_id.replace("_", " ").title())
    aname = (assignment_id or "").replace("_", " ").title()
    if aname and aname.lower() != cname.lower():
        return f"{cname} / {aname}"
    return cname


def get_stat(char: Character, code: str) -> int:
    ch = char.characteristics
    if code == "STR": return ch.STR
    if code == "DEX": return ch.DEX
    if code == "END": return ch.END
    if code == "INT": return ch.INT
    if code == "EDU": return ch.EDU
    if code == "SOC": return ch.SOC
    if code == "PSI": return char.psi
    # Extra characteristics (TER for Aslan, etc.)
    extra = getattr(char, "extra_characteristics", {}) or {}
    if code in extra:
        return int(extra[code])
    return 0  # MOR, LCK, SAN, CHA, WLT — not tracked in model


# ─────────────────────────────────────────────────────────────────────────────
# Low-level drawing primitives
# ─────────────────────────────────────────────────────────────────────────────

def fill_rect(c, x, y_top_d, w, h, color):
    c.setFillColor(color)
    c.rect(x, dy(y_top_d + h), w, h, fill=1, stroke=0)


def fill_stroke_rect(c, x, y_top_d, w, h, fill_color, stroke_color,
                     stroke_w=0.3):
    c.setFillColor(fill_color)
    c.setStrokeColor(stroke_color)
    c.setLineWidth(stroke_w)
    c.rect(x, dy(y_top_d + h), w, h, fill=1, stroke=1)


def hline(c, x0, x1, y_d, color=None, w=0.3):
    c.setStrokeColor(color or RULE_COL)
    c.setLineWidth(w)
    c.line(x0, dy(y_d), x1, dy(y_d))


def vline(c, x, y_top_d, y_bot_d, color=None, w=0.3):
    c.setStrokeColor(color or RULE_COL)
    c.setLineWidth(w)
    c.line(x, dy(y_top_d), x, dy(y_bot_d))


def draw_text(c, x, y_d, text, font=F_REG, size=7.0, color=None,
              align="left", max_w=None):
    if not text:
        return
    s = str(text)
    if max_w:
        while c.stringWidth(s, font, size) > max_w and len(s) > 1:
            s = s[:-2] + "…"
    c.setFillColor(color or BODY_COL)
    c.setFont(font, size)
    base_y = dy(y_d) - size * 0.30
    if align == "center":
        c.drawCentredString(x, base_y, s)
    elif align == "right":
        c.drawRightString(x, base_y, s)
    else:
        c.drawString(x, base_y, s)


def draw_hex(c, cx, cy_d, hw, hh,
             fill=None, stroke=None, sw=0.6):
    """Pointy-top hexagon centred at display position (cx, cy_d)."""
    fill  = fill  or HEX_FILL
    stroke = stroke or HEX_STR
    cy_c = dy(cy_d)
    pts = [
        (cx,      cy_c + hh),
        (cx + hw, cy_c + hh / 2),
        (cx + hw, cy_c - hh / 2),
        (cx,      cy_c - hh),
        (cx - hw, cy_c - hh / 2),
        (cx - hw, cy_c + hh / 2),
    ]
    p = c.beginPath()
    p.moveTo(*pts[0])
    for pt in pts[1:]:
        p.lineTo(*pt)
    p.close()
    c.setFillColor(fill)
    c.setStrokeColor(stroke)
    c.setLineWidth(sw)
    c.drawPath(p, fill=1, stroke=1)


def section_header(c, x0, x1, y_top_d, height=18.0, title="",
                   font_size=8.5, **_kwargs):
    """Dark header bar with orange title. Returns y_d just below the bar."""
    y_bot_d = y_top_d + height
    c.setFillColor(HDR_BG)
    c.setLineWidth(0)
    c.rect(x0, dy(y_top_d + height), x1 - x0, height, fill=1, stroke=0)
    if title:
        c.setFillColor(HDR_FG)
        c.setFont(F_HDR, font_size)
        c.drawString(x0 + 4.0,
                     dy(y_top_d + height * 0.5) - font_size * 0.30,
                     title)
    return y_bot_d


def add_text_field(c, name, x, y_top_d, w, h, value="",
                   font_size=7.5, multiline=False):
    """AcroForm fillable text field."""
    flags = "multiline" if multiline else ""
    c.acroForm.textfield(
        name=name, tooltip=name,
        x=x, y=dy(y_top_d + h),
        width=w, height=h,
        value=value or "",
        fontSize=font_size, fontName=F_REG,
        fillColor=FIELD_BG, borderColor=FIELD_BDR,
        borderWidth=0.5, textColor=BODY_COL,
        fieldFlags=flags, relative=False,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Characteristics strip  (shared geometry)
# ─────────────────────────────────────────────────────────────────────────────

SBAR_X0 = 24.0   # sidebar left
SBAR_X1 = 40.0   # sidebar right  (= hex-area left)
STAT_X1 = 106.0  # stat strip right edge

STAT_CX = 65.0;  STAT_HW = 11.0;  STAT_HH = 12.0   # single hex per stat

CORE_TOP_D  = 24.0;   CORE_BOT_D  = 297.0
OTHER_TOP_D = 310.0;  OTHER_BOT_D = 552.0

CORE_CENTERS  = [47.0, 92.0, 138.0, 183.0, 229.0, 274.0]
OTHER_CENTERS = [330.0, 370.0, 411.0, 451.0, 491.0, 531.0]

CORE_STATS  = [("STR","STRENGTH"), ("DEX","DEXTERITY"), ("END","ENDURANCE"),
               ("INT","INTELLECT"), ("EDU","EDUCATION"), ("SOC","SOCIAL")]
OTHER_STATS = [("MOR","MORALE"), ("LCK","LUCK"), ("SAN","SANITY"),
               ("CHA","CHARM"), ("PSI","PSI"), ("WLT","WEALTH")]


def draw_stat_block(c, char, stats, centers_d, sec_top_d, sec_bot_d, label):
    """Draw one stat section: sidebar + single hex per stat."""
    # Sidebar
    fill_rect(c, SBAR_X0, sec_top_d, SBAR_X1 - SBAR_X0,
              sec_bot_d - sec_top_d, SIDEBAR_BG)
    # Hex area background
    fill_rect(c, SBAR_X1, sec_top_d, STAT_X1 - SBAR_X1,
              sec_bot_d - sec_top_d, STAT_AREA)

    # Rotated section label in sidebar
    c.saveState()
    c.setFillColor(SIDEBAR_FG)
    c.setFont(F_BOLD, 4.5)
    mid_d = (sec_top_d + sec_bot_d) / 2
    c.translate(SBAR_X0 + 8.0, dy(mid_d))
    c.rotate(90)
    c.drawCentredString(0, 0, label)
    c.restoreState()

    for i, ((code, name), ctr_d) in enumerate(zip(stats, centers_d)):
        val = get_stat(char, code)
        dm  = char_dm(val)

        # Divider above each row (skip first)
        if i > 0:
            prev_d = centers_d[i - 1]
            hline(c, SBAR_X1, STAT_X1, (prev_d + ctr_d) / 2)

        # "DM" label above hex
        draw_text(c, STAT_CX, ctr_d - 17.0, "DM",
                  F_BOLD, 4.5, LABEL_COL, align="center")

        # Single hex with full stat value
        draw_hex(c, STAT_CX, ctr_d - 3.0, STAT_HW, STAT_HH)
        c.setFillColor(BODY_COL)
        c.setFont(F_BOLD, 9.0)
        c.drawCentredString(STAT_CX, dy(ctr_d - 3.0) - 3.2, str(max(0, int(val or 0))))

        # DM modifier below hex
        draw_text(c, STAT_CX, ctr_d + 12.0, fmt_dm(dm),
                  F_REG, 6.5, BODY_COL, align="center")

        # Stat name at bottom of cell
        draw_text(c, SBAR_X1 + 2.0, ctr_d + 19.0, name,
                  F_OBOL, 3.8, LABEL_COL)


def draw_stat_column(c, char):
    """Draw the full left characteristics strip on the current page."""
    draw_stat_block(c, char, CORE_STATS, CORE_CENTERS,
                    CORE_TOP_D, CORE_BOT_D, "CORE CHARACTERISTICS")

    # Build dynamic OTHER_STATS: show tracked stats only (PSI + extras),
    # pad remaining slots with the standard placeholders.
    extra = getattr(char, "extra_characteristics", {}) or {}
    # Known non-tracked placeholders in order; we'll replace them with real stats
    placeholders = [("MOR","MORALE"), ("LCK","LUCK"), ("SAN","SANITY"),
                    ("CHA","CHARM"), ("WLT","WEALTH")]
    known_tracked = [("PSI", "PSI")]
    for code, val in sorted(extra.items()):
        stat_label = {"TER": "TERRITORIAL"}.get(code, code)
        known_tracked.append((code, stat_label))

    # Fill 6 slots: tracked stats first, then placeholders
    other_stats = known_tracked[:6]
    for ph in placeholders:
        if len(other_stats) >= 6:
            break
        if ph[0] not in [s[0] for s in other_stats]:
            other_stats.append(ph)

    draw_stat_block(c, char, other_stats[:6], OTHER_CENTERS,
                    OTHER_TOP_D, OTHER_BOT_D, "OTHER CHARACTERISTICS")


# ─────────────────────────────────────────────────────────────────────────────
# Page furniture
# ─────────────────────────────────────────────────────────────────────────────

def draw_background(c):
    c.setFillColor(BG)
    c.rect(0, 0, PW, PH, fill=1, stroke=0)


def draw_footer(c, page_num):
    draw_text(c, PW / 2, 598.0,
              f"Traveller Character Sheet  —  Page {page_num}       travellercc.avorial.com",
              F_REG, 5.0, LABEL_COL, "center")


# ─────────────────────────────────────────────────────────────────────────────
# Generic row helpers
# ─────────────────────────────────────────────────────────────────────────────

def data_row(c, x0, x1, y_d, rh, label, value,
             alt=False, label_w=62.0, v_size=7.0):
    """Single-label + value row with bottom rule."""
    if alt:
        fill_rect(c, x0, y_d, x1 - x0, rh, ROW_ALT)
    draw_text(c, x0 + 3.0, y_d + rh * 0.52, label, F_BOLD, 5.0, LABEL_COL)
    draw_text(c, x0 + label_w, y_d + rh * 0.52, str(value) if value is not None else "",
              F_REG, v_size, BODY_COL, max_w=x1 - x0 - label_w - 3.0)
    hline(c, x0, x1, y_d + rh)


def skill_row(c, x0, x1, y_d, rh, label, level, alt=False):
    """Name-left, level-right row with bottom rule."""
    if alt:
        fill_rect(c, x0, y_d, x1 - x0, rh, ROW_ALT)
    draw_text(c, x0 + 3.0, y_d + rh * 0.52, label, F_REG, 6.5, BODY_COL,
              max_w=x1 - x0 - 20.0)
    draw_text(c, x1 - 3.0, y_d + rh * 0.52, str(level), F_BOLD, 7.0, BODY_COL,
              align="right")
    hline(c, x0, x1, y_d + rh)


# ─────────────────────────────────────────────────────────────────────────────
# PAGE 1
# ─────────────────────────────────────────────────────────────────────────────

# Left main column
LM_X0 = 114.0
LM_X1 = 360.0
LM_W  = LM_X1 - LM_X0

# Right main column
RM_X0 = 372.0
RM_X1 = 768.0
RM_W  = RM_X1 - RM_X0


def draw_p1_personal_data(c, char):
    """PERSONAL DATA FILE panel, page 1 left column."""
    sec_top = 24.0;  sec_bot = 118.0
    fill_rect(c, LM_X0, sec_top, LM_W, sec_bot - sec_top, PANEL)
    y = section_header(c, LM_X0, LM_X1, sec_top, title="PERSONAL DATA FILE")
    rh = 9.5

    # Name (fillable)
    draw_text(c, LM_X0 + 3.0, y + rh * 0.48, "NAME", F_BOLD, 5.0, LABEL_COL)
    add_text_field(c, "Name", LM_X0 + 40.0, y, LM_W - 43.0, rh,
                   value=char.name or "")
    hline(c, LM_X0, LM_X1, y + rh);  y += rh

    # Homeworld + UWP
    hw_mid = LM_X0 + LM_W * 0.58
    draw_text(c, LM_X0 + 3.0, y + rh * 0.48, "HOMEWORLD", F_BOLD, 5.0, LABEL_COL)
    add_text_field(c, "Homeworld", LM_X0 + 58.0, y, hw_mid - LM_X0 - 61.0, rh,
                   value=char.homeworld or "")
    vline(c, hw_mid, y, y + rh)
    draw_text(c, hw_mid + 3.0, y + rh * 0.48, "UWP", F_BOLD, 5.0, LABEL_COL)
    add_text_field(c, "UWP", hw_mid + 24.0, y, LM_X1 - hw_mid - 26.0, rh,
                   value=char.homeworld_uwp or "")
    hline(c, LM_X0, LM_X1, y + rh);  y += rh

    # Species + Age
    mid = (LM_X0 + LM_X1) / 2
    fill_rect(c, LM_X0, y, LM_W, rh, ROW_ALT)
    draw_text(c, LM_X0 + 3.0, y + rh * 0.52, "SPECIES", F_BOLD, 5.0, LABEL_COL)
    draw_text(c, LM_X0 + 45.0, y + rh * 0.52, species_name(char.species_id),
              F_REG, 6.5, BODY_COL, max_w=mid - LM_X0 - 48.0)
    vline(c, mid, y, y + rh)
    draw_text(c, mid + 3.0, y + rh * 0.52, "AGE", F_BOLD, 5.0, LABEL_COL)
    draw_text(c, mid + 28.0, y + rh * 0.52, str(char.age), F_BOLD, 7.5, BODY_COL)
    hline(c, LM_X0, LM_X1, y + rh);  y += rh

    # Terms
    draw_text(c, LM_X0 + 3.0, y + rh * 0.52, "TERMS SERVED", F_BOLD, 5.0, LABEL_COL)
    draw_text(c, LM_X0 + 70.0, y + rh * 0.52, str(char.total_terms),
              F_BOLD, 7.5, BODY_COL)
    vline(c, mid, y, y + rh)
    nt = noble_title(char)
    if nt:
        draw_text(c, mid + 3.0, y + rh * 0.52, "TITLE", F_BOLD, 5.0, LABEL_COL)
        draw_text(c, mid + 30.0, y + rh * 0.52, nt, F_REG, 6.5, BODY_COL)
    hline(c, LM_X0, LM_X1, y + rh);  y += rh

    # Credits
    fill_rect(c, LM_X0, y, LM_W, rh, ROW_ALT)
    draw_text(c, LM_X0 + 3.0, y + rh * 0.52, "CREDITS", F_BOLD, 5.0, LABEL_COL)
    draw_text(c, LM_X0 + 45.0, y + rh * 0.52, f"Cr {char.credits:,}",
              F_BOLD, 7.0, BODY_COL)
    clan_shares = getattr(char, "clan_shares", 0)
    if char.ship_shares > 0:
        vline(c, mid, y, y + rh)
        draw_text(c, mid + 3.0, y + rh * 0.52, "SHIP SHARES", F_BOLD, 5.0, LABEL_COL)
        draw_text(c, mid + 60.0, y + rh * 0.52, str(char.ship_shares),
                  F_BOLD, 7.0, BODY_COL)
    elif clan_shares > 0:
        vline(c, mid, y, y + rh)
        draw_text(c, mid + 3.0, y + rh * 0.52, "CLAN SHARES", F_BOLD, 5.0, LABEL_COL)
        draw_text(c, mid + 60.0, y + rh * 0.52, str(clan_shares),
                  F_BOLD, 7.0, BODY_COL)
    hline(c, LM_X0, LM_X1, y + rh);  y += rh

    # Pension (if any)
    if char.pension_per_year > 0:
        draw_text(c, LM_X0 + 3.0, y + rh * 0.52, "PENSION/YR", F_BOLD, 5.0, LABEL_COL)
        draw_text(c, LM_X0 + 60.0, y + rh * 0.52,
                  f"Cr {char.pension_per_year:,}", F_BOLD, 7.0, BODY_COL)
        hline(c, LM_X0, LM_X1, y + rh);  y += rh

    # Society
    draw_text(c, LM_X0 + 3.0, y + rh * 0.52, "SOCIETY", F_BOLD, 5.0, LABEL_COL)
    draw_text(c, LM_X0 + 45.0, y + rh * 0.52,
              char.society_id.replace("_", " ").title(), F_REG, 6.5, BODY_COL)
    hline(c, LM_X0, LM_X1, y + rh)


def draw_p1_careers(c, char):
    """CAREERS panel, page 1 left column."""
    sec_top = 126.0;  sec_bot = 234.0
    fill_rect(c, LM_X0, sec_top, LM_W, sec_bot - sec_top, PANEL)
    y = section_header(c, LM_X0, LM_X1, sec_top, title="CAREERS")
    rh = 9.0

    col_terms_x = LM_X1 - 76.0
    col_rank_x  = LM_X1 - 48.0

    # Column header row
    fill_rect(c, LM_X0, y, LM_W, rh, COL_HDR_BG)
    draw_text(c, LM_X0 + 3.0,       y + rh * 0.52, "CAREER", F_OBL, 5.5, COL_HDR_FG)
    draw_text(c, col_terms_x + 2.0,  y + rh * 0.52, "TERMS",  F_OBL, 5.5, COL_HDR_FG)
    draw_text(c, col_rank_x + 2.0,   y + rh * 0.52, "RANK",   F_OBL, 5.5, COL_HDR_FG)
    hline(c, LM_X0, LM_X1, y + rh);  y += rh

    careers = char.completed_careers
    if not careers:
        draw_text(c, LM_X0 + 4.0, y + 8.0, "No careers completed.",
                  F_OBL, 6.5, LABEL_COL)
        return

    for i, cr in enumerate(careers[:9]):
        label  = career_label(cr.career_id, cr.assignment_id)
        rank_s = cr.final_rank_title or (f"Rank {cr.final_rank}" if cr.final_rank else "")
        alt    = (i % 2 == 1)
        if alt:
            fill_rect(c, LM_X0, y, LM_W, rh, ROW_ALT)
        draw_text(c, LM_X0 + 3.0,      y + rh * 0.52, label,
                  F_REG, 6.5, BODY_COL, max_w=col_terms_x - LM_X0 - 6.0)
        draw_text(c, col_terms_x + 2.0, y + rh * 0.52, str(cr.terms_served),
                  F_BOLD, 6.5, BODY_COL)
        if rank_s:
            draw_text(c, col_rank_x + 2.0, y + rh * 0.52, rank_s,
                      F_REG, 6.0, BODY_COL, max_w=LM_X1 - col_rank_x - 4.0)
        hline(c, LM_X0, LM_X1, y + rh);  y += rh


def draw_p1_skills(c, char):
    """SKILLS panel, page 1 left column."""
    sec_top = 242.0;  sec_bot = 530.0
    fill_rect(c, LM_X0, sec_top, LM_W, sec_bot - sec_top, PANEL)
    y = section_header(c, LM_X0, LM_X1, sec_top, title="SKILLS")

    # Training header rows (reference style)
    th = 10.0
    fill_rect(c, LM_X0, y, LM_W, th, COL_HDR_BG)
    draw_text(c, LM_X0 + 3.0, y + th * 0.52,
              "TRAINING IN SKILL:", F_OBL, 5.0, COL_HDR_FG)
    draw_text(c, LM_X0 + LM_W * 0.65, y + th * 0.52,
              "WEEKS:", F_OBL, 5.0, COL_HDR_FG)
    hline(c, LM_X0, LM_X1, y + th);  y += th

    fill_rect(c, LM_X0, y, LM_W, th, COL_HDR_BG)
    draw_text(c, LM_X0 + 3.0, y + th * 0.52,
              "TRAINING PERIOD COMPLETE:", F_OBL, 5.0, COL_HDR_FG)
    hline(c, LM_X0, LM_X1, y + th);  y += th

    rh = 9.5
    skills = sorted(char.skills or [], key=lambda s: (s.name, s.speciality or ""))
    max_rows = int((sec_bot - y) / rh)

    if not skills:
        draw_text(c, LM_X0 + 4.0, y + 8.0, "No skills yet.",
                  F_OBL, 6.5, LABEL_COL)
        return

    for i, sk in enumerate(skills[:max_rows]):
        spec   = f"({sk.speciality})" if sk.speciality else ""
        label  = f"{sk.name}{spec}-{sk.level}"
        if i % 2 == 1:
            fill_rect(c, LM_X0, y, LM_W, rh, ROW_ALT)
        draw_text(c, LM_X0 + 3.0, y + rh * 0.52, label,
                  F_REG, 6.5, BODY_COL, max_w=LM_W - 8.0)
        hline(c, LM_X0, LM_X1, y + rh)
        y += rh
        if y + rh > sec_bot:
            remaining = len(skills) - i - 1
            if remaining > 0:
                draw_text(c, LM_X0 + 4.0, y + 4.0,
                          f"+ {remaining} more...",
                          F_OBL, 5.5, LABEL_COL)
            break


def draw_p1_finances(c, char):
    """FINANCES panel, page 1 right column."""
    sec_top = 24.0;  sec_bot = 94.0
    fill_rect(c, RM_X0, sec_top, RM_W, sec_bot - sec_top, PANEL)
    y = section_header(c, RM_X0, RM_X1, sec_top, title="FINANCES")
    rh = 10.0
    mid = RM_X0 + RM_W / 2

    # Row 1: MONTHLY SHIP PAYMENTS (full width)
    draw_text(c, RM_X0 + 3.0, y + rh * 0.52, "MONTHLY SHIP PAYMENTS:",
              F_OBL, 5.5, LABEL_COL)
    draw_text(c, RM_X1 - 3.0, y + rh * 0.52, "Cr.",
              F_BOLD, 6.5, BODY_COL, align="right")
    hline(c, RM_X0, RM_X1, y + rh);  y += rh

    # Row 2: PENSION left | CASH ON HAND right
    fill_rect(c, RM_X0, y, RM_W, rh, ROW_ALT)
    draw_text(c, RM_X0 + 3.0, y + rh * 0.52, "PENSION:", F_OBL, 5.5, LABEL_COL)
    pension_s = f"Cr. {char.pension_per_year:,}" if char.pension_per_year else "Cr. 0"
    draw_text(c, RM_X0 + 52.0, y + rh * 0.52, pension_s, F_BOLD, 6.5, BODY_COL)
    vline(c, mid, y, y + rh)
    draw_text(c, mid + 3.0, y + rh * 0.52, "CASH ON HAND:", F_OBL, 5.5, LABEL_COL)
    draw_text(c, RM_X1 - 3.0, y + rh * 0.52, f"Cr. {char.credits:,}",
              F_BOLD, 6.5, BODY_COL, align="right")
    hline(c, RM_X0, RM_X1, y + rh);  y += rh

    # Row 3: DEBT left | LIVING COST right
    draw_text(c, RM_X0 + 3.0, y + rh * 0.52, "DEBT:", F_OBL, 5.5, LABEL_COL)
    debt_col  = Color(0.8, 0.1, 0.1) if char.medical_debt > 0 else BODY_COL
    draw_text(c, RM_X0 + 52.0, y + rh * 0.52,
              f"Cr. {char.medical_debt:,}" if char.medical_debt else "Cr. 0",
              F_BOLD, 6.5, debt_col)
    vline(c, mid, y, y + rh)
    draw_text(c, mid + 3.0, y + rh * 0.52, "LIVING COST:", F_OBL, 5.5, LABEL_COL)
    draw_text(c, RM_X1 - 3.0, y + rh * 0.52, "Cr. 0",
              F_BOLD, 6.5, BODY_COL, align="right")
    hline(c, RM_X0, RM_X1, y + rh)


def draw_p1_armour(c, char):
    """ARMOUR panel, page 1 right column."""
    sec_top = 106.0;  sec_bot = 210.0
    fill_rect(c, RM_X0, sec_top, RM_W, sec_bot - sec_top, PANEL)
    y = section_header(c, RM_X0, RM_X1, sec_top, title="ARMOUR")
    rh = 9.0
    col_w = RM_W / 4

    # Header mini-row
    fill_rect(c, RM_X0, y, RM_W, rh, COL_HDR_BG)
    hdrs = ["TYPE", "RAD", "PROTECTION", "KG", "OPTIONS"]
    col_fracs = [0.0, 0.28, 0.44, 0.64, 0.76]
    for i, (h, frac) in enumerate(zip(hdrs, col_fracs)):
        cx_ = RM_X0 + RM_W * frac
        if i:
            vline(c, cx_, y, y + rh)
        draw_text(c, cx_ + 3.0, y + rh * 0.52, h, F_OBL, 5.0, COL_HDR_FG)
    hline(c, RM_X0, RM_X1, y + rh);  y += rh

    # Blank rows for recording armour (5 columns)
    for i in range(8):
        alt = (i % 2 == 1)
        if alt:
            fill_rect(c, RM_X0, y, RM_W, rh, ROW_ALT)
        for frac in col_fracs[1:]:
            vline(c, RM_X0 + RM_W * frac, y, y + rh)
        hline(c, RM_X0, RM_X1, y + rh);  y += rh


def draw_p1_weapons(c, char):
    """WEAPONS panel, page 1 right column."""
    sec_top = 220.0;  sec_bot = 350.0
    fill_rect(c, RM_X0, sec_top, RM_W, sec_bot - sec_top, PANEL)
    y = section_header(c, RM_X0, RM_X1, sec_top, title="WEAPONS")
    rh = 9.0

    # Column headers
    wcols = [("WEAPON", 0.0), ("TL", 0.36), ("RANGE", 0.46),
             ("DAMAGE", 0.60), ("KG", 0.76), ("MAGAZINE", 0.86)]
    fill_rect(c, RM_X0, y, RM_W, rh, COL_HDR_BG)
    for lbl, frac in wcols:
        cx_ = RM_X0 + RM_W * frac
        if frac > 0:
            vline(c, cx_, y, y + rh)
        draw_text(c, cx_ + 3.0, y + rh * 0.52, lbl, F_OBL, 5.0, COL_HDR_FG)
    hline(c, RM_X0, RM_X1, y + rh);  y += rh

    # Blank weapon rows
    for i in range(10):
        alt = (i % 2 == 1)
        if alt:
            fill_rect(c, RM_X0, y, RM_W, rh, ROW_ALT)
        for _, frac in wcols[1:]:
            vline(c, RM_X0 + RM_W * frac, y, y + rh)
        hline(c, RM_X0, RM_X1, y + rh);  y += rh


def draw_p1_augments(c, char):
    """AUGMENTS panel, page 1 right column."""
    sec_top = 360.0;  sec_bot = 444.0
    fill_rect(c, RM_X0, sec_top, RM_W, sec_bot - sec_top, PANEL)
    y = section_header(c, RM_X0, RM_X1, sec_top, title="AUGMENTS")
    rh = 9.0

    # Col headers: TYPE | TL | IMPROVEMENT
    tl_x = RM_X0 + RM_W * 0.45
    imp_x = RM_X0 + RM_W * 0.58
    fill_rect(c, RM_X0, y, RM_W, rh, COL_HDR_BG)
    draw_text(c, RM_X0 + 3.0, y + rh * 0.52, "TYPE",        F_OBL, 5.0, COL_HDR_FG)
    vline(c, tl_x,  y, y + rh)
    draw_text(c, tl_x + 3.0,  y + rh * 0.52, "TL",          F_OBL, 5.0, COL_HDR_FG)
    vline(c, imp_x, y, y + rh)
    draw_text(c, imp_x + 3.0, y + rh * 0.52, "IMPROVEMENT",  F_OBL, 5.0, COL_HDR_FG)
    hline(c, RM_X0, RM_X1, y + rh);  y += rh

    for i in range(6):
        alt = (i % 2 == 1)
        if alt:
            fill_rect(c, RM_X0, y, RM_W, rh, ROW_ALT)
        vline(c, tl_x,  y, y + rh)
        vline(c, imp_x, y, y + rh)
        hline(c, RM_X0, RM_X1, y + rh);  y += rh


def draw_p1_equipment(c, char):
    """EQUIPMENT panel, page 1 right column."""
    sec_top = 454.0;  sec_bot = 564.0
    fill_rect(c, RM_X0, sec_top, RM_W, sec_bot - sec_top, PANEL)
    y = section_header(c, RM_X0, RM_X1, sec_top, title="EQUIPMENT")
    rh = 9.0

    # Col headers: TYPE | MASS (ref style), items fill TYPE col
    mass_x = RM_X0 + RM_W * 0.78
    fill_rect(c, RM_X0, y, RM_W, rh, COL_HDR_BG)
    draw_text(c, RM_X0 + 3.0, y + rh * 0.52, "TYPE",  F_OBL, 5.0, COL_HDR_FG)
    vline(c, mass_x, y, y + rh)
    draw_text(c, mass_x + 3.0, y + rh * 0.52, "MASS", F_OBL, 5.0, COL_HDR_FG)
    hline(c, RM_X0, RM_X1, y + rh);  y += rh

    equipment = char.equipment or []
    shown = 0
    for eq in equipment:
        if y + rh > sec_bot:
            break
        alt = (shown % 2 == 1)
        if alt:
            fill_rect(c, RM_X0, y, RM_W, rh, ROW_ALT)
        name_s = eq.name
        if eq.quantity > 1:
            name_s += f" x{eq.quantity}"
        draw_text(c, RM_X0 + 3.0, y + rh * 0.52, name_s,
                  F_REG, 6.5, BODY_COL, max_w=mass_x - RM_X0 - 6.0)
        vline(c, mass_x, y, y + rh)
        hline(c, RM_X0, RM_X1, y + rh)
        y += rh;  shown += 1

    # Fill remaining blank rows
    i = shown
    while y + rh <= sec_bot:
        alt = (i % 2 == 1)
        if alt:
            fill_rect(c, RM_X0, y, RM_W, rh, ROW_ALT)
        vline(c, mass_x, y, y + rh)
        hline(c, RM_X0, RM_X1, y + rh)
        y += rh;  i += 1


def draw_page1(c, char):
    draw_background(c)
    draw_stat_column(c, char)
    draw_p1_personal_data(c, char)
    draw_p1_careers(c, char)
    draw_p1_skills(c, char)
    draw_p1_finances(c, char)
    draw_p1_armour(c, char)
    draw_p1_weapons(c, char)
    draw_p1_augments(c, char)
    draw_p1_equipment(c, char)
    draw_footer(c, 1)


# ─────────────────────────────────────────────────────────────────────────────
# PAGE 2
# ─────────────────────────────────────────────────────────────────────────────

P2_L_X0 = 24.0;   P2_L_X1 = 416.0;  P2_L_W = P2_L_X1 - P2_L_X0
P2_R_X0 = 432.0;  P2_R_X1 = 768.0;  P2_R_W = P2_R_X1 - P2_R_X0

# UCP hex geometry (page 2)
UCP_HW = 12.75;  UCP_HH = 15.0
UCP_CY_D = 229.0
UCP_CX = [463.0, 509.0, 555.0, 601.0, 647.0, 693.0]
UCP_LABELS = ["STR", "DEX", "END", "INT", "EDU", "SOC"]
UCP_STAT_CODES = ["STR", "DEX", "END", "INT", "EDU", "SOC"]


def draw_p2_notes(c, char):
    """NOTES panel (fillable), page 2 left column."""
    sec_top = 24.0;  sec_bot = 118.0
    fill_rect(c, P2_L_X0, sec_top, P2_L_W, sec_bot - sec_top, PANEL)
    y = section_header(c, P2_L_X0, P2_L_X1, sec_top, title="NOTES")

    # Fillable notes textarea
    add_text_field(c, "Notes", P2_L_X0 + 2.0, y,
                   P2_L_W - 4.0, sec_bot - y - 2.0,
                   value=char.user_notes or "", multiline=True)


def draw_p2_associates(c, char):
    """ALLIES / CONTACTS / RIVALS / ENEMIES (+ WIVES for K'kree) panel, page 2 left column."""
    sec_top = 134.0;  sec_bot = 356.0
    fill_rect(c, P2_L_X0, sec_top, P2_L_W, sec_bot - sec_top, PANEL)

    kkree_wives = getattr(char, "kkree_wives", 0)
    is_kkree = "kkree" in (getattr(char, "species_id", "") or "").lower()

    if is_kkree and kkree_wives:
        title_str = "ALLIES / CONTACTS / RIVALS / ENEMIES / WIVES"
        col_labels = ["ALLIES", "CONTACTS", "RIVALS", "ENEMIES", "WIVES"]
        col_kinds  = ["ally",   "contact",  "rival",  "enemy",   "wife"]
        num_cols   = 5
    else:
        title_str = "ALLIES / CONTACTS / RIVALS / ENEMIES"
        col_labels = ["ALLIES", "CONTACTS", "RIVALS", "ENEMIES"]
        col_kinds  = ["ally",   "contact",  "rival",  "enemy"]
        num_cols   = 4

    y = section_header(c, P2_L_X0, P2_L_X1, sec_top, title=title_str)
    rh = 9.5
    col_w = P2_L_W / num_cols

    # Collect associates by kind
    by_kind: dict = {k: [] for k in col_kinds}
    for a in (char.associates or []):
        if a.kind in by_kind:
            by_kind[a.kind].append(a)
    # K'kree wives as pseudo-associates
    if is_kkree and kkree_wives:
        fam = getattr(char, "kkree_family_members", []) or []
        wife_objs = [type("W", (), {"description": m.get("description", "Wife")})()
                     for m in fam if m.get("role") == "wife"]
        if not wife_objs:
            # generate placeholders
            wife_objs = [type("W", (), {"description": f"Wife {i+1}"})()
                         for i in range(kkree_wives)]
        by_kind["wife"] = wife_objs[:kkree_wives]

    fill_rect(c, P2_L_X0, y, P2_L_W, rh, ROW_ALT)
    for i, (lbl, kind) in enumerate(zip(col_labels, col_kinds)):
        cx_ = P2_L_X0 + i * col_w
        if i:
            vline(c, cx_, y, sec_bot)
        count = len(by_kind.get(kind, []))
        draw_text(c, cx_ + 3.0, y + rh * 0.52,
                  f"{lbl} ({count})", F_BOLD, 5.0, LABEL_COL)
    hline(c, P2_L_X0, P2_L_X1, y + rh);  y += rh

    max_rows = int((sec_bot - y) / rh)
    max_in_col = max((len(lst) for lst in by_kind.values()), default=0)
    for row in range(min(max_in_col + 1, max_rows)):
        alt = (row % 2 == 1)
        if alt:
            fill_rect(c, P2_L_X0, y, P2_L_W, rh, ROW_ALT)
        for i, kind in enumerate(col_kinds):
            lst = by_kind[kind]
            cx_ = P2_L_X0 + i * col_w
            if row < len(lst):
                draw_text(c, cx_ + 3.0, y + rh * 0.52, lst[row].description,
                          F_REG, 6.0, BODY_COL, max_w=col_w - 6.0)
        hline(c, P2_L_X0, P2_L_X1, y + rh);  y += rh
        if y >= sec_bot:
            break

    # Fill remaining blank rows
    while y + rh <= sec_bot:
        hline(c, P2_L_X0, P2_L_X1, y + rh);  y += rh


def draw_p2_history(c, char):
    """PREVIOUS HISTORY panel, page 2 left column."""
    sec_top = 372.0;  sec_bot = 548.0
    fill_rect(c, P2_L_X0, sec_top, P2_L_W, sec_bot - sec_top, PANEL)
    y = section_header(c, P2_L_X0, P2_L_X1, sec_top, title="PREVIOUS HISTORY")
    rh = 9.5

    # Collect events from term history
    events = []
    for term in (char.term_history or []):
        cname = career_label(term.career_id, term.assignment_id)
        for ev in (term.events or []):
            events.append((cname, term.overall_term_number, ev))

    if not events:
        if char.capsule_description:
            # Wrap capsule description
            from reportlab.lib.utils import simpleSplit
            lines = simpleSplit(char.capsule_description, F_REG, 6.5, P2_L_W - 8.0)
            for ln in lines:
                if y + 8.0 > sec_bot:
                    break
                draw_text(c, P2_L_X0 + 4.0, y + 6.5, ln, F_REG, 6.5, BODY_COL)
                y += 8.5
        else:
            draw_text(c, P2_L_X0 + 4.0, y + 8.0, "No recorded history.",
                      F_OBL, 6.5, LABEL_COL)
        return

    for i, (cname, term_num, ev) in enumerate(events):
        if y + rh > sec_bot:
            break
        alt = (i % 2 == 1)
        if alt:
            fill_rect(c, P2_L_X0, y, P2_L_W, rh, ROW_ALT)
        prefix = f"T{term_num} {cname}: "
        draw_text(c, P2_L_X0 + 3.0, y + rh * 0.52, prefix,
                  F_BOLD, 5.5, LABEL_COL)
        pw = c.stringWidth(prefix, F_BOLD, 5.5)
        draw_text(c, P2_L_X0 + 3.0 + pw, y + rh * 0.52, ev,
                  F_REG, 6.0, BODY_COL, max_w=P2_L_W - pw - 6.0)
        hline(c, P2_L_X0, P2_L_X1, y + rh);  y += rh


def draw_p2_personal_data(c, char):
    """PERSONAL DATA FILE panel, page 2 right column (summary)."""
    sec_top = 24.0;  sec_bot = 170.0
    fill_rect(c, P2_R_X0, sec_top, P2_R_W, sec_bot - sec_top, PANEL)
    y = section_header(c, P2_R_X0, P2_R_X1, sec_top, title="PERSONAL DATA FILE")
    rh = 9.5

    rows = [
        ("NAME",     char.name or ""),
        ("HOMEWORLD", char.homeworld or ""),
        ("UWP",      char.homeworld_uwp or ""),
        ("SPECIES",  species_name(char.species_id)),
        ("SOCIETY",  char.society_id.replace("_", " ").title()),
        ("AGE",      str(char.age)),
        ("TERMS",    str(char.total_terms)),
        ("CREDITS",  f"Cr {char.credits:,}"),
    ]
    nt = noble_title(char)
    if nt:
        rows.insert(4, ("TITLE", nt))
    if char.ship_shares > 0:
        rows.append(("SHIP SHARES", str(char.ship_shares)))
    clan_shares = getattr(char, "clan_shares", 0)
    if clan_shares > 0:
        rows.append(("CLAN SHARES", str(clan_shares)))
    reputation = getattr(char, "reputation", 0)
    if reputation:
        rows.append(("REPUTATION", f"{reputation:+d}"))
    # K'kree extras
    if "kkree" in (getattr(char, "species_id", "") or "").lower():
        rank = (getattr(char, "kkree_soc_rank_degree", "") or "").replace("_", " ").title()
        if rank:
            rows.append(("SOC RANK", rank))
        area = getattr(char, "kkree_specialist_area", None)
        if area:
            rows.append(("SPECIALIST", area.replace("_", " ").title()))
        wives = getattr(char, "kkree_wives", 0)
        if wives:
            rows.append(("WIVES", str(wives)))

    for i, (lbl, val) in enumerate(rows):
        if y + rh > sec_bot:
            break
        data_row(c, P2_R_X0, P2_R_X1, y, rh, lbl, val,
                 alt=(i % 2 == 1), label_w=68.0)
        y += rh


def draw_p2_ucp(c, char):
    """UCP (Universal Character Profile) hex display, page 2 right column."""
    sec_top = 190.0;  sec_bot = 262.0
    fill_rect(c, P2_R_X0, sec_top, P2_R_W, sec_bot - sec_top, PANEL)
    y = section_header(c, P2_R_X0, P2_R_X1, sec_top,
                       title="UNIVERSAL CHARACTER PROFILE (UCP)")

    # Six UCP hexes (one per core stat)
    for i, (code, cx_) in enumerate(zip(UCP_STAT_CODES, UCP_CX)):
        val = get_stat(char, code)
        ch = ucp_char(val)

        draw_hex(c, cx_, UCP_CY_D, UCP_HW, UCP_HH)
        # Stat label below hex
        draw_text(c, cx_, UCP_CY_D + UCP_HH + 5.0, code,
                  F_BOLD, 4.5, LABEL_COL, "center")
        # Value in hex (red)
        c.setFillColor(ROW_RED)
        c.setFont(F_BOLD, 10.0)
        c.drawCentredString(cx_, dy(UCP_CY_D) - 3.5, ch)

    # UCP string below hexes
    ucp_str = "".join(ucp_char(get_stat(char, cd)) for cd in UCP_STAT_CODES)
    if char.psi > 0:
        ucp_str += "-" + ucp_char(char.psi)
    draw_text(c, (P2_R_X0 + P2_R_X1) / 2, sec_bot - 5.0, ucp_str,
              F_BOLD, 11.0, ROW_RED, "center")


def draw_p2_wounds(c, char):
    """WOUNDS / INJURIES panel, page 2 right column."""
    sec_top = 274.0;  sec_bot = 386.0
    fill_rect(c, P2_R_X0, sec_top, P2_R_W, sec_bot - sec_top, PANEL)
    y = section_header(c, P2_R_X0, P2_R_X1, sec_top, title="WOUNDS / INJURIES")
    rh = 9.5

    ch = char.characteristics
    stat_entries = [
        ("STR", ch.STR), ("DEX", ch.DEX), ("END", ch.END),
        ("INT", ch.INT), ("EDU", ch.EDU), ("SOC", ch.SOC),
    ]
    # Extra characteristics (e.g. TER for Aslan)
    extra = getattr(char, "extra_characteristics", {}) or {}
    for code, val in sorted(extra.items()):
        stat_entries.append((code, int(val)))
    if char.psi > 0:
        stat_entries.append(("PSI", char.psi))

    mid = P2_R_X0 + P2_R_W / 2

    # Header
    fill_rect(c, P2_R_X0, y, P2_R_W, rh, ROW_ALT)
    draw_text(c, P2_R_X0 + 3.0, y + rh * 0.52, "CHARACTERISTIC", F_BOLD, 5.0, LABEL_COL)
    draw_text(c, P2_R_X0 + 85.0, y + rh * 0.52, "CURRENT", F_BOLD, 5.0, LABEL_COL)
    vline(c, mid, y, y + rh)
    draw_text(c, mid + 3.0, y + rh * 0.52, "DAMAGE", F_BOLD, 5.0, LABEL_COL)
    draw_text(c, mid + 60.0, y + rh * 0.52, "REDUCED TO", F_BOLD, 5.0, LABEL_COL)
    hline(c, P2_R_X0, P2_R_X1, y + rh);  y += rh

    for i, (code, val) in enumerate(stat_entries):
        if y + rh > sec_bot:
            break
        alt = (i % 2 == 1)
        if alt:
            fill_rect(c, P2_R_X0, y, P2_R_W, rh, ROW_ALT)
        draw_text(c, P2_R_X0 + 3.0, y + rh * 0.52, code, F_BOLD, 6.5, LABEL_COL)
        draw_text(c, P2_R_X0 + 85.0, y + rh * 0.52, str(val), F_BOLD, 7.0, BODY_COL)
        vline(c, mid, y, y + rh)
        hline(c, P2_R_X0, P2_R_X1, y + rh);  y += rh

    # Blank rows for additional wounds
    while y + rh <= sec_bot:
        vline(c, mid, y, y + rh)
        hline(c, P2_R_X0, P2_R_X1, y + rh);  y += rh


def draw_p2_psionics(c, char):
    """PSIONICS panel (only drawn if char has PSI), page 2 right column."""
    if not char.psi:
        return
    sec_top = 398.0;  sec_bot = 468.0
    fill_rect(c, P2_R_X0, sec_top, P2_R_W, sec_bot - sec_top, PANEL)
    y = section_header(c, P2_R_X0, P2_R_X1, sec_top, title="PSIONICS")
    rh = 9.5

    data_row(c, P2_R_X0, P2_R_X1, y, rh, "PSI STRENGTH", str(char.psi),
             label_w=70.0);  y += rh
    talent_str = ", ".join(char.psi_trained_talents) if char.psi_trained_talents else "None"
    data_row(c, P2_R_X0, P2_R_X1, y, rh, "TRAINED TALENTS", talent_str,
             label_w=85.0, alt=True);  y += rh


def draw_page2(c, char):
    draw_background(c)
    draw_p2_notes(c, char)
    draw_p2_associates(c, char)
    draw_p2_history(c, char)
    draw_p2_personal_data(c, char)
    draw_p2_ucp(c, char)
    draw_p2_wounds(c, char)
    draw_p2_psionics(c, char)
    draw_footer(c, 2)


# ─────────────────────────────────────────────────────────────────────────────
# Public entry point
# ─────────────────────────────────────────────────────────────────────────────

def generate_character_pdf(char: Character) -> bytes:
    """Return the two-page landscape character sheet as raw PDF bytes."""
    buf = io.BytesIO()
    c = rl_canvas.Canvas(buf, pagesize=(PW, PH))
    c.setTitle(f"{char.name or 'Traveller'}  —  Character Sheet")
    c.setAuthor("Traveller Character Creator")
    c.setSubject("MgT 2e Character Sheet")

    # Page 1
    draw_page1(c, char)
    c.showPage()

    # Page 2
    draw_page2(c, char)
    c.showPage()

    c.save()
    buf.seek(0)
    return buf.read()
