-- Ratio Legis — le sort d'un amendement, lu là où chaque chambre l'écrit
-- Justification : docs/30-sort-des-amendements.md
--
-- Le sort est déjà en base : 33 217 amendements le portent. Il n'était ni
-- lisible, ni comparable, ni rendu.
--
-- **Il n'est pas au même endroit dans les deux chambres.** Améli publie une
-- colonne « Sort ». L'Assemblée en publie une aussi, vide pour 1 149 de ses
-- 11 115 amendements — et ces 1 149 ne sont pas des sorts inconnus : l'état
-- procédural, colonne voisine, en dit 694 retirés et 447 irrecevables, et n'en
-- laisse que 8 en attente. Ne lire que `sort` faisait afficher **zéro
-- irrecevabilité à l'Assemblée** quand le Sénat en affiche 1 735 : un lecteur en
-- aurait tiré une conclusion fausse sur l'usage de l'irrecevabilité par les deux
-- chambres.
--
-- **Les libellés ne sont pas comparables.** « Adopté » et « Adopté - vote
-- unique » sont le même sort ; « Irrecevable art. 40 C » et « Irrecevable art.
-- 45, al. 1 C (cavalier) » sont deux motifs opposés — l'un est financier, l'autre
-- dit que l'amendement était hors sujet. Le libellé source est conservé verbatim
-- à côté de la famille : la famille sert à compter, le libellé à citer.
--
-- **La provenance du sort est une donnée.** `source` dit dans quelle colonne il a
-- été lu, parce qu'un sort déduit de l'état procédural ne vaut pas un sort
-- publié comme tel, et que la restitution doit pouvoir le dire.

PRAGMA foreign_keys = ON;

DROP VIEW  IF EXISTS tentative_sur_article;
DROP VIEW  IF EXISTS sort_par_chambre;
DROP TABLE IF EXISTS sort_amendement;

CREATE TABLE sort_amendement (
    amendement_id  INTEGER PRIMARY KEY REFERENCES amendement,
    famille        TEXT NOT NULL CHECK (famille IN (
                       'adopte', 'rejete', 'retire', 'non_soutenu', 'tombe',
                       'irrecevable', 'non_statue', 'inconnu')),
    -- Le fondement de l'irrecevabilité, quand la chambre le déclare : article 40
    -- pour la charge publique, article 45 pour le cavalier, article 41 pour le
    -- domaine réglementaire. L'Assemblée écrit « Irrecevable » sans motif ; la
    -- colonne est alors vide, et ne doit pas être devinée.
    motif          TEXT,
    libelle        TEXT,        -- le libellé source, verbatim
    source         TEXT CHECK (source IN ('sort', 'etat')),
    CHECK ((libelle IS NULL) = (source IS NULL)),
    CHECK (motif IS NULL OR famille = 'irrecevable')
) STRICT;

CREATE INDEX sort_par_famille ON sort_amendement (famille);

CREATE VIEW sort_par_chambre AS
    SELECT am.chambre, s.famille, count(*) AS amendements,
           sum(s.source = 'etat') AS lus_dans_l_etat
    FROM sort_amendement s JOIN amendement am ON am.id = s.amendement_id
    GROUP BY 1, 2 ORDER BY 1, 3 DESC;

-- Ce qu'un légiste consulte avant de rédiger : tout ce qui a été tenté sur un
-- article, avec son auteur, son sort et le motif de son échec. `vise` porte la
-- cible déclarée par le dispositif ; `resulte_de` dit, parmi ces tentatives,
-- lesquelles ont effectivement écrit un alinéa qui subsiste.
CREATE VIEW tentative_sur_article AS
    SELECT a.numero          AS article,
           am.id             AS amendement_id,
           am.numero         AS amendement,
           am.chambre        AS chambre,
           s.famille         AS famille,
           s.motif           AS motif,
           s.libelle         AS sort_publie,
           s.source          AS sort_lu_dans,
           ac.nom            AS auteur,
           ac.groupe         AS groupe,
           -- Sous-requêtes, non jointure : un dossier peut avoir produit deux
           -- textes au Journal officiel, et la jointure dupliquerait alors la
           -- tentative — un même amendement compté deux fois dans un décompte
           -- d'hygiène est un chiffre faux.
           (SELECT t.titre FROM issu_de i JOIN texte_normatif t
              ON t.id_jorf = i.texte_id WHERE i.dossier_id = am.dossier_id
              ORDER BY t.date_texte, t.id_jorf LIMIT 1)          AS loi,
           (SELECT t.date_texte FROM issu_de i JOIN texte_normatif t
              ON t.id_jorf = i.texte_id WHERE i.dossier_id = am.dossier_id
              ORDER BY t.date_texte, t.id_jorf LIMIT 1)          AS date_texte,
           am.subdivision    AS article_du_texte,
           am.objet          AS objet,
           am.url            AS url,
           v.formule         AS formule,
           v.confiance       AS confiance
    FROM vise v
    JOIN article a      ON a.id  = v.article_id
    JOIN amendement am  ON am.id = v.amendement_id
    JOIN sort_amendement s ON s.amendement_id = am.id
    LEFT JOIN acteur ac ON ac.id = am.auteur_id;
