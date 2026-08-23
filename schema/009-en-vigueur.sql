-- « En vigueur aujourd'hui » : une seule définition, au lieu de dix-sept.
--
-- Le test employé partout était `etat = 'VIGUEUR'`. Il a marché tant que le fonds
-- extrait datait de juillet 2025. La réincrémentation quotidienne (docs/26) a
-- ramené les états **différés** que LEGI publie à l'avance, et 243 articles ont
-- disparu du corpus d'un coup :
--
--   ABROGE_DIFF   cette version sera abrogée à `date_fin`. Jusque-là, elle est
--                 en vigueur — 187 articles étaient dans ce cas, abrogés au
--                 20 novembre 2026, donc bel et bien applicables aujourd'hui ;
--   VIGUEUR_DIFF  cette version entrera en vigueur à `date_debut`. Elle ne l'est
--                 pas encore, et `etat = 'VIGUEUR'` ne la retenait pas non plus
--                 — le seul cas où l'ancien test tombait juste ;
--   MODIFIE_MORT_NE, ANNULE   versions qui n'ont jamais pris effet.
--
-- L'état dit **ce qui arrivera**, les dates disent **quand**. C'est donc aux
-- dates qu'il faut poser la question, et à l'état seulement d'écarter ce qui n'a
-- jamais eu d'existence.
--
-- La vue est évaluée à la lecture, non à la construction : `date('now')`. C'est
-- voulu — l'objet du projet est « un article de code en vigueur **aujourd'hui** ».
-- Un dump relu après le 20 novembre 2026 cessera de son propre chef de compter
-- ces 187 articles, ce qui sera juste.
--
-- `row_number()` garantit au plus une version par article : le fonds en présente
-- un cas où deux versions se chevauchent, et un graphe de provenance ne peut pas
-- se permettre de rendre deux textes pour un même article.

DROP VIEW IF EXISTS version_en_vigueur;
CREATE VIEW version_en_vigueur AS
SELECT id_legi, article_id, date_debut, date_fin, etat, texte, hash
FROM (SELECT *, row_number() OVER (PARTITION BY article_id
                                   ORDER BY date_debut DESC, id_legi) AS rang
      FROM version_article
      WHERE etat NOT IN ('MODIFIE_MORT_NE', 'ANNULE')
        AND date_debut <= date('now')
        AND (date_fin IS NULL OR date_fin > date('now')))
WHERE rang = 1;
