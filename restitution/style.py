"""La feuille de style commune aux rendus HTML.

Cinq modules rendent une page — la fiche, la note, le surlignage, les
tentatives, le retentissement — et chacun portait sa propre copie de la
feuille, qui divergeait : 16 ou 17 pixels selon la vue, des intitulés en
capitales sans-serif ici et pas là. Le socle est écrit une fois, ici ; chaque
vue n'ajoute que ce qui lui est propre.

Deux règles qu'il tient.

**Aucune police n'est chargée du réseau.** Un `@import` ou un `<link>` vers un
service de polices est une requête tierce à chaque ouverture de page, donc une
trace de lecture chez un tiers — pour un outil qui montre à un juriste ce qu'il
consulte, ce n'est pas acceptable. Les piles ci-dessous ne nomment que des
polices installées sur la machine du lecteur, et se terminent par une famille
générique : la page se lit partout, sans jamais rien demander à personne.

**Le registre est celui de l'imprimé juridique**, pas celui d'une application :
un texte en romain sur fond papier, justifié et coupé aux règles du français,
des intitulés en petites capitales espacées comme les rubriques d'un code, un
filet double sous l'en-tête comme au Journal officiel, un seul rouge sombre
pour ce qui appelle l'attention, et le vert sobre du verdict tenu. Rien
n'imite la charte de l'État — ce n'est pas une page de Légifrance, et elle ne
doit pas pouvoir être prise pour telle.
"""

# Romain pour le corps : les garaldes et réales installées d'ordinaire sur
# macOS, Windows et les distributions libres, dans cet ordre, puis le générique.
SERIF = ('"Iowan Old Style","Libertinus Serif","Linux Libertine O",'
         '"Palatino Linotype",Palatino,"Book Antiqua","Charis SIL",'
         '"Source Serif 4","Source Serif Pro",Georgia,"DejaVu Serif",serif')
# Sans pour les métadonnées — confiance, offsets, méthode — qu'on lit comme
# une donnée et non comme du texte.
SANS = 'ui-sans-serif,system-ui,"Segoe UI",Cantarell,"Noto Sans","DejaVu Sans",sans-serif'
MONO = 'ui-monospace,SFMono-Regular,Menlo,Consolas,"Liberation Mono","DejaVu Sans Mono",monospace'

SOCLE = f"""
:root{{--fond:#f9f6ef;--encre:#1b1916;--doux:#6a635a;--trait:#d9d2c4;--acc:#7a2a24;
--vert:#3b5743;--carte:#fffdf8;
--legi:#6a635a;--gouv:#7a2a24;--parl:#3b5743;--ce:#4a4374;--ue:#1e5f74}}
@media(prefers-color-scheme:dark){{:root:not([data-theme=light]){{--fond:#17161a;
--encre:#e8e4db;--doux:#9b948a;--trait:#302d34;--acc:#d9907c;--vert:#8fbb9c;
--carte:#1e1d22;--legi:#9b948a;--gouv:#d9907c;--parl:#8fbb9c;--ce:#a9a2d8;--ue:#7fc4d8}}}}
*{{box-sizing:border-box}}
html{{-webkit-text-size-adjust:100%}}
body{{margin:0;background:var(--fond);color:var(--encre);
font:17px/1.6 {SERIF};padding:2.5rem 1.25rem;
font-feature-settings:"onum","kern","liga"}}
main{{max-width:48rem;margin:0 auto}}
.rubrique{{font-variant-caps:small-caps;letter-spacing:.14em;color:var(--doux);
font-size:.9rem;margin:0 0 .35rem}}
h1{{font-weight:normal;font-size:1.9rem;line-height:1.2;margin:0 0 .4rem;
letter-spacing:-.005em}}
.chapeau{{color:var(--doux);font-size:.95rem;margin:0 0 1.6rem;
padding-bottom:.9rem;border-bottom:3px double var(--trait)}}
h2{{font-weight:normal;font-size:1rem;font-variant-caps:small-caps;letter-spacing:.12em;
color:var(--encre);margin:2.4rem 0 .9rem;padding-bottom:.35rem;
border-bottom:1px solid var(--trait)}}
.tx,.al,.cit,.passage,.objet,.raison>div:first-of-type{{text-align:justify;hyphens:auto}}
.meta,.src,.leg,.bilan,.alerte,.etiquette,.sort,.amend{{font-family:{SANS}}}
.num,.preuve,code,.puces,.onde b,.tent b{{font-family:{MONO}}}
code{{font-size:.85em}}
.num{{font-size:.72rem;color:var(--doux);letter-spacing:.04em}}
.conf,td,th{{font-variant-numeric:tabular-nums}}
.silence{{color:var(--doux);font-style:italic;font-size:.92rem;margin:.4rem 0}}
table{{width:100%;border-collapse:collapse;font-size:.9rem}}
td,th{{text-align:left;padding:.4rem .5rem;border-bottom:1px solid var(--trait);vertical-align:top}}
th{{font-weight:normal;font-variant-caps:small-caps;letter-spacing:.1em;color:var(--doux)}}
a{{color:var(--acc);text-decoration-thickness:1px;text-underline-offset:.15em}}
footer{{margin-top:3rem;padding-top:1rem;border-top:3px double var(--trait);
font-size:.82rem;color:var(--doux);text-align:justify;hyphens:auto}}
@media print{{body{{background:#fff;color:#000;padding:0}}a{{color:inherit}}}}
"""

# La rubrique au-dessus du titre, comme le nom du code en tête de page d'un
# recueil : chaque page dit de quel fonds elle parle avant de dire de quoi.
RUBRIQUE = '<p class="rubrique">Code de la consommation</p>'
