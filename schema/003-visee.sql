-- Ratio Legis — ce qu'un amendement visait, adopté ou non
-- Justification : docs/10-amendements-non-adoptes.md
--
-- `resulte_de` ne relie que les amendements dont le texte a survécu. Elle ne dit
-- rien des 5 913 amendements rejetés, 3 638 retirés, 795 déclarés irrecevables au
-- titre de l'article 40 et 597 au titre de l'article 45. Or c'est ce corpus qui
-- intéresse le législateur : ce qui a déjà été tenté sur un article, et ce qui l'a
-- fait échouer.
--
-- La cible est ici **déclarée**, pas inférée : le dispositif nomme l'article et la
-- formule de modification qui le vise. Aucun appariement textuel n'intervient, et
-- l'arête vaut donc pour un amendement qui n'a jamais produit une ligne de droit.

PRAGMA foreign_keys = ON;

CREATE TABLE vise (
    amendement_id  INTEGER NOT NULL REFERENCES amendement,
    article_id     INTEGER NOT NULL REFERENCES article,
    formule        TEXT NOT NULL,     -- la formule de modification relevée
    methode        TEXT NOT NULL DEFAULT 'declaree'
                   CHECK (methode IN ('declaree', 'derivee', 'inferee')),
    confiance      REAL NOT NULL CHECK (confiance BETWEEN 0 AND 1),
    preuve_id      INTEGER REFERENCES preuve,
    PRIMARY KEY (amendement_id, article_id),
    CHECK (methode = 'declaree' OR preuve_id IS NOT NULL)
) STRICT;

CREATE INDEX vise_par_article ON vise (article_id);

-- Ce qu'un législateur consulte avant de rédiger : tout ce qui a été tenté sur un
-- article, avec l'auteur, le sort et l'objet.
CREATE VIEW historique_article AS
    SELECT a.numero        AS article,
           am.numero       AS amendement,
           am.sort         AS sort,
           ac.nom          AS auteur,
           ac.groupe       AS groupe,
           t.titre         AS loi,
           am.objet        AS objet,
           am.url          AS url,
           v.formule       AS formule
    FROM vise v
    JOIN article a     ON a.id = v.article_id
    JOIN amendement am ON am.id = v.amendement_id
    LEFT JOIN acteur ac ON ac.id = am.auteur_id
    LEFT JOIN issu_de i ON i.dossier_id = am.dossier_id
    LEFT JOIN texte_normatif t ON t.id_jorf = i.texte_id;
