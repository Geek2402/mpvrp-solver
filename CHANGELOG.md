# Changelog - MPVRP-CC Solver

Toutes les modifications notables du projet sont documentées dans ce fichier.

## [2.0] - 2026-01-31

### ✅ Corrections Critiques
- **Calcul des coûts cumulatifs** : Correction complète de la fonction `_build_product_line()` pour calculer progressivement les coûts au lieu d'appliquer le total en bloc
- **Faux changement au retour** : Suppression du comptage incorrect de changement de produit au retour au garage
- **Affichage des produits** : Correction de l'affichage du produit au garage de retour (produit actuel au lieu de "0")

### 🔧 Modifications de l'API
- `SolutionWriter.__init__()` : Ajout du paramètre `instance` (requis pour accéder à la matrice de coûts)
- `Route.return_to_garage()` : Suppression du paramètre `return_transition_cost` (non utilisé)

### 📖 Documentation
- Ajout de `RAPPORT_COMPLET.md` : Documentation détaillée de toutes les corrections
- Ajout de `SYNTHESE_VISUELLE.md` : Vue d'ensemble visuelle des changements
- Ajout de `CORRECTIONS_MPVRP.md` : Détails techniques des corrections
- Ajout de `QUICKSTART.md` : Guide de démarrage rapide

### 🧪 Tests
- Ajout de `test_corrections.py` : Test de validation de la cohérence des coûts
- Ajout de `test_with_changes.py` : Test avec changements de produit
- Ajout d'instances de test dans `examples/`

### ✅ Validation
- Toutes les solutions passent la validation de l'API officielle MPVRP-CC
- Tests automatiques : 100% de réussite
- Instances testées : Small (0.03s), Medium (0.62s), Large (142s)

---

## [1.0] - Version Initiale

### Fonctionnalités
- Parser d'instances MPVRP-CC
- Solveur MILP optimal (PuLP + CBC/GLPK/HiGHS)
- Solveur heuristique constructif
- Générateur de fichiers solution .dat
- Interface en ligne de commande

### ⚠️ Problèmes Connus (Corrigés en v2.0)
- ❌ Coûts cumulatifs incorrects dans les fichiers solution
- ❌ Changement de produit fictif compté au retour
- ❌ Produit au garage de retour affiché comme "0"

---

## Notes de Version

### Migration de v1.0 vers v2.0

**Changement d'API Obligatoire** :
```python
# Ancien (v1.0) - NE FONCTIONNE PLUS
writer = SolutionWriter(solution, instance_name)

# Nouveau (v2.0) - REQUIS
writer = SolutionWriter(solution, instance_name, instance)
```

**Comportement Modifié** :
- Les changements de produit ne sont plus comptés au retour au garage
- Les coûts cumulatifs augmentent progressivement (au lieu d'apparaître en bloc)
- Le produit au garage de retour affiche le produit actuel (au lieu de 0)

**Compatibilité** :
- ✅ Format des fichiers d'instance : 100% compatible
- ✅ Format des fichiers solution : 100% compatible
- ⚠️ Code client : Modification requise (ajout paramètre instance)

---

## Feuille de Route

### Version 2.1 (Planifié)
- [ ] Support de solvers additionnels (Gurobi, CPLEX)
- [ ] Amélioration de l'heuristique (2-opt, 3-opt)
- [ ] Interface graphique (GUI)
- [ ] Export en format JSON/XML

### Version 3.0 (Futur)
- [ ] Parallélisation multi-thread
- [ ] Algorithmes métaheuristiques (GA, SA, ACO)
- [ ] Mode cloud/serveur
- [ ] Visualisation des routes

---

Pour plus de détails sur les corrections, consultez `docs/RAPPORT_COMPLET.md`.
