import html

import streamlit as st

# Vintage treasure-map palette (user-provided mockup: aged parchment + gold).
GOLD = "#B8791E"
GOLD_DARK = "#8B5E17"
PARCHMENT = "#F6ECD4"
PARCHMENT_DARK = "#E4D2A0"
INK = "#3B2A18"
INK_FAINT = "#8A7857"
DONE = "#8B6914"
UPCOMING = "#E4D3A6"

_CSS = f"""
<style>
/* Aged-paper background: layered soft stains, no external image needed */
[data-testid="stAppViewContainer"] {{
    background-color: {PARCHMENT};
    background-image:
        radial-gradient(ellipse 500px 350px at 8% 12%, rgba(139,94,23,0.10), transparent 60%),
        radial-gradient(ellipse 600px 400px at 95% 85%, rgba(139,94,23,0.10), transparent 60%),
        radial-gradient(ellipse 400px 300px at 85% 10%, rgba(184,121,30,0.08), transparent 55%),
        radial-gradient(ellipse 450px 350px at 5% 90%, rgba(184,121,30,0.08), transparent 55%);
}}
[data-testid="stSidebar"] {{
    background-color: {PARCHMENT_DARK};
    border-right: 1px solid rgba(139,94,23,0.25);
}}
h1, h2, h3, h4, h5, h6 {{
    color: {INK} !important;
}}

/* Buttons: stable, non-hashed testid — st.button / st.form_submit_button */
[data-testid^="stBaseButton"] {{
    background: linear-gradient(180deg, #D9A63E, {GOLD}) !important;
    color: #FFFBEF !important;
    border: 1px solid {GOLD_DARK} !important;
    border-radius: 8px !important;
    box-shadow: 0 1px 2px rgba(59,42,24,0.25) !important;
}}
[data-testid^="stBaseButton"]:hover {{
    filter: brightness(1.06);
}}
/* st.link_button renders as an anchor, not stBaseButton */
[data-testid="stLinkButton"] a {{
    background: linear-gradient(180deg, #D9A63E, {GOLD}) !important;
    color: #FFFBEF !important;
    border: 1px solid {GOLD_DARK} !important;
    border-radius: 8px !important;
}}

/* Card marker trick: st.markdown renders each call as an isolated fragment
(see ui.card()'s docstring), so a hand-rolled <div> can't wrap the native
widgets inside st.container(border=True) — but modern :has() lets us style
the *actual* bordered container from a hidden marker placed inside it,
without depending on Streamlit's internal (unstable, hashed) CSS classes. */
.pn-card-marker {{ display: none; }}
[data-testid="stVerticalBlock"]:has(> [data-testid="stElementContainer"] .pn-card-marker) {{
    background: #FBF4E2;
    border: 1px solid rgba(139,94,23,0.35) !important;
    border-radius: 12px;
    padding: 0.9rem 1.1rem;
}}

.pn-mentor {{
    background: #FBF0D9;
    border-left: 4px solid {GOLD};
    border-radius: 10px;
    padding: 0.9rem 1.2rem;
    margin-bottom: 1rem;
    color: {INK};
}}
.pn-task-row {{
    padding: 0.25rem 0;
    font-size: 0.98rem;
    color: {INK};
}}
.pn-task-done {{
    color: {INK_FAINT};
    text-decoration: line-through;
}}

/* Map pins: keep only the current step's label always visible, reveal the
rest on hover — CSS-only, so tap devices fall back to the native <title>
tooltip (Streamlit strips <script>, so a real tap-to-toggle isn't possible). */
.pn-pin-label {{ opacity: 0; transition: opacity 0.12s ease; }}
.pn-pin:hover .pn-pin-label {{ opacity: 1; }}
.pn-pin-current .pn-pin-label {{ opacity: 1; }}
.pn-pin-node {{
    transition: transform 0.15s ease;
    transform-box: fill-box;
    transform-origin: center;
}}
.pn-pin:hover .pn-pin-node {{ transform: scale(1.3); }}
</style>
"""


def inject_css() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)


def card(title: str | None = None):
    """Context manager for a bordered card grouping native widgets.

    st.markdown renders each call as its own isolated HTML fragment, so a
    hand-rolled <div> opened in one call and closed in another never actually
    wraps the elements rendered in between (they end up as siblings, not
    children) — st.container(border=True) is the real grouping primitive.
    Styling it uses a hidden marker + :has() (see _CSS) since Streamlit's own
    border styling is applied via unpredictable hashed classes we can't target.
    """
    container = st.container(border=True)
    with container:
        st.markdown('<span class="pn-card-marker"></span>', unsafe_allow_html=True)
        if title:
            st.markdown(f"**{html.escape(title)}**")
    return container


def mentor_message(text: str) -> None:
    st.markdown(
        f'<div class="pn-mentor">💬 {html.escape(text)}</div>',
        unsafe_allow_html=True,
    )


def task_row(text: str, done: bool) -> None:
    mark = "✅" if done else "☐"
    css_class = "pn-task-row pn-task-done" if done else "pn-task-row"
    st.markdown(
        f'<div class="{css_class}">{mark} {html.escape(text)}</div>',
        unsafe_allow_html=True,
    )


def render_map_path(milestones, current_id) -> None:
    """A winding, treasure-map-style route (zigzagging pins connected by a
    dotted path) rather than a plain vertical list."""
    if not milestones:
        st.info("マイルストーンがまだありません。")
        return

    n = len(milestones)
    width = 380
    row_h = 100
    top_pad = 50
    height = top_pad * 2 + row_h * (n + 1)

    def pos(i):
        if i == 0:
            return width / 2, top_pad * 0.6
        if i == n + 1:
            return width / 2, height - top_pad * 0.6
        x = width * 0.26 if i % 2 == 1 else width * 0.74
        y = top_pad + row_h * i
        return x, y

    points = [pos(i) for i in range(n + 2)]
    path_d = f"M {points[0][0]:.0f},{points[0][1]:.0f} " + " ".join(
        f"L {x:.0f},{y:.0f}" for x, y in points[1:]
    )

    svg = [
        f'<svg viewBox="0 0 {width} {height}" width="100%" height="{height}" '
        f'xmlns="http://www.w3.org/2000/svg">',
        f'<path d="{path_d}" fill="none" stroke="{GOLD_DARK}" stroke-width="3" '
        f'stroke-dasharray="1 9" stroke-linecap="round" opacity="0.55"/>',
    ]

    sx, sy = points[0]
    svg.append(
        f'<text x="{sx:.0f}" y="{sy - 14:.0f}" text-anchor="middle" font-size="12" '
        f'font-weight="700" fill="{INK_FAINT}">START</text>'
    )
    svg.append(f'<circle cx="{sx:.0f}" cy="{sy:.0f}" r="6" fill="{INK_FAINT}"/>')

    for i, m in enumerate(milestones, start=1):
        x, y = points[i]
        is_current = current_id is not None and m.id == current_id
        if m.status == "done":
            fill = DONE
        elif is_current:
            fill = GOLD
        else:
            fill = UPCOMING
        text_color = INK if (m.status == "done" or is_current) else INK_FAINT
        label_anchor = "start" if x < width / 2 else "end"
        label_x = x + 22 if x < width / 2 else x - 22
        icon = "✓" if m.status == "done" else str(i)
        glow = (
            f'<circle cx="{x:.0f}" cy="{y:.0f}" r="21" fill="none" stroke="{GOLD}" '
            f'stroke-width="2" opacity="0.35"/>'
            if is_current
            else ""
        )
        pin_class = "pn-pin pn-pin-current" if is_current else "pn-pin"
        tooltip = f"STEP{i} {m.name}" + (f"（KPI: {m.kpi}）" if m.kpi else "")

        svg.append(f'<g class="{pin_class}">')
        svg.append(f"<title>{html.escape(tooltip)}</title>")
        svg.append(glow)
        svg.append('<g class="pn-pin-node">')
        svg.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="16" fill="{fill}" stroke="#FFFBEF" stroke-width="3"/>')
        svg.append(
            f'<text x="{x:.0f}" y="{y + 5:.0f}" text-anchor="middle" font-size="13" '
            f'font-weight="700" fill="#FFFBEF">{icon}</text>'
        )
        svg.append("</g>")
        svg.append('<g class="pn-pin-label">')
        # stroke behind fill acts as a readability halo — no background rect needed;
        # the node already shows the step number, so the label just needs the name
        svg.append(
            f'<text x="{label_x:.0f}" y="{y - 4:.0f}" text-anchor="{label_anchor}" font-size="13" '
            f'font-weight="600" fill="{text_color}" stroke="{PARCHMENT}" stroke-width="4" '
            f'stroke-linejoin="round" paint-order="stroke fill">{html.escape(m.name)}</text>'
        )
        if m.kpi:
            svg.append(
                f'<text x="{label_x:.0f}" y="{y + 16:.0f}" text-anchor="{label_anchor}" '
                f'font-size="11" fill="{INK_FAINT}" stroke="{PARCHMENT}" stroke-width="4" '
                f'stroke-linejoin="round" paint-order="stroke fill">KPI: {html.escape(m.kpi)}</text>'
            )
        svg.append("</g>")
        svg.append("</g>")

    gx, gy = points[-1]
    svg.append(
        f'<text x="{gx:.0f}" y="{gy + 22:.0f}" text-anchor="middle" font-size="12" '
        f'font-weight="700" fill="{INK_FAINT}">GOAL</text>'
    )
    svg.append(f'<circle cx="{gx:.0f}" cy="{gy:.0f}" r="8" fill="none" stroke="{INK_FAINT}" stroke-width="3"/>')
    svg.append("</svg>")

    st.markdown("".join(svg), unsafe_allow_html=True)
