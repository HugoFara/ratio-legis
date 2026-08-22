-- Ratio Legis — graphe de provenance normative
-- Révision du § 3 de la feuille de route au grain du segment.
-- Justification des choix : docs/06-modele-de-donnees.md
--
-- PostgreSQL 16. pg_trgm sert à l'alignement textuel, pgvector à la seule
-- recherche de candidats — jamais à établir un fait (règle § 5.5).

CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- ---------------------------------------------------------------- référentiel

CREATE TYPE methode_arete AS ENUM ('declaree', 'derivee', 'inferee');

CREATE TYPE type_document AS ENUM (
    'expose_des_motifs',
    'etude_impact',
    'avis_conseil_etat',
    'rapport_commission',
    'rapport_president_republique',
    'compte_rendu'
);

CREATE TYPE nature_texte AS ENUM ('loi', 'ordonnance', 'decret', 'arrete');

-- --------------------------------------------------------------------- nœuds

CREATE TABLE article (
    id          bigserial PRIMARY KEY,
    code        text NOT NULL,
    numero      text NOT NULL,
    UNIQUE (code, numero)
);

CREATE TABLE version_article (
    id_legi     text PRIMARY KEY,              -- LEGIARTI…
    article_id  bigint NOT NULL REFERENCES article,
    date_debut  date NOT NULL,
    date_fin    date,
    etat        text NOT NULL,
    texte       text NOT NULL,
    hash        bytea NOT NULL
);
CREATE INDEX ON version_article (article_id, date_debut);

-- Un segment est un alinéa. Le fonds LEGI ne le balise pas de façon fiable :
-- 26,5 % des articles n'ont aucune balise <p> et le fonds compte deux fois plus
-- de <br/> que de <p>. Le découpage combine les deux.
--
-- L'identité d'un segment n'est pas stable entre versions : insérer un alinéa
-- décale tous les suivants. La continuité est portée par l'arête repris_de, pas
-- par une clef partagée.
CREATE TABLE segment (
    id            bigserial PRIMARY KEY,
    version_id    text NOT NULL REFERENCES version_article,
    ordre         int NOT NULL,
    texte         text NOT NULL,
    offset_debut  int NOT NULL,
    offset_fin    int NOT NULL,
    hash          bytea NOT NULL,
    UNIQUE (version_id, ordre)
);
CREATE INDEX ON segment USING gin (texte gin_trgm_ops);

-- Sous 60 caractères, l'appariement textuel n'a aucun pouvoir discriminant.
-- 16,7 % des segments sont dans ce cas : ils existent et sont restitués, mais ne
-- peuvent pas porter d'arête dérivée. Pour eux, l'absence de provenance est une
-- limite de méthode et doit être présentée comme telle, jamais comme une absence
-- de motivation.
CREATE VIEW segment_non_appariable AS
    SELECT id, version_id, ordre FROM segment WHERE length(texte) < 60;

CREATE TABLE texte_normatif (
    id_jorf     text PRIMARY KEY,
    nature      nature_texte NOT NULL,
    date_texte  date NOT NULL,
    titre       text NOT NULL
);

CREATE TABLE dossier (
    id_dole     text PRIMARY KEY,
    id_an       text,
    id_senat    text,
    titre       text NOT NULL,
    legislature int
);

-- Remplace ExposeDesMotifs, EtudeImpact et AvisConseilEtat du § 3, qui étaient
-- trois nœuds pour un même objet. Deux types manquaient et ce sont les plus
-- utiles : le rapport de commission nomme l'article dans 79,1 % des cas, contre
-- 24,8 % pour l'étude d'impact et 6,4 % pour l'exposé des motifs.
CREATE TABLE document (
    id                 bigserial PRIMARY KEY,
    dossier_id         text REFERENCES dossier,
    texte_normatif_id  text REFERENCES texte_normatif,
    type               type_document NOT NULL,
    url                text NOT NULL,
    texte              text NOT NULL,
    hash               bytea NOT NULL,
    date_recuperation  timestamptz NOT NULL,
    CHECK (dossier_id IS NOT NULL OR texte_normatif_id IS NOT NULL)
);

CREATE TABLE acteur (
    id      bigserial PRIMARY KEY,
    nom     text NOT NULL,
    groupe  text
);

CREATE TABLE amendement (
    id           bigserial PRIMARY KEY,
    dossier_id   text NOT NULL REFERENCES dossier,
    chambre      text NOT NULL CHECK (chambre IN ('assemblee', 'senat')),
    numero       text NOT NULL,
    auteur_id    bigint REFERENCES acteur,
    sort         text,
    subdivision  text,      -- article du PROJET de loi, jamais du code
    objet        text,
    dispositif   text,
    UNIQUE (dossier_id, chambre, numero)
);

CREATE TABLE acte_ue (
    celex         text PRIMARY KEY,
    type_acte     text,
    considerants  jsonb
);

-- Rend la confiance vérifiable plutôt que déclarative (règle § 5.4) : une arête
-- dérivée porte la fenêtre de texte qui l'a produite et les offsets des deux
-- côtés, de sorte que la décision puisse être rejouée.
CREATE TABLE preuve (
    id              bigserial PRIMARY KEY,
    methode         text NOT NULL,
    fenetre         text NOT NULL,
    source_offset   int,
    cible_offset    int,
    CHECK (length(fenetre) >= 60)
);

-- -------------------------------------------------------------------- arêtes

-- Couverture mesurée : 99,0 % du périmètre, sans inférence.
CREATE TABLE produite_par (
    version_id  text NOT NULL REFERENCES version_article,
    texte_id    text NOT NULL REFERENCES texte_normatif,
    type_lien   text NOT NULL,
    methode     methode_arete NOT NULL DEFAULT 'declaree',
    confiance   real NOT NULL DEFAULT 1.0,
    PRIMARY KEY (version_id, texte_id, type_lien)
);

-- Déclarée par LEGI via CONCORDANCE, CONCORDE, TRANSFERE, DEPLACE : 76,4 % du
-- périmètre. Les tables de concordance PDF prévues au § 4 sont donc inutiles
-- pour l'essentiel du corpus.
CREATE TABLE renumerote_de (
    article_id   bigint NOT NULL REFERENCES article,
    ancien_id    bigint NOT NULL REFERENCES article,
    methode      methode_arete NOT NULL DEFAULT 'declaree',
    confiance    real NOT NULL DEFAULT 1.0,
    PRIMARY KEY (article_id, ancien_id)
);

CREATE TABLE issu_de (
    texte_id    text PRIMARY KEY REFERENCES texte_normatif,
    dossier_id  text NOT NULL REFERENCES dossier,
    methode     methode_arete NOT NULL DEFAULT 'declaree'
);

-- L'arête critique du projet. Elle part du SEGMENT et non de la version
-- d'article : sur les 307 articles issus de la loi de 2014, aucun n'a plus
-- cette loi comme texte producteur de sa version en vigueur. Attachée à
-- l'article, elle serait vide par construction sur un corpus recodifié.
CREATE TABLE resulte_de (
    segment_id     bigint NOT NULL REFERENCES segment,
    amendement_id  bigint NOT NULL REFERENCES amendement,
    methode        methode_arete NOT NULL,
    confiance      real NOT NULL CHECK (confiance BETWEEN 0 AND 1),
    preuve_id      bigint REFERENCES preuve,
    PRIMARY KEY (segment_id, amendement_id),
    -- Règle § 5.1 : provenance ou silence. Une arête dérivée sans preuve est
    -- refusée à l'écriture, pas signalée à la lecture.
    CHECK (methode = 'declaree' OR preuve_id IS NOT NULL)
);

-- Porte la continuité d'un alinéa entre deux versions, notamment à travers une
-- recodification. Sans elle, impossible de dire « cet alinéa vient de cet
-- amendement de 2013, repris sans modification de fond en 2016 » sans mentir
-- sur la chaîne.
CREATE TABLE repris_de (
    segment_id         bigint NOT NULL REFERENCES segment,
    segment_source_id  bigint NOT NULL REFERENCES segment,
    part_reprise       real NOT NULL CHECK (part_reprise BETWEEN 0 AND 1),
    methode            methode_arete NOT NULL DEFAULT 'derivee',
    preuve_id          bigint REFERENCES preuve,
    PRIMARY KEY (segment_id, segment_source_id),
    CHECK (methode = 'declaree' OR preuve_id IS NOT NULL)
);

-- Les offsets sont obligatoires : le § 4.3 interdit toute phrase produite sans
-- citation résoluble au niveau du passage. Une motivation sans offsets ne peut
-- pas être citée, donc ne doit pas exister.
--
-- La cible est un segment OU un article : le rapport au Président de la
-- République ne nomme l'article que dans 2 cas sur 25, il motive l'ordonnance
-- entière et la restitution doit le dire.
CREATE TABLE motive (
    id            bigserial PRIMARY KEY,
    document_id   bigint NOT NULL REFERENCES document,
    segment_id    bigint REFERENCES segment,
    article_id    bigint REFERENCES article,
    offset_debut  int NOT NULL,
    offset_fin    int NOT NULL,
    methode       methode_arete NOT NULL,
    confiance     real NOT NULL CHECK (confiance BETWEEN 0 AND 1),
    preuve_id     bigint REFERENCES preuve,
    CHECK (num_nonnulls(segment_id, article_id) = 1),
    CHECK (offset_fin > offset_debut),
    CHECK (methode = 'declaree' OR preuve_id IS NOT NULL)
);

CREATE TABLE transpose (
    texte_id   text NOT NULL REFERENCES texte_normatif,
    celex      text NOT NULL REFERENCES acte_ue,
    methode    methode_arete NOT NULL DEFAULT 'derivee',
    confiance  real NOT NULL,
    preuve_id  bigint REFERENCES preuve,
    PRIMARY KEY (texte_id, celex)
);
