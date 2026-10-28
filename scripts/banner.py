"""Gera o banner e o botão "Entrar na Forja" do README, em pt/en e nos temas claro/escuro (8 SVGs).

O texto vira curva (path), porque o GitHub não carrega fontes dentro de um SVG em <img>.
Para mudar um texto: edite LANGS, rode `python scripts/banner.py` e copie o `title`
novo para o alt da imagem em README.md e README.en.md.

Precisa de: pip install fonttools, e das fontes Inter e JetBrains Mono
(no Debian/Ubuntu: apt install fonts-inter fonts-jetbrains-mono), ou --fonts com a pasta delas.
"""
import argparse
import re
import sys
from pathlib import Path
from xml.sax.saxutils import escape

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

FONT_FILES = {
    'display': 'InterDisplay-Bold.otf',
    'body': 'Inter-Medium.otf',
    'mono': 'JetBrainsMono-Medium.ttf',
}
FONT_DIRS = [
    Path('/usr/share/fonts/opentype/inter'),
    Path('/usr/share/fonts/truetype/jetbrains-mono'),
]

LANGS = {
    'pt': dict(
        suffix='',
        kicker='DESENVOLVEDOR FULL STACK',
        available='disponível para vagas',
        tagline=[('3+ anos em ', 'muted'), ('Go', 'fg'), (' e ', 'muted'), ('React', 'fg'), (', do banco à tela', 'muted')],
        title='Victor Novakoski, desenvolvedor full stack. 3+ anos em Go e React, do banco à tela. Disponível para vagas.',
        cta='Entrar na Forja',
        cta_title='Entrar na Forja: abrir o portfólio',
    ),
    'en': dict(
        suffix='-en',
        kicker='FULL-STACK DEVELOPER',
        available='open to work',
        tagline=[('3+ years of ', 'muted'), ('Go', 'fg'), (' and ', 'muted'), ('React', 'fg'), (', from database to UI', 'muted')],
        title='Victor Novakoski, full-stack developer. 3+ years of Go and React, from database to UI. Open to work.',
        cta='Enter the Forge',
        cta_title='Enter the Forge: open the portfolio',
    ),
}

# Cores da Forja do Caçador (portfólio). Contraste conferido: secundário e brasa passam de 4,5:1 nos dois temas.
THEMES = {
    'dark': dict(bg='#0E0D0B', surface='#17150F', line='#2E2A22', fg='#E8E2D4',
                 muted='#9A9385', ember='#C7A25D', hot='#E0BC74', ok='#9FC79A'),
    'light': dict(bg='#FBF8F1', surface='#F3EDE0', line='#E2D9C6', fg='#1F1B14',
                  muted='#5E574A', ember='#8A6420', hot='#B5852F', ok='#3D7A37'),
}

BANNER_W, BANNER_H = 1200, 320
TEXT_X = 72
EMBER_X, EMBER_Y = BANNER_W - 110, 196
EMBER_GLOW_R = 86

CTA_W, CTA_H = 600, 120
CTA_PAD = 14
GEM_W = 40
CTA_GAP = 18


class Fonts:
    def __init__(self, dirs):
        self._fonts = {}
        for role, name in FONT_FILES.items():
            found = next((d / name for d in dirs if (d / name).exists()), None)
            if found is None:
                sys.exit(f'fonte não encontrada: {name}. Instale fonts-inter e fonts-jetbrains-mono ou use --fonts.')
            self._fonts[role] = TTFont(found)

    def path(self, text, role, size, x, y, tracking=0.0):
        """Devolve o `d` do texto já posicionado e a largura que ele ocupa."""
        font = self._fonts[role]
        glyphs = font.getGlyphSet()
        cmap = font.getBestCmap()
        scale = size / font['head'].unitsPerEm
        pen = SVGPathPen(glyphs)
        advance = 0.0
        for ch in text:
            name = cmap.get(ord(ch))
            if name is None:
                sys.exit(f'sem glifo para {ch!r} na fonte {role}')
            glyphs[name].draw(TransformPen(pen, (scale, 0, 0, -scale, x + advance, y)))
            advance += glyphs[name].width * scale + tracking
        return pen.getCommands(), advance

    def width(self, text, role, size, tracking=0.0):
        return self.path(text, role, size, 0, 0, tracking)[1]


def minify(svg):
    # uma casa decimal basta para os contornos e deixa o arquivo bem menor
    return re.sub(r'\d+\.\d{2,}', lambda m: f'{float(m[0]):.1f}', svg)


def check_fits(label, right_edge, limit):
    if right_edge > limit:
        sys.exit(f'o texto "{label}" passa da brasa ({right_edge:.0f} > {limit:.0f}); encurte em LANGS')


def diamond(cx, cy, half_w, half_h):
    return f'M{cx} {cy-half_h} L{cx+half_w} {cy} L{cx} {cy+half_h} L{cx-half_w} {cy} Z'


def build_banner(fonts, colors, lang):
    text_limit = EMBER_X - EMBER_GLOW_R
    kicker, kicker_w = fonts.path(lang['kicker'], 'mono', 28, TEXT_X, 96, 2.5)
    dot_x = TEXT_X + kicker_w + 34
    available, available_w = fonts.path(lang['available'], 'mono', 28, dot_x + 28, 96, 0.5)
    check_fits(lang['available'], dot_x + 28 + available_w, text_limit)
    name, name_w = fonts.path('Victor Novakoski', 'display', 104, TEXT_X - 4, 204)
    check_fits('Victor Novakoski', TEXT_X + name_w, text_limit)

    tagline = {'muted': '', 'fg': ''}
    x = TEXT_X
    for text, color in lang['tagline']:
        d, w = fonts.path(text, 'body', 42, x, 268)
        tagline[color] += d
        x += w
    check_fits('tagline', x, text_limit)

    c = colors
    parts = [f'<rect x="1" y="1" width="{BANNER_W-2}" height="{BANNER_H-2}" rx="16" fill="{c["bg"]}" stroke="{c["line"]}" stroke-width="2"/>']
    # cinzas subindo ao fundo, bem fracas
    for x, delay, duration, r in [(180, 0, 9, 2), (340, 3.5, 11, 1.6), (520, 6, 10, 2.2), (700, 1.5, 12, 1.4),
                                  (860, 4.5, 9.5, 1.8), (980, 7.5, 11.5, 1.5), (420, 8.5, 10.5, 1.3), (620, 2.5, 13, 1.7)]:
        parts.append(f'<circle class="ash" style="animation-duration:{duration}s;animation-delay:-{delay}s" '
                     f'cx="{x}" cy="{BANNER_H+10}" r="{r}" fill="{c["ember"]}"/>')
    parts += [
        f'<rect x="1" y="1" width="10" height="{BANNER_H-2}" rx="5" fill="{c["ember"]}"/>',
        f'<path d="{kicker}" fill="{c["ember"]}"/>',
        f'<circle class="ring" cx="{dot_x:.1f}" cy="86" r="7" fill="none" stroke="{c["ok"]}" stroke-width="2"/>',
        f'<circle cx="{dot_x:.1f}" cy="86" r="7" fill="{c["ok"]}"/>',
        f'<path d="{available}" fill="{c["muted"]}"/>',
        f'<path id="name" d="{name}" fill="{c["fg"]}"/>',
        # brilho que passa pelo nome, como metal saindo da forja
        '<g clip-path="url(#name-clip)"><rect class="sweep" x="-260" y="100" width="220" height="130" fill="url(#sweep)"/></g>',
        f'<path d="{tagline["muted"]}" fill="{c["muted"]}"/>',
        f'<path d="{tagline["fg"]}" fill="{c["fg"]}"/>',
        # brasa da forja: losango que tremula, brilho e faíscas
        f'<circle class="glow" cx="{EMBER_X}" cy="{EMBER_Y}" r="{EMBER_GLOW_R}" fill="url(#glow)"/>',
        f'<g class="flick"><path d="{diamond(EMBER_X, EMBER_Y, 30, 46)}" fill="{c["ember"]}"/>',
        f'<path class="core" d="{diamond(EMBER_X, EMBER_Y, 15, 24)}" fill="{c["hot"]}"/></g>',
    ]
    for dx, delay, r, drift in [(-34, 0.0, 4.0, -20), (30, 0.5, 3.2, 26), (-6, 1.0, 3.4, -8), (46, 1.5, 2.6, 34),
                                (-50, 2.0, 2.8, -40), (14, 2.5, 3.6, 12), (-22, 0.8, 2.4, -30), (38, 1.8, 2.2, 20)]:
        parts.append(f'<circle class="spark" style="animation-delay:{delay}s;--dx:{drift}px" '
                     f'cx="{EMBER_X+dx}" cy="{EMBER_Y-30}" r="{r}" fill="{c["hot"]}"/>')

    style = (
        '.glow{animation:pulse 2.6s ease-in-out infinite}'
        '.flick{animation:flick 1.9s ease-in-out infinite;transform-origin:center;transform-box:fill-box}'
        '.core{animation:core 1.3s ease-in-out infinite}'
        '.spark{opacity:0;animation:rise 2.8s ease-out infinite;transform-box:fill-box}'
        '.ash{opacity:0;animation:ash 10s linear infinite}'
        '.ring{transform-origin:center;transform-box:fill-box;animation:ring 2.4s ease-out infinite}'
        '.sweep{animation:sweep 5.5s ease-in-out infinite}'
        '@keyframes pulse{0%,100%{opacity:.5}50%{opacity:1}}'
        '@keyframes flick{0%,100%{transform:scale(1) rotate(0)}30%{transform:scale(1.07) rotate(-2deg)}60%{transform:scale(.97) rotate(1.5deg)}}'
        '@keyframes core{0%,100%{opacity:1}50%{opacity:.65}}'
        '@keyframes rise{0%{opacity:0;transform:translate(0,0)}12%{opacity:1}100%{opacity:0;transform:translate(var(--dx),-120px)}}'
        f'@keyframes ash{{0%{{opacity:0;transform:translate(0,0)}}10%{{opacity:.45}}90%{{opacity:.3}}100%{{opacity:0;transform:translate(30px,-{BANNER_H+20}px)}}}}'
        '@keyframes ring{0%{opacity:.9;transform:scale(1)}100%{opacity:0;transform:scale(2)}}'
        f'@keyframes sweep{{0%,55%{{transform:translateX(0)}}100%{{transform:translateX({BANNER_W+60}px)}}}}'
        '@media (prefers-reduced-motion:reduce){.glow,.flick,.core,.spark,.ash,.ring,.sweep{animation:none}.glow{opacity:.8}}'
    )
    return minify(
        f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{BANNER_W}" height="{BANNER_H}" '
        f'viewBox="0 0 {BANNER_W} {BANNER_H}" role="img" aria-labelledby="t"><title id="t">{escape(lang["title"])}</title>'
        f'<defs><radialGradient id="glow"><stop offset="0" stop-color="{c["hot"]}" stop-opacity=".55"/>'
        f'<stop offset="1" stop-color="{c["hot"]}" stop-opacity="0"/></radialGradient>'
        f'<linearGradient id="sweep" x1="0" x2="1"><stop offset="0" stop-color="{c["hot"]}" stop-opacity="0"/>'
        f'<stop offset=".5" stop-color="{c["hot"]}" stop-opacity=".9"/><stop offset="1" stop-color="{c["hot"]}" stop-opacity="0"/></linearGradient>'
        '<clipPath id="name-clip"><use href="#name" xlink:href="#name"/></clipPath>'
        f'<style>{style}</style></defs>'
        + ''.join(parts) + '</svg>'
    )


def build_cta(fonts, colors, lang):
    c = colors
    label_w = fonts.width(lang['cta'], 'display', 46)
    arrow_w = fonts.width('→', 'display', 46)
    start = (CTA_W - (GEM_W + CTA_GAP + label_w + CTA_GAP + arrow_w)) / 2
    label_x = start + GEM_W + CTA_GAP
    label, _ = fonts.path(lang['cta'], 'display', 46, label_x, 76)
    arrow, _ = fonts.path('→', 'display', 46, label_x + label_w + CTA_GAP, 76)
    gem_x, gem_y = start + GEM_W / 2, CTA_H / 2

    pill_w, pill_h = CTA_W - 2 * CTA_PAD, CTA_H - 2 * CTA_PAD
    pill = f'x="{CTA_PAD}" y="{CTA_PAD}" width="{pill_w}" height="{pill_h}" rx="{pill_h/2}"'
    style = (
        '.halo{animation:halo 2.4s ease-in-out infinite}'
        '.arrow{animation:nudge 1.4s ease-in-out infinite}'
        '.gem{animation:flick 1.9s ease-in-out infinite;transform-origin:center;transform-box:fill-box}'
        '.sweep{animation:sweep 4.5s ease-in-out infinite}'
        '@keyframes halo{0%,100%{opacity:.25}50%{opacity:.85}}'
        '@keyframes nudge{0%,100%{transform:translateX(0)}50%{transform:translateX(8px)}}'
        '@keyframes flick{0%,100%{transform:scale(1)}40%{transform:scale(1.12)}70%{transform:scale(.95)}}'
        f'@keyframes sweep{{0%,50%{{transform:translateX(0)}}100%{{transform:translateX({CTA_W+160}px)}}}}'
        '@media (prefers-reduced-motion:reduce){.halo,.arrow,.gem,.sweep{animation:none}.halo{opacity:.5}}'
    )
    return minify(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{CTA_W}" height="{CTA_H}" viewBox="0 0 {CTA_W} {CTA_H}" '
        f'role="img" aria-labelledby="t"><title id="t">{escape(lang["cta_title"])}</title>'
        '<defs><filter id="blur" x="-20%" y="-60%" width="140%" height="220%"><feGaussianBlur stdDeviation="7"/></filter>'
        f'<linearGradient id="sweep" x1="0" x2="1"><stop offset="0" stop-color="{c["hot"]}" stop-opacity="0"/>'
        f'<stop offset=".5" stop-color="{c["hot"]}" stop-opacity=".35"/><stop offset="1" stop-color="{c["hot"]}" stop-opacity="0"/></linearGradient>'
        f'<clipPath id="pill"><rect {pill}/></clipPath>'
        f'<style>{style}</style></defs>'
        f'<rect class="halo" {pill} fill="none" stroke="{c["hot"]}" stroke-width="8" filter="url(#blur)"/>'
        f'<rect {pill} fill="{c["surface"]}" stroke="{c["ember"]}" stroke-width="3"/>'
        f'<g clip-path="url(#pill)"><rect class="sweep" x="-160" y="0" width="140" height="{CTA_H}" fill="url(#sweep)"/></g>'
        f'<g class="gem"><path d="{diamond(gem_x, gem_y, 14, 22)}" fill="{c["ember"]}"/>'
        f'<path d="{diamond(gem_x, gem_y, 7, 11)}" fill="{c["hot"]}"/></g>'
        f'<path d="{label}" fill="{c["fg"]}"/>'
        f'<path class="arrow" d="{arrow}" fill="{c["ember"]}"/>'
        '</svg>'
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('out', nargs='?', default=Path(__file__).resolve().parent.parent / 'assets', type=Path)
    parser.add_argument('--fonts', type=Path, action='append', help='pasta extra com as fontes')
    args = parser.parse_args()

    fonts = Fonts((args.fonts or []) + FONT_DIRS)
    args.out.mkdir(parents=True, exist_ok=True)
    for lang in LANGS.values():
        for theme, colors in THEMES.items():
            (args.out / f'banner{lang["suffix"]}-{theme}.svg').write_text(build_banner(fonts, colors, lang))
            (args.out / f'botao-forja{lang["suffix"]}-{theme}.svg').write_text(build_cta(fonts, colors, lang))
    print(f'8 SVGs gerados em {args.out}')


if __name__ == '__main__':
    main()
