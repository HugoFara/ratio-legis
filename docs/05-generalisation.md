# Généralisation du pilote aux 48 dossiers du périmètre

**Objet :** vérifier si les chiffres du prototype, établis sur une seule loi,
tiennent sur l'ensemble du périmètre avant d'engager la phase 1.
**Date : 22 août 2026.**
**Code :** `tools/prototype/generalisation.py`.
**Sortie :** `data/prototype/generalisation-perimetre.csv`, un dossier par ligne.

---

## 1. Pourquoi cette étape

Le prototype (`03-prototype-resolveur.md`) ne portait que sur la loi 2014-344,
soit 307 des 832 articles éligibles. Trois chiffres structurants en dépendaient et
tout le dimensionnement de la phase 2 reposait dessus. Un pilote sur 37 % du
périmètre, et sur une loi de consommation particulièrement bien préparée, n'est
pas une preuve.

Corpus constitué pour cette mesure : **316 rapports de commission**, **126 textes
déposés**, **61 jeux d'amendements Améli**, répartis sur les 48 dossiers qui
produisent les 832 articles éligibles.

## 2. Le pilote était optimiste sur les trois mesures

| Mesure | Pilote (307 articles) | Périmètre (832 articles) |
|---|---:|---:|
| Ancrage par un commentaire de rapport | 94,1 % | **79,1 %** |
| Part issue du texte déposé | 68 % | **40,8 %** |
| Part issue de la navette | 32 % | **59,2 %** |
| C1 — rattachement à un amendement du Sénat | 29,3 % | **13,8 %** |

**La population qui a besoin de l'arête critique double**, de 32 % à 59 % du
périmètre. Le prototype concluait que `resulte_de` n'était requise que sur un
tiers du corpus ; c'est près des deux tiers. La charge de la phase 2 est à
réviser en conséquence.

Le rattachement effectif tombe de 29,3 % à 13,8 %. Sur les 832 articles
éligibles, **39 portent aujourd'hui une chaîne complète** allant de l'article en
vigueur jusqu'à un amendement nommé, contre 10 au terme du pilote.

## 3. Le résultat central : 40 % du corpus est dans une zone grise

C'est le résultat qui compte, et il n'était pas visible sur un seul dossier.

La partition « issu du texte déposé » / « issu de la navette » **n'est pas
définie au grain de l'article**. Selon la finesse d'échantillonnage retenue pour
comparer le texte de l'article au texte déposé, la même mesure a successivement
donné 68 %, 82,7 % puis 40,8 % — sans que rien ne change sur le fond. Ce n'était
pas une mesure, c'était un artefact de seuil.

En remplaçant le booléen par la **part du texte de l'article retrouvée dans le
texte déposé**, la distribution apparaît :

| Part du texte de l'article retrouvée | Articles | Part |
|---|---:|---:|
| Plus de 90 % — repris tel quel | 183 | 24,1 % |
| **De 10 à 90 % — zone grise** | **302** | **39,8 %** |
| Moins de 10 % | 142 | 18,7 % |
| Aucune fenêtre commune — entièrement parlementaire | 131 | 17,3 % |

**Deux articles sur cinq sont partiellement gouvernementaux et partiellement
parlementaires.** Pour ceux-là, la question « cet article vient-il du
Gouvernement ou du Parlement ? » n'a pas de réponse : les deux, selon l'alinéa.

Conséquence directe, et elle tranche une décision restée ouverte : **la
provenance doit être modélisée au segment, pas à l'article.** Ce n'était jusqu'ici
qu'un argument de principe tiré des 19,5 textes modificateurs par article ; c'est
désormais une mesure. Toute métrique de couverture au grain de l'article — C1
compris — décrira mal 40 % du corpus, quelle que soit la qualité du code.

## 4. L'ancrage documentaire est bimodal

79,1 % en agrégat, mais la moyenne masque tout :

| | |
|---|---:|
| Médiane par dossier | **42 %** |
| Premier quartile | 0 % |
| Troisième quartile | 100 % |
| Dossiers à 0 % d'ancrage | 21 (92 articles) |
| Dossiers à 100 % | 16 |

Les dix dossiers les plus lourds portent 636 articles, soit 76 % du périmètre, et
sont bien couverts. Les 21 dossiers sans aucun ancrage ne pèsent que 92 articles.

C'est une bonne nouvelle pour le dimensionnement — traiter dix dossiers couvre les
trois quarts du périmètre — et une mauvaise pour la promesse produit : sur la
queue de distribution, la réponse sera « raison non documentée » et elle le
restera.

## 5. Trois pièges de récupération, et ce qu'ils ont coûté

Tous trois ont produit des chiffres faux sans lever d'erreur. Ils sont notés ici
parce que la phase 1 les rencontrera à nouveau.

**Redirection HTTP non suivie.** `curl --fail` sans `-L` rejette la redirection
http → https que pratiquent les deux assemblées. Coût : deux tiers du corpus
manquants, silencieusement. Symptôme trompeur : le script annonçait « 79 rapports
récupérés » sans erreur.

**Fermeture TLS sans `close_notify`.** Le serveur du Sénat clôt la connexion sans
alerte de fin ; curl sort en erreur 56 alors que le corps est complet. Un script
qui se fie au code de sortie supprime des fichiers valides. Il faut se fier au
code HTTP et à la taille.

**Index à offsets alignés.** Indexer les deux côtés d'un appariement par fenêtres
à pas fixe ne marche pas : les grilles d'offsets ne coïncident jamais. Cette
erreur a fait tomber C1 de 29 % à 5 % sans qu'aucune donnée ne change. Un côté au
moins doit être balayé au pas de 1.

Le troisième est le plus instructif : il produisait un résultat plausible et
faux, du même ordre de grandeur que les vrais chiffres. Seule la comparaison avec
le pilote, qui donnait 29 rattachements sur le même dossier, l'a révélé. **Toute
mesure de phase 2 doit conserver un cas de référence vérifié à la main**, sans
quoi ce type d'erreur passe.

## 6. Limite de méthode à connaître

Le « texte déposé » n'est pas uniformément le texte initial du Gouvernement. Les
liens de DOLE pointent, selon les dossiers, vers le projet déposé à l'Assemblée
(`/projets/pl…`) ou vers le texte transmis au Sénat (`/leg/pjl…`) — lequel a déjà
été amendé par la première chambre.

Pour les dossiers du second type, une part de la « reprise » attribuée au texte
déposé recouvre en réalité du travail parlementaire de l'Assemblée. **La part
gouvernementale de 40,8 % est donc une borne haute**, et la part navette de 59,2 %
une borne basse. Corriger cela suppose de distinguer, pour chaque dossier, le
texte de dépôt initial des textes intermédiaires — travail de phase 1, pas de
phase 0.

## 7. Ce que cela change

1. **La décision segment / article est tranchée par la mesure** : segment. Elle
   conditionne le schéma relationnel et doit être actée avant toute ingestion.
2. **La charge de la phase 2 double** : l'arête `resulte_de` est requise sur 59 %
   du périmètre, non 32 %.
3. **C1 n'est pas un bon critère go/no-go au grain de l'article.** Il faut le
   redéfinir au grain du segment, ou l'accompagner de la distribution de reprise
   qui, elle, est stable.
4. **Le dimensionnement du dépouillement est favorable** : dix dossiers couvrent
   76 % du périmètre.
5. **L'extracteur d'amendements AN reste justifié** : 387 des 449 articles issus
   de la navette ne sont rattachés à aucun amendement du Sénat, et l'Assemblée est
   la chambre de dépôt de la plupart de ces textes.
