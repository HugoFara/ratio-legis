# Sixième tranche — l'Assemblée nationale entre en base

**Objet :** charger les amendements de la chambre de dépôt, absente jusqu'ici.
**Date : 23 août 2026.**
**Code :** `tools/an/extraire_amendements_an.py`, `ingestion/an_vers_amendements.py`.

---

## 1. Ce que la tranche change

| | Avant | Après |
|---|---:|---:|
| Amendements en base | 19 078 | **30 193** |
| dont Assemblée · Sénat | 0 · 19 078 | 11 115 · 19 078 |
| Acteurs | 933 | 1 359 |
| Arêtes `resulte_de` | 164 | **293** |
| **Articles en vigueur remontant à un amendement** | 53 | **90** |
| Arêtes `vise` · articles visés | 162 · 107 | 194 · 123 |

Base complète : 196 Mo.

```
L111-1   ←  amdt 768 (assemblée, adopté)  M. Frédéric Barbier
L113-1   ←  amdt 198 (assemblée, adopté)  M. Philippe Noguès
L122-19  ←  amdt 981 (assemblée, adopté)  LE GOUVERNEMENT
```

Ces chaînes n'existaient pas : elles partent d'un article en vigueur, traversent
la recodification de 2016, et aboutissent à un député nommé.

## 2. Trois identités confondues, 2 116 amendements perdus en silence

Le fichier de l'Assemblée compte 624 colonnes et n'est pas conçu pour être lu par
clef naturelle. Trois fois de suite, une clef trop courte a fait disparaître des
amendements à l'insertion, sans erreur ni avertissement.

**Le sort n'est pas dans la colonne `sort`.** Celle-ci est vide sur toute la
législature ; le sort est dans `sort[1]/sortEnSeance[1]`. La colonne `etat[1]` ne
porte que l'état procédural — « Discuté », « Irrecevable » — et la prendre pour le
sort aurait fait disparaître 3 280 rejets derrière un « Discuté » uniforme.

**Le même numéro désigne deux amendements selon l'organe d'examen.** Amendement
n° 2 du texte 2964 : « Supprimer l'alinéa 26 », adopté, en séance ; et « Supprimer
cet article », retiré, en commission. 2 098 couples (texte, numéro) en double.

**Le même numéro désigne deux amendements selon le stade du texte.** `B2736`
est le texte déposé, `BTC2736` le texte issu de la commission. Un motif qui tolère
`BTC` sans le capturer les écrase : 2 032 amendements de plus.

Après correction, 11 115 amendements sur 11 117 extraits entrent en base. Les deux
manquants sont de vrais doublons de la source.

## 3. Deux choses que la donnée ne dit pas

**Les signataires ne sont pas nommés.** Le fichier ne porte que des références —
`PA267551` pour l'acteur, `PO…` pour le groupe. Elles se résolvent par le jeu
Acteurs historique de l'Assemblée, 3 117 personnes et 63 groupes politiques, qui
couvre les législatures depuis la XIe. Sans lui, les 11 115 amendements auraient
un sort mais pas d'auteur — c'est-à-dire la moitié de la promesse produit. 97
signataires restent non résolus.

**Aucune URL n'est fabriquée.** Les anciennes adresses (`/14/amendements/1015/AN/…asp`)
rendent 404 et le schéma `/dyn/` ne les sert pas. Écrire une adresse plausible mais
morte contreviendrait au § 4.3, qui exige une citation résoluble : le champ reste
vide et l'amendement est cité par son numéro, son texte et son organe d'examen.

## 4. Confiance révisée à 0,7102

L'échantillon vérifié à la main passe à 26 arêtes `resulte_de` — 14 au Sénat, 12 à
l'Assemblée — pour 23 succès. La borne inférieure de Wilson à 95 % monte de 0,6853
à 0,7102 : la précision n'a pas changé, l'échantillon a grandi.

Les échecs restants sont d'un seul type et il est identifié : un amendement qui
crée un article dans un autre code, sans que ce code soit nommé dans le
dispositif. Le contexte est porté par l'article du projet de loi, pas par
l'amendement. Le résoudre suppose de charger les textes déposés, déjà récupérés
en phase 0.

## 5. Ce qui reste

**La XIIIe législature**, 216 articles éligibles, n'a jamais été publiée en open
data. Ses pages d'amendement subsistent une à une dans la Wayback Machine.

**Les législatures XV à XVII** — 103 articles éligibles — sont disponibles au même
format et n'ont pas été chargées : 1,3 Go, pour un gain proportionnellement
faible.

**Le sort n'est pas exploité en restitution.** 12 681 amendements rejetés et 795
irrecevabilités au titre de l'article 40 sont en base ; c'est le produit
législateur qui reste à écrire, pas la donnée qui manque.
