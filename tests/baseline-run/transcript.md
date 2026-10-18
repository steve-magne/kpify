## Ce qui s'est passé en juin : rien

**Juin n'a pas baissé — juin est incomplet.** La dernière commande du fichier date du **14 juin 2026**. Les 6 133 € de juin couvrent 14 jours, pas 30.

Normalisé par jour, juin est parfaitement dans la norme :

| mois | CA/jour | cmd/jour | panier |
|---|---|---|---|
| jan | 395 € | 7,7 | 51,28 € |
| fév | 458 € | 8,0 | 56,98 € |
| mars | 486 € | 8,1 | 59,78 € |
| avr | 440 € | 8,1 | 54,29 € |
| mai | 467 € | 8,7 | 53,63 € |
| **juin** | **456 €** | **8,9** | **51,10 €** |

Juin a même le **meilleur rythme de commandes/jour de l'année** (8,93). Extrapolé sur 30 jours : ~13 700 € — un mois normal.

## Le vrai problème, lui, est invisible dans le CA total

**L'acquisition s'effondre depuis janvier**, masquée par la montée des clients récurrents :

| | jan | fév | mars | avr | mai | juin |
|---|---|---|---|---|---|---|
| CA nouveaux clients /jour | **289 €** | 215 € | 207 € | 115 € | 72 € | **68 €** |
| CA récurrents /jour | 106 € | 243 € | 279 € | 325 € | 395 € | 388 € |

Part du CA venant de nouveaux clients : **73 % → 15 %**. Et **zéro inscription dans `customers.csv` depuis février**. Le chiffre d'affaires tient aujourd'hui uniquement sur le réachat d'une base qui ne se renouvelle plus. C'est ça qu'il faut traiter, pas juin.

Deux détails au passage : le pic de mars (486 €/j) vient en partie d'**une seule commande B2B de 1 920 €** (votre unique client `business`) — non reproductible. Et les promos ne portent rien : le CA sans promo est stable, le CA promo aussi.

## Problèmes de qualité des données à corriger

Trois défauts fausseront n'importe quel suivi tant qu'ils ne sont pas réglés :

1. **30 commandes dupliquées** (même `order_id`, même ligne entière) → +1 409 € de CA fantôme, concentrés en mai (22 sur 30). Mai est donc légèrement surévalué.
2. **39 remboursements** stockés comme commandes à montant négatif (`R0001`…), sans lignes dans `order_items.csv`. Ils plombent le panier moyen si on ne les isole pas. Total : −2 298 €.
3. **17 commandes sans `customer_id`** → impossible de les classer nouveau/récurrent (~0,5 % du CA, peu grave mais à corriger à la source).

## Ce qu'il faut suivre chaque mois

Script livré : **`monthly_kpis.py`** (stdlib seule, pas de dépendance). Il déduplique, isole les remboursements, et **normalise par jour écoulé** en marquant les mois incomplets — ce qui évite exactement l'erreur de lecture de juin.

```
python3 monthly_kpis.py          # le tableau
python3 monthly_kpis.py --check  # auto-test
```

Les métriques à regarder, par ordre d'importance :

1. **CA net par jour** (et non CA du mois) — la seule mesure comparable d'un mois à l'autre.
2. **CA nouveaux clients /jour vs récurrents /jour** — votre indicateur d'alerte n°1 aujourd'hui.
3. **Commandes/jour × panier moyen** — décompose toute variation de CA en effet volume vs effet valeur.
4. **Clients actifs /jour**.
5. **% du CA sous promo** — pour vérifier que les remises achètent vraiment de la croissance (actuellement non).
6. **Taux de remboursement** (% du CA brut) — il grimpe doucement : 2,7 % en janvier → 3,9 % en mai.

## Taux de conversion : pas calculable en l'état

Il manque le dénominateur. `orders.csv` ne contient que des commandes abouties — aucune donnée de trafic, de session ou de panier abandonné. Impossible à reconstruire a posteriori.

Pour le suivre, il faut instrumenter une seule chose : **les sessions mensuelles** (export GA4, Plausible, Shopify Analytics, selon votre stack). Ensuite :

- **Conversion = commandes / sessions** (viser 1,5–3 % en e-commerce café)
- idéalement complétée par **sessions → panier → checkout → commande**, pour savoir *où* ça fuit

Dès que vous avez un `sessions.csv` (colonnes `month,sessions`), dites-le moi : une dizaine de lignes à ajouter dans `monthly_kpis.py` et c'est intégré au tableau.

---

**Hypothèses posées** (tu n'étais pas disponible) : les lignes `R*` à montant négatif sont des remboursements et je les ai sortis du CA brut ; les `order_id` dupliqués à l'identique sont des erreurs d'export et non deux vraies commandes ; les jours sans commande comptent comme des jours d'activité dans la moyenne. Si l'une de ces lectures est fausse, le correctif tient en une ligne dans `clean()`.

**Non livré** : le dashboard visuel — sa publication demandait ton approbation. Dis-le moi et je le publie.
