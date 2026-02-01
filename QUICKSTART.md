# 🚀 Guide de Démarrage Rapide

## Installation en 3 Étapes

### 1️⃣ Extraire et Accéder
```bash
unzip mpvrp_solver_package.zip
cd mpvrp_solver_package
```

### 2️⃣ Installer les Dépendances
```bash
pip install -r requirements.txt --break-system-packages
```

### 3️⃣ Vérifier l'Installation
```bash
cd tests
python test_corrections.py
```

Vous devriez voir :
```
✅ ✅ ✅ VALIDATION RÉUSSIE - Tous les coûts sont cohérents !
```

---

## Résoudre Votre Première Instance

```bash
cd src
python mpvrp_optimal_main.py ../examples/MPVRP_TEST_s3_d1_p2.dat
```

Résultat attendu :
```
✅ Solution OPTIMALE trouvée!
💰 Coût total: 412.02
💾 Solution sauvegardée: /mnt/user-data/outputs/Sol_MPVRP_TEST_s3_d1_p2.dat
```

---

## Cas d'Usage Courants

### Résoudre une Instance Simple
```bash
python mpvrp_optimal_main.py mon_instance.dat
```

### Résoudre avec Limite de Temps
```bash
python mpvrp_optimal_main.py mon_instance.dat --time-limit 600
```

### Résoudre Toutes les Instances d'un Dossier
```bash
python mpvrp_optimal_main.py --all ./mes_instances/
```

### Mode Rapide (Heuristique)
```bash
python mpvrp_optimal_main.py mon_instance.dat --fast
```

---

## Comprendre la Sortie

Le programme affiche :
- 📊 **Informations sur l'instance** : taille, produits, véhicules
- 🔧 **Paramètres du solver** : temps, gap d'optimalité
- ✅ **Statut de résolution** : Optimal / Proche de l'optimal
- 💰 **Métriques** : coût total, distance, changements
- 💾 **Fichier de solution** : chemin vers le fichier .dat généré

---

## Structure du Fichier de Solution

Format `.dat` conforme :
```
1: 1 - 1 [1344] - 2 (1344) - 1
1: 0(0.0) - 0(0.0) - 0(0.0) - 0(0.0)

2
0
0.00
412.02
Intel Core i7-10700K
0.003
```

- Ligne 1 : Route (Garage-Dépôt-Stations-Garage)
- Ligne 2 : Produits et coûts cumulatifs
- Lignes finales : Métriques (véhicules, changements, coût, distance, CPU, temps)

---

## Aide et Documentation

### Obtenir de l'Aide
```bash
python mpvrp_optimal_main.py --help
```

### Documentation Complète
Consultez `docs/RAPPORT_COMPLET.md` pour :
- Détails des corrections
- Architecture du code
- Guide d'utilisation avancé
- Résolution de problèmes

---

## Prochaines Étapes

1. ✅ Installation terminée → Testez avec vos propres instances
2. 📖 Lisez `docs/RAPPORT_COMPLET.md` pour comprendre les corrections
3. 🧪 Exécutez `tests/test_with_changes.py` pour voir un exemple complet
4. 🚀 Résolvez vos instances MPVRP-CC !

---

**Besoin d'aide ?** Consultez README.md ou la documentation dans `docs/`
