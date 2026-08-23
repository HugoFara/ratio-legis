-- Ratio Legis — les textes en discussion et ce sur quoi ils portent
-- Justification : docs/16-textes-discutes.md
--
-- Le chaînon manquant du projet. Le graphe savait ce qu'un **article du code**
-- était devenu, et ce qu'un **article du texte en discussion** avait suscité — un
-- amendement s'y dépose, un rapport le commente, une étude d'impact le chiffre.
-- Il ne savait pas relier les deux, et ce lien n'est écrit qu'à un seul endroit :
-- le texte lui-même, « L'article L. 121-1 du code de la consommation est ainsi
-- modifié ».
--
-- Trois chantiers en dépendaient : rattacher l'étude d'impact et l'exposé des
-- motifs au grain de l'article (`docs/15` § 5), rattraper les amendements qui
-- insèrent sans nommer de code (`docs/09`), et donner un ancrage français aux
-- tableaux de concordance des directives.

PRAGMA foreign_keys = ON;

DROP VIEW  IF EXISTS articles_du_texte;
DROP TABLE IF EXISTS porte_sur;
DROP TABLE IF EXISTS texte_discute;

-- Un état du texte, à un stade de la navette. Le stade est le libellé que DOLE
-- lui donne, repris tel quel : « Texte adopté en 1ère lecture par l'Assemblée
-- nationale le 12 juillet 2013 ». Le reformuler perdrait la date, qui est le
-- seul moyen d'ordonner deux états d'une même chambre.
CREATE TABLE texte_discute (
    id          TEXT PRIMARY KEY,          -- chemin d'origine, législature comprise
    dossier_id  TEXT NOT NULL REFERENCES dossier,
    chambre     TEXT NOT NULL CHECK (chambre IN ('assemblee', 'senat')),
    stade       TEXT NOT NULL,
    url         TEXT NOT NULL,
    articles    INTEGER NOT NULL CHECK (articles >= 0)
) STRICT;

-- « L'article N de ce texte porte sur l'article L. X du code. » Rien de plus :
-- porter sur n'est ni créer, ni modifier, ni abroger. Le texte le dit — « est
-- ainsi modifié », « est complété par », « est abrogé » — mais le verbe se
-- rattache à la subdivision, pas à l'article cité, et une même phrase en enchaîne
-- plusieurs. Qualifier demanderait de découper le langage modificatif ; ce n'est
-- pas fait, donc ce n'est pas prétendu.
--
-- La portée dit ce qu'on sait de la cible, comme pour `renvoie_a` :
--   interne      résolue dans le fonds
--   externe      un autre code, nommé dans le texte
--   non_resolue  aucun code nommé, ou numéro absent du fonds
CREATE TABLE porte_sur (
    id                INTEGER PRIMARY KEY,
    texte_id          TEXT NOT NULL REFERENCES texte_discute,
    article_du_texte  TEXT NOT NULL,
    article_id        INTEGER REFERENCES article,
    numero_cite       TEXT NOT NULL,
    code_cite         TEXT,
    portee            TEXT NOT NULL CHECK (portee IN
                          ('interne', 'externe', 'non_resolue')),
    methode           TEXT NOT NULL DEFAULT 'derivee'
                      CHECK (methode IN ('declaree', 'derivee', 'inferee')),
    confiance         REAL NOT NULL CHECK (confiance BETWEEN 0 AND 1),
    preuve_id         INTEGER REFERENCES preuve,
    UNIQUE (texte_id, article_du_texte, numero_cite),
    CHECK ((article_id IS NOT NULL) = (portee = 'interne')),
    CHECK (methode = 'declaree' OR preuve_id IS NOT NULL)
) STRICT;

CREATE INDEX porte_sur_par_article ON porte_sur (article_id);
CREATE INDEX porte_sur_par_texte   ON porte_sur (texte_id, article_du_texte);

-- Pour un article du code en vigueur : quels articles de quels textes, à quel
-- stade, l'ont eu pour objet. C'est la clef qui manquait pour confronter un
-- article à l'étude d'impact et à l'exposé des motifs qui le concernent.
--
-- La descendance par `renumerote_de` est indispensable, et c'est elle qui porte
-- l'essentiel : un texte de 2014 vise L. 121-42, que la recodification de 2016 a
-- fait L. 224-43. Sans la chaîne, 204 articles en vigueur sont atteints ; avec
-- elle, 807. C'est la même leçon que pour `motive` (`docs/07`) : sur un corpus
-- recodifié, la cible nommée par le texte n'existe presque jamais sous ce numéro
-- aujourd'hui. `direct` dit laquelle des deux voies a servi.
CREATE VIEW articles_du_texte AS
    WITH RECURSIVE descendance(origine, courant) AS (
        SELECT id, id FROM article
        UNION
        SELECT d.origine, r.article_id
        FROM renumerote_de r JOIN descendance d ON r.ancien_id = d.courant)
    SELECT a.numero                         AS article,
           t.dossier_id                     AS dossier,
           t.chambre                        AS chambre,
           t.stade                          AS stade,
           p.article_du_texte               AS article_du_texte,
           p.numero_cite                    AS numero_cite,
           (p.article_id = d.courant)       AS direct,
           t.url                            AS url,
           p.preuve_id                      AS preuve_id
    FROM porte_sur p
    JOIN descendance d     ON d.origine = p.article_id
    JOIN article a         ON a.id = d.courant
    JOIN texte_discute t   ON t.id = p.texte_id
    JOIN version_en_vigueur v ON v.article_id = a.id;
