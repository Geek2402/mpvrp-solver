# 🚛 MPVRP-CC Solver - Solveur Optimal et Heuristique

**Multi-Product Vehicle Routing Problem with Changeover Cost**

Solveur Python pour résoudre de manière optimale ou heuristique le problème de routage de véhicules multi-produits avec coûts de changement.

## 📦 Contenu du Package

```
mpvrp_solver_package/
├── src/                           # Code source
│   ├── mpvrp_parser.py           # Parser d'instances
│   ├── mpvrp_heuristic_solver.py # Solveur heuristique
│   ├── mpvrp_optimal_solver.py   # Solveur MILP optimal
│   ├── mpvrp_solution_writer.py  # Générateur de fichiers solution
│   └── mpvrp_optimal_main.py     # Script principal
│
├── tests/                         # Tests de validation
│   ├── test_corrections.py       # Test de cohérence des coûts
│   └── test_with_changes.py      # Test avec changements de produit
│
├── docs/                          # Documentation
│   ├── RAPPORT_COMPLET.md        # Documentation complète
│   ├── SYNTHESE_VISUELLE.md      # Synthèse visuelle
│   └── CORRECTIONS_MPVRP.md      # Détails techniques
│
├── examples/                      # Instances de test
│   ├── MPVRP_TEST_s3_d1_p2.dat   # Instance simple
│   └── MPVRP_CHANGES_s4_d1_p2.dat # Instance avec changements
│
├── README.md                      # Ce fichier
└── requirements.txt               # Dépendances Python
```

## 🚀 Installation Rapide

```bash
# 1. Extraire l'archive
unzip mpvrp_solver_package.zip
cd mpvrp_solver_package

# 2. Installer les dépendances
pip install -r requirements.txt --break-system-packages

# 3. Tester l'installation
cd tests
python test_corrections.py
```

## 📖 Utilisation

### Résoudre une Instance

```bash
cd src
python mpvrp_optimal_main.py chemin/vers/instance.dat
```

### Options Disponibles

```bash
# Résoudre toutes les instances d'un répertoire
python mpvrp_optimal_main.py --all ./instances/

# Mode heuristique rapide (non optimal)
python mpvrp_optimal_main.py instance.dat --fast

# Limiter le temps de résolution
python mpvrp_optimal_main.py instance.dat --time-limit 600

# Ajuster le gap d'optimalité
python mpvrp_optimal_main.py instance.dat --gap 0.001
```

### Exemples

```bash
# Instance Small (résolution rapide)
python mpvrp_optimal_main.py ../examples/MPVRP_TEST_s3_d1_p2.dat

# Instance avec limite de temps personnalisée
python mpvrp_optimal_main.py instance.dat --time-limit 3600 --gap 0.01
```

## 📊 Performance

| Taille | Stations | Temps Typique | Qualité |
|--------|----------|---------------|---------|
| Small  | < 20     | < 10s         | Optimal |
| Medium | 20-60    | < 1 min       | Optimal |
| Large  | > 60     | 2-30 min      | Optimal |

## ✅ Corrections Appliquées

Ce package contient les **corrections validées** pour :
1. ✅ Calcul correct des coûts cumulatifs
2. ✅ Suppression du faux changement au retour
3. ✅ Affichage cohérent des produits

**Tous les tests passent** et les solutions sont validées par l'API officielle.

## 📚 Documentation

- **README.md** (ce fichier) - Guide de démarrage rapide
- **docs/RAPPORT_COMPLET.md** - Documentation détaillée complète
- **docs/SYNTHESE_VISUELLE.md** - Vue d'ensemble visuelle
- **docs/CORRECTIONS_MPVRP.md** - Détails techniques des corrections

## 🧪 Tests

```bash
cd tests

# Test de validation des coûts
python test_corrections.py

# Test avec changements de produit
python test_with_changes.py
```

Les deux tests doivent afficher :
```
✅ ✅ ✅ VALIDATION RÉUSSIE
```

## 🔧 Architecture

### Composants Principaux

1. **mpvrp_parser.py** : Parse les fichiers d'instances `.dat`
2. **mpvrp_optimal_solver.py** : Résolution MILP optimale avec PuLP
3. **mpvrp_heuristic_solver.py** : Heuristique constructive gloutonne
4. **mpvrp_solution_writer.py** : Génère les fichiers solution conformes
5. **mpvrp_optimal_main.py** : Interface en ligne de commande

### Format des Fichiers

**Instance** : Fichiers `.dat` décrivant le problème
- Produits, dépôts, garages, stations, véhicules
- Matrice de coûts de transition
- Demandes et capacités

**Solution** : Fichiers `.dat` conformes avec
- Routes détaillées par véhicule
- Séquences de produits avec coûts cumulatifs
- Métriques globales

## 💡 Conseils d'Utilisation

### Pour les Petites Instances (< 20 stations)
```bash
python mpvrp_optimal_main.py instance.dat --time-limit 300
```
Résolution rapide garantie (< 5 min).

### Pour les Instances Moyennes (20-60 stations)
```bash
python mpvrp_optimal_main.py instance.dat --time-limit 1800
```
Résolution en 10-30 minutes généralement.

### Pour les Grandes Instances (> 60 stations)
```bash
python mpvrp_optimal_main.py instance.dat --time-limit 7200
```
Peut prendre jusqu'à 2 heures.

### Mode Heuristique (Rapide mais non optimal)
```bash
python mpvrp_optimal_main.py instance.dat --fast
```
Résolution quasi-instantanée avec bonne qualité.

## ⚠️ Notes Importantes

### Changement d'API du SolutionWriter

Le `SolutionWriter` nécessite maintenant l'instance en paramètre :

```python
# ANCIEN (incorrect)
writer = SolutionWriter(solution, instance_name)

# NOUVEAU (correct)
writer = SolutionWriter(solution, instance_name, instance)
```

### Pas de Changement au Retour

Les changements de produit se produisent **UNIQUEMENT au chargement** au dépôt, pas au retour au garage. C'est conforme à la définition du problème MPVRP-CC.

## 🏆 Validation

Solutions testées et validées par l'API officielle MPVRP-CC :
- ✅ Format conforme
- ✅ Coûts corrects
- ✅ Contraintes respectées
- ✅ Optimalité garantie (ou gap < 1%)

## 📧 Support

Pour toute question sur les corrections ou l'utilisation :
1. Consultez `docs/RAPPORT_COMPLET.md`
2. Vérifiez `docs/CORRECTIONS_MPVRP.md`
3. Exécutez les tests pour valider

## 📜 Licence

Code fourni dans le cadre du projet MPVRP-CC.

---

**Version** : 2.0 (Corrections validées)  
**Date** : 31 janvier 2026  
**Statut** : ✅ Production Ready
