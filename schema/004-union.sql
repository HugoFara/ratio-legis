-- Ratio Legis — la couche européenne
-- Justification : docs/13-couche-europeenne.md
--
-- Le code de la consommation est l'un des codes les plus européens du droit
-- français : 280 actes de l'Union sont cités dans son texte. Jusqu'ici le graphe
-- n'en portait aucun. Quand la vraie réponse à « pourquoi cet article dit ceci »
-- était « parce que la directive 2011/83/UE l'impose », le produit répondait par
-- le silence — et le silence, ici, se lit « aucune raison documentée ». C'était
-- faux, et c'est le seul endroit du projet où nous rendions un résultat faux.
--
-- Les tables `acte_ue` et `transpose` existaient depuis le § 3 de la feuille de
-- route, vides. Elles sont redéfinies ici plutôt qu'altérées : rien ne les
-- peuplait, donc rien ne se perd, et le fichier reste lisible d'un bloc.

PRAGMA foreign_keys = ON;

DROP VIEW  IF EXISTS union_par_article;
DROP TABLE IF EXISTS cite_acte_ue;
DROP TABLE IF EXISTS transpose;
DROP TABLE IF EXISTS acte_ue;

-- Le CELEX n'est pas recopié d'une source : il est *construit* depuis le numéro
-- cité en français, puis **vérifié** auprès de Cellar, le service d'identifiants
-- de l'Office des publications. Un identifiant construit et non vérifié serait
-- une invention plausible, exactement ce que le § 5.1 interdit ; `verifie_le`
-- porte donc la date de cette vérification et ne peut pas être nulle.
--
-- `denomination` est la forme littérale la plus fréquemment observée dans le
-- corpus — « règlement (CE) n° 2006/2004 » — et non une forme reconstruite. Le
-- suffixe correct (CEE, CE, UE) dépend de la date de l'acte et de traités
-- successifs ; le déduire serait deviner. Ce que le législateur français a écrit
-- est déjà dans nos sources, et il fait autorité pour l'affichage.
CREATE TABLE acte_ue (
    celex         TEXT PRIMARY KEY,
    type_acte     TEXT NOT NULL CHECK (type_acte IN
                      ('directive', 'reglement', 'decision')),
    annee         INTEGER NOT NULL,
    numero        INTEGER NOT NULL,
    denomination  TEXT NOT NULL,
    url           TEXT NOT NULL,
    verifie_le    TEXT NOT NULL,
    considerants  TEXT,                        -- JSON, non peuplé à ce stade
    CHECK (celex GLOB '3[0-9][0-9][0-9][0-9][LRD][0-9][0-9][0-9][0-9]')
) STRICT;

-- Un texte français déclare transposer une directive : la mention est dans son
-- intitulé complet au Journal officiel. C'est une déclaration de l'auteur du
-- texte, pas une déduction — d'où `declaree` par défaut.
CREATE TABLE transpose (
    texte_id   TEXT NOT NULL REFERENCES texte_normatif,
    celex      TEXT NOT NULL REFERENCES acte_ue,
    methode    TEXT NOT NULL DEFAULT 'declaree'
               CHECK (methode IN ('declaree', 'derivee', 'inferee')),
    confiance  REAL NOT NULL CHECK (confiance BETWEEN 0 AND 1),
    preuve_id  INTEGER REFERENCES preuve,
    PRIMARY KEY (texte_id, celex),
    CHECK (methode = 'declaree' OR preuve_id IS NOT NULL)
) STRICT;

-- Citer n'est ni transposer, ni appliquer, ni être fondé sur. Un article qui
-- renvoie au règlement (UE) 2017/2394 ne le transpose pas — un règlement ne se
-- transpose pas — et un article qui cite une directive pour l'écarter la cite
-- tout autant. Cette table dit seulement : *le texte de cet alinéa nomme cet
-- acte, à cet endroit*. C'est un fait vérifiable ; la qualification du lien ne
-- l'est pas, et n'est donc pas inventée. La restitution doit tenir ce mot.
--
-- `article_cite` n'est renseigné que lorsque la fenêtre qui précède l'acte nomme
-- **un seul** article, sans énumération : « De l'article 23 du règlement (CE)
-- n° 1008/2008 ». 150 citations sur 1 478 sont dans ce cas. Les autres en nomment
-- souvent plusieurs, par plages et par suffixes (« des articles 5 ter, 8, 9 et
-- 16 »), et une première version qui tentait de les découper attribuait à un acte
-- les articles de l'acte cité juste avant. Le champ reste nul plutôt que faux.
CREATE TABLE cite_acte_ue (
    id            INTEGER PRIMARY KEY,
    segment_id    TEXT NOT NULL REFERENCES segment,
    celex         TEXT NOT NULL REFERENCES acte_ue,
    article_cite  TEXT,
    offset_debut  INTEGER NOT NULL,
    offset_fin    INTEGER NOT NULL,
    methode       TEXT NOT NULL DEFAULT 'derivee'
                  CHECK (methode IN ('declaree', 'derivee', 'inferee')),
    confiance     REAL NOT NULL CHECK (confiance BETWEEN 0 AND 1),
    preuve_id     INTEGER REFERENCES preuve,
    UNIQUE (segment_id, celex, offset_debut),
    CHECK (offset_fin > offset_debut),
    CHECK (methode = 'declaree' OR preuve_id IS NOT NULL)
) STRICT;

CREATE INDEX cite_acte_ue_par_acte ON cite_acte_ue (celex);

-- Ce que le droit de l'Union impose à un article donné, au grain de l'article et
-- restreint aux versions en vigueur : la vue que consulte le citoyen.
CREATE VIEW union_par_article AS
    SELECT a.numero        AS article,
           c.celex         AS celex,
           c.article_cite  AS article_cite,
           u.denomination  AS denomination,
           u.type_acte     AS type_acte,
           u.url           AS url,
           c.segment_id    AS segment_citant,
           c.preuve_id     AS preuve_id
    FROM cite_acte_ue c
    JOIN acte_ue u          ON u.celex = c.celex
    JOIN segment s          ON s.id = c.segment_id
    JOIN version_en_vigueur v ON v.id_legi = s.version_id
    JOIN article a          ON a.id = v.article_id;
