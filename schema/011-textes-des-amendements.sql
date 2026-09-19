-- Ratio Legis — la correspondance des identifiants de texte, et ce qu'elle porte
-- Justification : docs/31-correspondance-des-textes.md
--
-- Trois corpus nomment le même document de trois façons, et `docs/16` § 6 en
-- faisait le dernier verrou : « les identifiants de texte des deux corpus ne se
-- correspondent pas — `2002-2003_166.csv` côté Sénat, `BTC1156/PO644420` côté
-- Assemblée, `senat/leg-tas07-009.html` ici. Une table de correspondance est
-- nécessaire, et elle n'est pas écrite. »
--
-- Elle l'est. Elle n'est pas devinée : le Sénat numérote ses documents par
-- (session, numéro), et c'est exactement la clef d'une URL Améli ; l'Assemblée
-- numérote les siens dans une série « b » dont la référence `B…` / `BTC…` des
-- amendements est la reprise. La correspondance est donc une **identité de
-- document**, pas un rapprochement.
--
-- Deux contrôles la vérifient, tous deux reproductibles :
--
--   - **le dossier concorde** — le texte trouvé par le numéro appartient au même
--     dossier DOLE que les amendements, 67 fois sur 67 au Sénat ;
--   - **les subdivisions tombent dans la plage** — un amendement déposé sur
--     l'article 12 suppose que le texte ait douze articles. 3 578 sur 3 655, soit
--     97,9 %. Un appariement faux se signalerait ici en premier.
--
-- Un troisième, non reproductible en une passe, a servi à trancher : apparier
-- chaque jeu à un texte tiré au hasard fait tomber la concordance des
-- subdivisions de 40,9 % à 15,3 %. Le signal n'est pas un artefact de petits
-- nombres.

PRAGMA foreign_keys = ON;

DROP VIEW  IF EXISTS depot_des_amendements;
DROP TABLE IF EXISTS depose_sur;
DROP TABLE IF EXISTS texte_des_amendements;

CREATE TABLE texte_des_amendements (
    chambre       TEXT NOT NULL CHECK (chambre IN ('assemblee', 'senat')),
    -- `amendement.texte_discute` : la clef du corpus d'amendements.
    texte_corpus  TEXT NOT NULL,
    texte_id      TEXT NOT NULL REFERENCES texte_discute,
    -- `numero_declare` : les deux identifiants désignent le même document par le
    -- même numéro, dans la même série et la même session.
    methode       TEXT NOT NULL CHECK (methode IN ('numero_declare')),
    -- Contrôle de plage, porté par la ligne : le dénominateur est le nombre de
    -- subdivisions distinctes, le numérateur celles que le texte peut contenir.
    subdivisions  INTEGER NOT NULL CHECK (subdivisions >= 0),
    dans_la_plage INTEGER NOT NULL CHECK (dans_la_plage >= 0),
    PRIMARY KEY (chambre, texte_corpus),
    CHECK (dans_la_plage <= subdivisions)
) STRICT;

-- Ce que la correspondance permet enfin d'écrire : l'amendement a été déposé sur
-- un article du texte, et cet article du texte modifie cet article du code.
--
-- **Seulement quand il n'en modifie qu'un.** Un article de projet de loi en
-- réécrit couramment plusieurs ; choisir l'un d'eux serait fabriquer une arête
-- pour combler un trou, ce que le § 3 de la feuille de route interdit. La
-- restriction est le prix de la règle « précision > rappel » du § 5.3 : elle
-- écarte 159 amendements de plus.
--
-- **Et jamais pour un article additionnel.** « art. add. après Article 19 » ne
-- vise pas l'article 19 : il vise un article qui n'existe pas encore, et dont le
-- numéro dans le code n'est pas fixé. 7 501 amendements sont dans ce cas — c'est
-- le résultat principal de la tranche, et c'est un résultat négatif.
-- **Trois voies, mesurées à part** (docs/42). La composition seule — déposé sur
-- l'article N du texte, N réécrit A et aucun autre — vaut 7 sur 15 quand on
-- lui demande ce qu'elle prétend, « l'amendement portait sur A » (docs/41) :
-- un amendement déposé sur N peut ne toucher qu'un paragraphe qui modifie un
-- autre code. Le dispositif dit presque toujours **où** il porte, par le numéro
-- d'alinéa du texte ; et l'alinéa se laisse rattacher à l'article du code que
-- le texte réécrit à cet endroit.
--
--   visee           le dispositif nomme l'article du code, et c'est celui-là
--   alinea          le dispositif nomme un alinéa de l'article du texte, et
--                   l'instruction qui gouverne cet alinéa réécrit A
--   article_entier  le dispositif porte sur tout l'article du texte
--                   (« Supprimer cet article », « Rédiger ainsi cet article »)
--                   et N ne réécrit que A
CREATE TABLE depose_sur (
    amendement_id     INTEGER NOT NULL REFERENCES amendement,
    article_id        INTEGER NOT NULL REFERENCES article,
    texte_id          TEXT NOT NULL REFERENCES texte_discute,
    article_du_texte  TEXT NOT NULL,
    voie              TEXT NOT NULL DEFAULT 'article_entier'
                      CHECK (voie IN ('visee', 'alinea', 'article_entier')),
    methode           TEXT NOT NULL DEFAULT 'derivee'
                      CHECK (methode IN ('declaree', 'derivee', 'inferee')),
    confiance         REAL NOT NULL CHECK (confiance BETWEEN 0 AND 1),
    PRIMARY KEY (amendement_id, article_id)
) STRICT;

CREATE INDEX depose_sur_par_article ON depose_sur (article_id);

CREATE VIEW depot_des_amendements AS
    SELECT a.numero          AS article,
           am.id             AS amendement_id,
           am.numero         AS amendement,
           am.chambre        AS chambre,
           d.article_du_texte,
           d.texte_id,
           d.confiance,
           s.famille, s.motif, s.libelle AS sort_publie, s.source AS sort_lu_dans,
           ac.nom AS auteur, ac.groupe,
           am.subdivision AS subdivision, am.objet, am.url,
           (SELECT t.titre FROM issu_de i JOIN texte_normatif t
              ON t.id_jorf = i.texte_id WHERE i.dossier_id = am.dossier_id
              ORDER BY t.date_texte, t.id_jorf LIMIT 1)          AS loi,
           (SELECT t.date_texte FROM issu_de i JOIN texte_normatif t
              ON t.id_jorf = i.texte_id WHERE i.dossier_id = am.dossier_id
              ORDER BY t.date_texte, t.id_jorf LIMIT 1)          AS date_texte
    FROM depose_sur d
    JOIN article a         ON a.id = d.article_id
    JOIN amendement am     ON am.id = d.amendement_id
    JOIN sort_amendement s ON s.amendement_id = am.id
    LEFT JOIN acteur ac    ON ac.id = am.auteur_id;
