-- Ratio Legis — l'article de l'acte de l'Union que l'article du code transpose
-- Justification : docs/54-tableaux-de-concordance.md
--
-- `transpose` relie un texte à la directive qu'il déclare transposer : au grain
-- du texte. Le lien au grain de l'article n'était écrit nulle part dans le
-- corpus lu — sauf dans les annexes des études d'impact, où le Gouvernement
-- dresse le tableau de concordance : telle disposition de la directive, tel
-- article du code. Ce tableau est une déclaration de l'auteur du texte ;
-- l'alignement de ses lignes, lu dans le PDF, est notre lecture, d'où
-- `derivee` et une preuve.
--
-- Les numéros du tableau sont ceux du projet de loi (la note 36 de l'étude
-- d'impact de la loi consommation le dit), résolus à la date du dossier.

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS transpose_article (
    article_id    INTEGER NOT NULL REFERENCES article,
    celex         TEXT NOT NULL REFERENCES acte_ue,
    article_acte  TEXT NOT NULL,              -- « 2 », tel que l'acte le numérote
    paragraphe    TEXT NOT NULL DEFAULT '',   -- « 7 » pour « Art. 2-7) », sinon vide
    document_id   INTEGER NOT NULL REFERENCES document,
    page          INTEGER NOT NULL,           -- page du PDF, à partir de 1
    numero_ecrit  TEXT NOT NULL,              -- le numéro tel que le tableau l'écrit
    methode       TEXT NOT NULL DEFAULT 'derivee'
                  CHECK (methode IN ('declaree', 'derivee', 'inferee')),
    confiance     REAL NOT NULL CHECK (confiance BETWEEN 0 AND 1),
    preuve_id     INTEGER REFERENCES preuve,
    PRIMARY KEY (article_id, celex, article_acte, paragraphe, document_id),
    CHECK (methode = 'declaree' OR preuve_id IS NOT NULL)
) STRICT;
CREATE INDEX IF NOT EXISTS transpose_article_par_acte ON transpose_article (celex, article_acte);
