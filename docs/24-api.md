# Dix-huitième tranche — l'API de lecture

**Objet :** le second livrable du § 4.4.
**Date : 23 août 2026.**
**Code :** `restitution/api.py`. **Dépendances :** `pip install '.[api]'`.

---

## 1. Elle n'expose rien de neuf

`restitution/graphe.py` savait déjà remonter la provenance d'un article ;
`restitution/note.py` savait déjà la rédiger sous le contrat du § 4.3. L'API les
rend interrogeables et **impose trois choses que la ligne de commande laissait à
l'appelant**.

Elle n'a été possible qu'après la seizième tranche : à 425 ms par article, aucune
API n'était sérieuse. Elle répond aujourd'hui en **12 ms de médiane et 21 ms au
95ᵉ centile**, bout en bout, HTTP compris.

## 2. L'attribution voyage avec la donnée

`ATTRIBUTION.md` en fait une obligation de licence, pas une politesse : elle
« doit apparaître dans l'interface, dans l'API et dans tout export du graphe ».

- chaque réponse porte `X-Attribution`, `X-Licence` et `X-Avertissement` ;
- chaque charge utile porte un bloc `mentions` complet ;
- `/attribution` les donne en entier.

Une donnée ouverte qu'on peut consommer sans jamais voir d'où elle vient n'est
pas attribuée.

**Piège rencontré :** un en-tête HTTP ne transporte que du latin-1. Le tiret
cadratin et le symbole © des mentions complètes faisaient échouer la réponse
entière avec un 500. L'en-tête porte donc une forme courte sans accent, et le
texte exact reste dans la charge utile.

## 3. Le produit n'interprète pas, et le redit

Le § 0 en fait un non-objectif, le § 8 un risque de positionnement. Une API se
consomme sans lire le README : chaque réponse porte donc, en clair, que le
service documente la provenance et ne produit ni interprétation juridique ni
conseil, et que la donnée ne fait pas foi.

## 4. Une connexion par requête

SQLite n'est pas sûr entre fils d'exécution, et FastAPI exécute les fonctions
synchrones dans un pool. Partager une connexion marcherait presque toujours — ce
qui est la pire des situations. La base est ouverte en **lecture seule**, une
connexion par requête, refermée à la fin. Le coût est négligeable devant les
9 ms de la requête elle-même.

## 5. Points d'entrée

| | |
|---|---|
| `GET /articles` | les articles en vigueur, filtrables par partie et par verdict, paginés par curseur |
| `GET /articles/{numero}` | la fiche de provenance complète |
| `GET /articles/{numero}/note` | la note « pourquoi cet article », sous contrat |
| `GET /articles/{numero}/note.html` | la même, en HTML |
| `GET /articles/{numero}/graphe.txt` | le graphe brut, arête par arête |
| `GET /mesures` | les métriques d'hygiène |
| `GET /attribution`, `/sante`, `/docs` | mentions, état de la base, OpenAPI |

`/sante` rend la table `diffusion` quand la base servie vient d'un dump : mode,
licence, horodatage et **commit du code qui l'a produite**. Servir un dump sans
pouvoir dire quel code l'a écrit reviendrait à publier une mesure sans son
protocole.

## 6. Servir le dump, et non la base de travail

L'API a été éprouvée sur les deux. Sur le dump, les passages non rediffusés
apparaissent tels quels :

> « Un rapport de commission de l'Assemblée nationale commente cet article. »
> citation : *texte non rediffusé dans cette base — le document reste à son URL*
> offsets : 726908–729979

La référence reste résoluble — URL et offsets — et le lecteur sait pourquoi le
passage n'est pas là. C'est le comportement voulu : le contrat du § 4.3 exige une
citation résoluble, pas une citation recopiée.
