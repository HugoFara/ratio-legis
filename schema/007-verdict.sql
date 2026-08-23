-- Ratio Legis — le verdict, et ce qu'il permet de compter
-- Justification : docs/18-verdict-et-hygiene.md
--
-- Le § 4.3 de la feuille de route donne au produit un verdict explicite —
-- **`raison non documentée`** — et en fait « un résultat de premier ordre, pas un
-- échec ». Douze tranches plus tard, il n'était rendu nulle part : la restitution
-- affichait ce qu'elle savait, et se taisait sur ce qu'elle ne savait pas, ce qui
-- n'est pas la même chose que le dire.
--
-- Le verdict retient **le grain le plus fin disponible**, dans cet ordre :
--
--   passage_motivant      un passage explique cet article — commentaire de rapport
--                         qui le nomme, ou amendement qui a écrit l'alinéa
--   origine_situee        aucun passage, mais on sait sous quel article de quel
--                         texte il a été discuté
--   motivation_du_texte   ni l'un ni l'autre, mais un document motive le texte
--                         entier, ou un acte de l'Union le commande
--   raison_non_documentee rien
--
-- Les trois derniers ne sont pas des échecs de méthode : ce sont des états du
-- fonds documentaire français, et le dernier est le plus intéressant des quatre.

PRAGMA foreign_keys = ON;

DROP VIEW  IF EXISTS hygiene_par_partie;
DROP TABLE IF EXISTS verdict;

CREATE TABLE verdict (
    article_id           INTEGER PRIMARY KEY REFERENCES article,
    partie               TEXT NOT NULL CHECK (partie IN ('L', 'R', 'D')),
    verdict              TEXT NOT NULL CHECK (verdict IN (
                             'passage_motivant', 'origine_situee',
                             'motivation_du_texte', 'raison_non_documentee')),
    -- Les cinq voies, indépendamment du verdict retenu : le verdict dit la
    -- meilleure, ces colonnes disent toutes celles qui existent.
    a_passage_motivant   INTEGER NOT NULL CHECK (a_passage_motivant IN (0, 1)),
    a_amendement         INTEGER NOT NULL CHECK (a_amendement IN (0, 1)),
    a_article_du_texte   INTEGER NOT NULL CHECK (a_article_du_texte IN (0, 1)),
    a_document_du_texte  INTEGER NOT NULL CHECK (a_document_du_texte IN (0, 1)),
    a_acte_ue            INTEGER NOT NULL CHECK (a_acte_ue IN (0, 1))
) STRICT;

CREATE INDEX verdict_par_classe ON verdict (verdict);

-- La partie réglementaire n'a ni exposé des motifs, ni débat, ni amendement :
-- son silence est structurel, celui de la partie législative ne l'est pas. Les
-- confondre dans un taux unique produit un chiffre qui ne veut rien dire.
CREATE VIEW hygiene_par_partie AS
    SELECT partie,
           count(*)                                                   AS articles,
           sum(verdict = 'passage_motivant')                          AS motives,
           sum(verdict = 'origine_situee')                            AS situes,
           sum(verdict = 'motivation_du_texte')                       AS texte_seul,
           sum(verdict = 'raison_non_documentee')                     AS non_documentes,
           round(100.0 * sum(verdict = 'raison_non_documentee') / count(*), 1)
                                                                      AS part_muette
    FROM verdict GROUP BY partie ORDER BY partie;
