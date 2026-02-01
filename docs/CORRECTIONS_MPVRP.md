# 🔧 Corrections MPVRP-CC - Problèmes de coûts

## 📋 Résumé des problèmes identifiés

### 1. **Calcul incorrect des coûts cumulatifs dans le fichier de solution**
**Fichier**: `mpvrp_solution_writer.py` - Fonction `_build_product_line()`

**Problème**:
- Le coût cumulatif était mal calculé
- Le coût total était appliqué en bloc au lieu d'augmenter progressivement
- Pas d'accès à la matrice de transition costs pour calculer les coûts réels

**Solution**:
- Ajout du paramètre `instance` au constructeur de `SolutionWriter`
- Recalcul progressif du coût cumulatif à chaque changement de produit
- Utilisation de la matrice `instance.transition_costs` pour les coûts réels

### 2. **Faux changement de produit au retour au garage**
**Fichiers**: `mpvrp_heuristic_solver.py` et `mpvrp_optimal_solver.py`

**Problème**:
- La méthode `Route.return_to_garage()` comptait un changement de produit au retour
- Un coût de retour au "produit 0" était ajouté incorrectement
- Le véhicule était marqué comme transportant "produit 0" au garage de retour

**Solution**:
- Suppression du comptage de changement au retour dans `return_to_garage()`
- Le véhicule garde son produit actuel au retour (pas de "produit 0")
- Suppression du calcul de `return_cost` dans `_build_routes_from_deliveries()`

### 3. **Incohérence dans l'affichage des produits**
**Fichier**: `mpvrp_solution_writer.py`

**Problème**:
- Le produit au garage de retour était affiché comme "0" au lieu du produit actuel
- Confusion entre indexation 0 et 1

**Solution**:
- Le produit au garage de retour affiche maintenant le dernier produit transporté
- Conversion correcte 1-indexé → 0-indexé pour l'affichage

## 📝 Fichiers modifiés

### 1. **mpvrp_solution_writer.py**
```python
# Ligne 81-85: Ajout du paramètre instance
def __init__(self, solution: Dict, instance_name: str, instance=None):
    self.solution = solution
    self.instance_name = instance_name
    self.instance = instance  # AJOUT: instance pour accéder aux coûts
    self.output_filename = f"Sol_{instance_name}"

# Lignes 153-201: Réécriture complète de _build_product_line()
# - Calcul progressif du coût cumulatif
# - Utilisation de instance.transition_costs
# - Affichage correct du produit au retour
```

### 2. **mpvrp_heuristic_solver.py**
```python
# Lignes 62-75: Correction de return_to_garage()
def return_to_garage(self, return_transition_cost: float = 0):
    """
    Retourne au garage
    IMPORTANT: Pas de changement de produit au retour
    """
    # Le véhicule retourne avec son produit actuel
    self.steps.append(('G', self.home_garage, ..., self.current_product, 0))
    # PLUS de num_product_changes += 1 ici !
    # PLUS de total_changeover_cost += return_transition_cost !
```

### 3. **mpvrp_optimal_solver.py**
```python
# Lignes 565-568: Suppression du calcul de return_cost
# Retour au garage sans coût de changement
route.return_to_garage(0)  # Pas de coût de retour
routes.append(route)
```

### 4. **mpvrp_optimal_main.py**
```python
# Ligne 134: Passage de l'instance au SolutionWriter
writer = SolutionWriter(solution, instance_name, instance)
```

## ✅ Corrections appliquées

1. ✅ Le `SolutionWriter` reçoit maintenant l'instance en paramètre
2. ✅ Les coûts cumulatifs sont calculés progressivement et correctement
3. ✅ Pas de faux changement de produit au retour au garage
4. ✅ Le produit au garage de retour est affiché correctement
5. ✅ Cohérence entre le calcul des coûts et leur affichage

## 🎯 Résultats attendus

Après ces corrections:
- Les coûts affichés dans le fichier `.dat` correspondent aux coûts réellement calculés
- Le nombre de changements de produit est correct
- Le coût total de changement correspond à la somme des coûts de transition réels
- Les métriques finales (lignes 1-6 du fichier) sont cohérentes avec le contenu des routes

## ⚠️ Limitations connues du modèle MILP

Le modèle MILP simplifié utilise `min(cost_p1_p2, cost_p2_p1)` pour les changements:
- Ceci est une approximation car la matrice n'est pas symétrique
- Pour un modèle vraiment optimal, il faudrait capturer l'ordre exact des produits
- Cette simplification permet une résolution plus rapide au prix d'une petite approximation

## 🧪 Test

Pour tester les corrections:
```bash
cd /home/claude
python mpvrp_optimal_main.py /mnt/user-data/uploads/MPVRP_S_018_s7_d1_p2.dat --time-limit 300
```

Le fichier de solution généré devrait maintenant avoir:
- Des coûts cumulatifs qui augmentent progressivement
- Un nombre de changements cohérent
- Un coût total qui correspond aux métriques finales
