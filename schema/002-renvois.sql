-- Ratio Legis — graphe de renvois entre articles
-- Justification : docs/08-graphe-de-renvois.md
--
-- Répond à la question du législateur, qui n'est pas « pourquoi cet article
-- existe » mais « si je modifie celui-ci, qu'est-ce qui bouge ». La donnée est
-- déjà dans le fonds : elle est dans le texte des articles, jamais extraite.

PRAGMA foreign_keys = ON;

-- La portée dit ce qu'on sait de la cible, et surtout ce qu'on n'en sait pas.
-- Confondre « cité hors de ce code » et « cité et introuvable » ferait passer une
-- limite de périmètre pour une incohérence du droit.
--
--   interne        cible résolue dans le fonds chargé, partie réglementaire comprise
--   externe        autre code, nommé dans le texte
--   non_resolue    numéro de ce code sans version couvrant la date de citation
--
-- Il n'y a pas de classe « réglementaire ». Une première version en avait une,
-- fondée sur la supposition que seule la partie législative était ingérée : le
-- fonds contient en réalité 1 241 articles R et 254 D, dont 670 et 168 en
-- vigueur. Elle écartait 2 133 renvois résolvables. La nature de la cible se lit
-- dans `numero_cite`, elle n'a pas à être une portée.
CREATE TABLE renvoie_a (
    id           INTEGER PRIMARY KEY,
    segment_id   TEXT NOT NULL REFERENCES segment,
    article_id   INTEGER REFERENCES article,
    numero_cite  TEXT NOT NULL,
    code_cite    TEXT,
    portee       TEXT NOT NULL CHECK (portee IN
                     ('interne', 'externe', 'non_resolue')),
    methode      TEXT NOT NULL DEFAULT 'derivee'
                 CHECK (methode IN ('declaree', 'derivee', 'inferee')),
    confiance    REAL NOT NULL CHECK (confiance BETWEEN 0 AND 1),
    preuve_id    INTEGER REFERENCES preuve,
    UNIQUE (segment_id, numero_cite),
    -- Une cible n'est renseignée que si elle a été résolue, et elle l'est
    -- toujours quand la portée dit qu'elle l'a été.
    CHECK ((article_id IS NOT NULL) = (portee = 'interne')),
    CHECK (methode = 'declaree' OR preuve_id IS NOT NULL)
) STRICT;

CREATE INDEX renvoie_a_par_cible ON renvoie_a (article_id);

-- Ce qui cite un article donné, au grain de l'article citant et restreint aux
-- versions en vigueur : c'est la vue que consulte le législateur.
CREATE VIEW renvois_entrants AS
    SELECT cible.numero      AS article_cite,
           citant.numero     AS article_citant,
           r.segment_id      AS segment_citant,
           r.preuve_id       AS preuve_id
    FROM renvoie_a r
    JOIN article cible          ON cible.id = r.article_id
    JOIN segment s              ON s.id = r.segment_id
    JOIN version_article v      ON v.id_legi = s.version_id
    JOIN article citant         ON citant.id = v.article_id
    WHERE v.etat = 'VIGUEUR';
