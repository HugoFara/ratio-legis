-- Ratio Legis — les considérants des actes de l'Union
-- Justification : docs/14-considerants.md
--
-- Le « pourquoi » du droit de l'Union est écrit, numéroté et publié. Un
-- considérant de directive est l'exposé des motifs que le droit français n'a
-- pas : l'exposé des motifs d'un projet de loi ne nomme l'article que dans 6,4 %
-- des cas, l'étude d'impact dans 24,8 %, alors qu'un acte de l'Union motive
-- systématiquement ce qu'il édicte, en tête de son propre texte.
--
-- La segmentation n'est pas à faire : EUR-Lex publie chaque acte en HTML
-- structuré selon ELI, où chaque considérant porte `id="rct_N"` et chaque article
-- `id="art_N"`, N étant le numéro imprimé. C'est une structure **déclarée**.
-- Aucune heuristique de découpage n'intervient, contrairement aux rapports
-- parlementaires, où elle avait coûté quatre défauts silencieux (`docs/07`).

PRAGMA foreign_keys = ON;

DROP VIEW  IF EXISTS motivation_europeenne;
DROP TABLE IF EXISTS considerant;
DROP TABLE IF EXISTS article_acte_ue;

-- Un considérant motive l'acte entier, jamais un article français en
-- particulier. Aucune arête ne le relie à un article du code : le lien passe par
-- l'acte, et la restitution doit dire à quel grain elle parle.
--
-- `rang` est l'ordre de lecture, toujours connu. `numero` est le numéro
-- **imprimé**, et il est nul pour les actes antérieurs à la numérotation des
-- considérants : ceux-là enchaînent « considérant que … ; qu'il convient … »
-- sans numéroter. Combler ce nul par le rang donnerait un numéro d'apparence
-- officielle qui ne figure nulle part dans l'original.
CREATE TABLE considerant (
    celex     TEXT NOT NULL REFERENCES acte_ue,
    rang      INTEGER NOT NULL,
    numero    INTEGER,
    texte     TEXT NOT NULL,
    url       TEXT NOT NULL,          -- ancre ELI quand l'acte en porte une
    PRIMARY KEY (celex, rang),
    CHECK (length(texte) > 0)
) STRICT;

-- Les articles de l'acte servent à résoudre `cite_acte_ue.article_cite` : quand
-- le code français dit « l'article 23 du règlement (CE) n° 1008/2008 », on peut
-- nommer et atteindre cet article-là. Un numéro qui ne s'y retrouve pas est
-- effacé de `cite_acte_ue` plutôt que publié.
CREATE TABLE article_acte_ue (
    celex     TEXT NOT NULL REFERENCES acte_ue,
    numero    TEXT NOT NULL,
    intitule  TEXT,
    url       TEXT NOT NULL,
    PRIMARY KEY (celex, numero)
) STRICT;

-- Ce que le droit de l'Union donne comme motif, pour un article en vigueur du
-- code, avec le grain rappelé par la colonne `porte_sur`.
CREATE VIEW motivation_europeenne AS
    SELECT p.article        AS article,
           c.celex          AS celex,
           u.denomination   AS denomination,
           c.rang           AS rang,
           c.numero         AS considerant,
           c.texte          AS texte,
           c.url            AS url,
           'acte entier'    AS porte_sur
    FROM union_par_article p
    JOIN considerant c ON c.celex = p.celex
    JOIN acte_ue u     ON u.celex = c.celex;
