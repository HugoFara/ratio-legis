-- Ratio Legis — graphe de provenance normative
-- Révision du § 3 de la feuille de route au grain du segment.
-- Justification des choix : docs/06-modele-de-donnees.md
--
-- SQLite. Le § 6 de la feuille de route recommandait PostgreSQL avec pg_trgm et
-- pgvector ; le volume ne le justifie pas — 1 280 articles cibles, quelques
-- centaines de milliers de lignes au total. La contrepartie est assumée :
-- l'alignement par trigrammes et le rappel vectoriel de la phase 3 devront
-- s'appuyer sur FTS5 et sur un index externe, non sur le moteur.
--
-- Tables STRICT : sans elles SQLite accepte n'importe quel type dans n'importe
-- quelle colonne, ce qui rendrait les contraintes de ce fichier décoratives.
--
-- À exécuter avec  PRAGMA foreign_keys = ON;  les clefs étrangères ne sont pas
-- appliquées par défaut.

PRAGMA foreign_keys = ON;

-- --------------------------------------------------------------------- nœuds

-- Un article n'est pas un numéro. 285 numéros du code en vigueur ont désigné
-- une autre disposition avant le 1er juillet 2016 — L313-10 fut le cautionnement
-- disproportionné de 1993 à 2016, il est la fiche standardisée d'information
-- depuis — et le nœud clé par numéro les confondait : l'historique de l'un
-- devenait celui de l'autre, et un rapport de 2010 commentant le cautionnement
-- « motivait » la fiche standardisée. `docs/02` § 7 l'avait écrit : résoudre par
-- identifiant, jamais par numéro. La **lignée** est ce qui manquait : le rang de
-- la disposition qui a porté ce numéro, incrémenté à chaque discontinuité —
-- numéro abrogé, puis recréé avec un texte sans rapport (`legi_vers_graphe.py`).
-- La lignée la plus haute est celle d'aujourd'hui ; `article_courant` la sert à
-- tout ce qui entre par un numéro sans date.
CREATE TABLE article (
    id      INTEGER PRIMARY KEY,
    code    TEXT NOT NULL,
    numero  TEXT NOT NULL,
    lignee  INTEGER NOT NULL DEFAULT 1,
    UNIQUE (code, numero, lignee)
) STRICT;


CREATE TABLE version_article (
    id_legi     TEXT PRIMARY KEY,              -- LEGIARTI…
    article_id  INTEGER NOT NULL REFERENCES article,
    date_debut  TEXT NOT NULL,
    date_fin    TEXT,
    etat        TEXT NOT NULL,
    texte       TEXT NOT NULL,
    hash        TEXT NOT NULL
) STRICT;

CREATE INDEX version_article_par_article ON version_article (article_id, date_debut);

-- Période couverte par chaque lignée, pour résoudre un numéro cité par un
-- document daté : le rapport de 2010 qui nomme L313-10 parle de la lignée qui
-- portait ce numéro en 2010.
CREATE VIEW periode_article AS
    SELECT article_id, min(date_debut) AS debut,
           max(coalesce(date_fin, '9999-12-31')) AS fin
    FROM version_article
    WHERE etat NOT IN ('MODIFIE_MORT_NE', 'ANNULE')
    GROUP BY article_id;

-- La lignée d'aujourd'hui : la plus haute parmi celles qui ont eu une version
-- vivante — une lignée faite d'une seule version mort-née ne compte pas.
CREATE VIEW article_courant AS
    SELECT id, code, numero, lignee FROM article a
    WHERE lignee = (SELECT max(b.lignee) FROM article b
                    JOIN periode_article p ON p.article_id = b.id
                    WHERE b.code = a.code AND b.numero = a.numero);

-- Un segment est un alinéa. Le fonds LEGI ne le balise pas de façon fiable :
-- 26,5 % des articles n'ont aucune balise <p> et le fonds compte deux fois plus
-- de <br/> que de <p>. Le découpage combine les deux.
--
-- L'identité d'un segment n'est pas stable entre versions : insérer un alinéa
-- décale tous les suivants. La continuité est portée par l'arête repris_de, pas
-- par une clef partagée.
CREATE TABLE segment (
    id            TEXT PRIMARY KEY,            -- <id_legi>:<ordre>
    version_id    TEXT NOT NULL REFERENCES version_article,
    ordre         INTEGER NOT NULL,
    texte         TEXT NOT NULL,
    offset_debut  INTEGER NOT NULL,
    offset_fin    INTEGER NOT NULL,
    hash          TEXT NOT NULL,
    UNIQUE (version_id, ordre),
    CHECK (offset_fin > offset_debut)
) STRICT;

-- Sous 60 caractères, l'appariement textuel n'a aucun pouvoir discriminant.
-- 16,7 % des segments sont dans ce cas : ils existent et sont restitués, mais ne
-- peuvent pas porter d'arête dérivée. Pour eux, l'absence de provenance est une
-- limite de méthode et doit être présentée comme telle, jamais comme une absence
-- de motivation.
CREATE VIEW segment_non_appariable AS
    SELECT id, version_id, ordre FROM segment WHERE length(texte) < 60;

-- Recherche plein texte. Remplace l'index trigramme de PostgreSQL : sert au
-- rappel de candidats, jamais à établir un fait (règle § 5.5).
CREATE VIRTUAL TABLE segment_fts USING fts5 (
    texte,
    content = 'segment',
    content_rowid = 'rowid'
);

CREATE TABLE texte_normatif (
    id_jorf     TEXT PRIMARY KEY,
    nature      TEXT NOT NULL CHECK (nature IN ('loi', 'ordonnance', 'decret', 'arrete')),
    date_texte  TEXT NOT NULL,
    titre       TEXT NOT NULL
) STRICT;

CREATE TABLE dossier (
    id_dole      TEXT PRIMARY KEY,
    id_an        TEXT,
    id_senat     TEXT,
    titre        TEXT NOT NULL,
    legislature  INTEGER
) STRICT;

-- Remplace ExposeDesMotifs, EtudeImpact et AvisConseilEtat du § 3, qui étaient
-- trois nœuds pour un même objet. Deux types manquaient et ce sont les plus
-- utiles : le rapport de commission nomme l'article dans 79,1 % des cas, contre
-- 24,8 % pour l'étude d'impact et 6,4 % pour l'exposé des motifs.
CREATE TABLE document (
    id                 INTEGER PRIMARY KEY,
    dossier_id         TEXT REFERENCES dossier,
    texte_normatif_id  TEXT REFERENCES texte_normatif,
    type               TEXT NOT NULL CHECK (type IN (
                           'expose_des_motifs', 'etude_impact', 'avis_conseil_etat',
                           'rapport_commission', 'rapport_president_republique',
                           'compte_rendu')),
    url                TEXT NOT NULL,
    texte              TEXT NOT NULL,
    hash               TEXT NOT NULL,
    date_recuperation  TEXT NOT NULL,
    CHECK (dossier_id IS NOT NULL OR texte_normatif_id IS NOT NULL)
) STRICT;

CREATE TABLE acteur (
    id      INTEGER PRIMARY KEY,
    nom     TEXT NOT NULL,
    groupe  TEXT
) STRICT;

-- `texte_discute` n'était pas au § 3 et la donnée l'impose : un dossier passe
-- plusieurs textes en navette, et chacun renumérote ses amendements à partir de
-- 1. La clef (dossier, chambre, numéro) du § 3 fait donc collisionner l'amendement
-- n° 1 de première lecture avec celui de deuxième lecture.
CREATE TABLE amendement (
    id             INTEGER PRIMARY KEY,
    dossier_id     TEXT NOT NULL REFERENCES dossier,
    chambre        TEXT NOT NULL CHECK (chambre IN ('assemblee', 'senat')),
    texte_discute  TEXT NOT NULL,
    numero         TEXT NOT NULL,
    auteur_id      INTEGER REFERENCES acteur,
    sort           TEXT,
    -- L'état procédural, distinct du sort et publié par la seule Assemblée. Il
    -- porte le sort de 1 143 amendements dont la colonne `sort` est vide — 694
    -- retirés, 449 déclarés irrecevables. Les confondre serait faux, ignorer
    -- celui-ci l'était davantage : l'Assemblée paraissait ne rien déclarer
    -- irrecevable. Voir `ingestion/sort_des_amendements.py`.
    etat           TEXT,
    subdivision    TEXT,      -- article du PROJET de loi, jamais du code
    objet          TEXT,
    dispositif     TEXT,
    url            TEXT,      -- § 4.3 : toute pièce doit rester citable
    UNIQUE (dossier_id, chambre, texte_discute, numero)
) STRICT;

CREATE TABLE acte_ue (
    celex         TEXT PRIMARY KEY,
    type_acte     TEXT,
    considerants  TEXT          -- JSON
) STRICT;

-- Rend la confiance vérifiable plutôt que déclarative (règle § 5.4) : une arête
-- dérivée porte la fenêtre de texte qui l'a produite, de sorte que la décision
-- puisse être rejouée. Une fenêtre de moins de 60 caractères ne prouve rien.
CREATE TABLE preuve (
    id             INTEGER PRIMARY KEY,
    methode        TEXT NOT NULL,
    fenetre        TEXT NOT NULL,
    source_offset  INTEGER,
    cible_offset   INTEGER,
    CHECK (length(fenetre) >= 60)
) STRICT;

-- -------------------------------------------------------------------- arêtes

-- Couverture mesurée : 99,0 % du périmètre, sans inférence.
CREATE TABLE produite_par (
    version_id  TEXT NOT NULL REFERENCES version_article,
    texte_id    TEXT NOT NULL REFERENCES texte_normatif,
    type_lien   TEXT NOT NULL,
    methode     TEXT NOT NULL DEFAULT 'declaree'
                CHECK (methode IN ('declaree', 'derivee', 'inferee')),
    confiance   REAL NOT NULL DEFAULT 1.0 CHECK (confiance BETWEEN 0 AND 1),
    PRIMARY KEY (version_id, texte_id, type_lien)
) STRICT;

-- Déclarée par LEGI via CONCORDANCE, CONCORDE, TRANSFERE, DEPLACE : 76,4 % du
-- périmètre. Les tables de concordance PDF prévues au § 4 sont donc inutiles
-- pour l'essentiel du corpus.
CREATE TABLE renumerote_de (
    article_id  INTEGER NOT NULL REFERENCES article,
    ancien_id   INTEGER NOT NULL REFERENCES article,
    methode     TEXT NOT NULL DEFAULT 'declaree'
                CHECK (methode IN ('declaree', 'derivee', 'inferee')),
    confiance   REAL NOT NULL DEFAULT 1.0 CHECK (confiance BETWEEN 0 AND 1),
    PRIMARY KEY (article_id, ancien_id),
    CHECK (article_id <> ancien_id)
) STRICT;

CREATE TABLE issu_de (
    texte_id    TEXT PRIMARY KEY REFERENCES texte_normatif,
    dossier_id  TEXT NOT NULL REFERENCES dossier,
    methode     TEXT NOT NULL DEFAULT 'declaree'
                CHECK (methode IN ('declaree', 'derivee', 'inferee'))
) STRICT;

-- L'arête critique du projet. Elle part du SEGMENT et non de la version
-- d'article : sur les 307 articles issus de la loi de 2014, aucun n'a plus cette
-- loi comme texte producteur de sa version en vigueur. Attachée à l'article,
-- elle serait vide par construction sur un corpus recodifié.
CREATE TABLE resulte_de (
    segment_id     TEXT NOT NULL REFERENCES segment,
    amendement_id  INTEGER NOT NULL REFERENCES amendement,
    methode        TEXT NOT NULL
                   CHECK (methode IN ('declaree', 'derivee', 'inferee')),
    confiance      REAL NOT NULL CHECK (confiance BETWEEN 0 AND 1),
    preuve_id      INTEGER REFERENCES preuve,
    PRIMARY KEY (segment_id, amendement_id),
    -- Règle § 5.1 : provenance ou silence. Une arête dérivée sans preuve est
    -- refusée à l'écriture, pas signalée à la lecture.
    CHECK (methode = 'declaree' OR preuve_id IS NOT NULL)
) STRICT;

-- Porte la continuité d'un alinéa entre deux versions, notamment à travers une
-- recodification. Sans elle, impossible de dire « cet alinéa vient de cet
-- amendement de 2013, repris sans modification de fond en 2016 » sans mentir sur
-- la chaîne. `part_reprise` distingue l'alinéa repris tel quel de l'alinéa
-- retouché — 20,9 % des segments mesurés.
CREATE TABLE repris_de (
    segment_id         TEXT NOT NULL REFERENCES segment,
    segment_source_id  TEXT NOT NULL REFERENCES segment,
    part_reprise       REAL NOT NULL CHECK (part_reprise BETWEEN 0 AND 1),
    methode            TEXT NOT NULL DEFAULT 'derivee'
                       CHECK (methode IN ('declaree', 'derivee', 'inferee')),
    preuve_id          INTEGER REFERENCES preuve,
    PRIMARY KEY (segment_id, segment_source_id),
    CHECK (methode = 'declaree' OR preuve_id IS NOT NULL)
) STRICT;

-- Les offsets sont obligatoires : le § 4.3 interdit toute phrase produite sans
-- citation résoluble au niveau du passage. Une motivation sans offsets ne peut
-- pas être citée, donc ne doit pas exister.
--
-- La cible est un segment OU un article : le rapport au Président de la
-- République ne nomme l'article que dans 2 cas sur 25, il motive l'ordonnance
-- entière et la restitution doit le dire.
CREATE TABLE motive (
    id                INTEGER PRIMARY KEY,
    document_id       INTEGER NOT NULL REFERENCES document,
    -- Article du TEXTE en discussion que commente la section, jamais du code.
    -- Sans lui, impossible de confronter un amendement au commentaire censé le
    -- motiver : c'est la seule clef structurelle commune aux deux.
    article_du_texte  TEXT,
    segment_id    TEXT REFERENCES segment,
    article_id    INTEGER REFERENCES article,
    offset_debut  INTEGER NOT NULL,
    offset_fin    INTEGER NOT NULL,
    methode       TEXT NOT NULL
                  CHECK (methode IN ('declaree', 'derivee', 'inferee')),
    confiance     REAL NOT NULL CHECK (confiance BETWEEN 0 AND 1),
    preuve_id     INTEGER REFERENCES preuve,
    CHECK ((segment_id IS NULL) + (article_id IS NULL) = 1),
    CHECK (offset_fin > offset_debut),
    CHECK (methode = 'declaree' OR preuve_id IS NOT NULL)
) STRICT;

CREATE TABLE transpose (
    texte_id   TEXT NOT NULL REFERENCES texte_normatif,
    celex      TEXT NOT NULL REFERENCES acte_ue,
    methode    TEXT NOT NULL DEFAULT 'derivee'
               CHECK (methode IN ('declaree', 'derivee', 'inferee')),
    confiance  REAL NOT NULL CHECK (confiance BETWEEN 0 AND 1),
    preuve_id  INTEGER REFERENCES preuve,
    PRIMARY KEY (texte_id, celex),
    CHECK (methode = 'declaree' OR preuve_id IS NOT NULL)
) STRICT;
