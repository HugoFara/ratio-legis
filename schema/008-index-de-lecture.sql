-- Index de lecture, et statistiques du planificateur.
--
-- Le schéma des sept premières tranches ne portait que les index nécessaires à
-- l'ingestion. La restitution interroge autrement : elle part toujours du
-- **numéro d'article**, et remonte des chaînes récursives. Or `article` n'était
-- indexé que par le couple (code, numero) — un préfixe inutilisable pour une
-- recherche sur le seul numéro.
--
-- Ces index ne changent aucun résultat. Ils ne sont pas dans les fichiers de
-- schéma des tranches parce qu'ils ne servent qu'à la lecture, et qu'un index
-- pendant l'ingestion se paie à chaque insertion.

CREATE INDEX IF NOT EXISTS article_par_numero      ON article (numero);
CREATE INDEX IF NOT EXISTS motive_par_article      ON motive (article_id);
CREATE INDEX IF NOT EXISTS motive_par_segment      ON motive (segment_id);
CREATE INDEX IF NOT EXISTS renumerote_par_ancien   ON renumerote_de (ancien_id);
CREATE INDEX IF NOT EXISTS repris_de_par_source    ON repris_de (segment_source_id);
CREATE INDEX IF NOT EXISTS produite_par_par_texte  ON produite_par (texte_id);
CREATE INDEX IF NOT EXISTS considerant_par_celex   ON considerant (celex, rang);
CREATE INDEX IF NOT EXISTS cite_acte_ue_par_segment ON cite_acte_ue (segment_id);
