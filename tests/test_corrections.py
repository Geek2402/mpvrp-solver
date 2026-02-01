#!/usr/bin/env python3
"""
Script de test pour valider les corrections MPVRP-CC
Vérifie que les coûts calculés correspondent aux coûts affichés
"""

import sys
import os

# Ajouter le répertoire src au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from mpvrp_parser import MPVRPInstance
from mpvrp_heuristic_solver import MPVRPHeuristicSolver
from mpvrp_solution_writer import SolutionWriter


def test_solution_costs():
    """
    Test de validation des coûts
    """
    print("\n" + "="*80)
    print("TEST DE VALIDATION DES COÛTS - CORRECTIONS MPVRP-CC")
    print("="*80)
    
    # Charger l'instance
    instance_file = os.path.join(os.path.dirname(__file__), '..', 'examples', 'MPVRP_TEST_s3_d1_p2.dat')
    
    if not os.path.exists(instance_file):
        print(f"\n❌ Instance de test non trouvée: {instance_file}")
        print(f"   Créez l'instance ou modifiez le chemin dans le test.")
        return False
    
    print(f"\n📂 Chargement de l'instance: {instance_file}")
    instance = MPVRPInstance(instance_file)
    
    print(f"\n📊 Informations instance:")
    print(f"  - Produits: {instance.nb_products}")
    print(f"  - Stations: {instance.nb_stations}")
    print(f"  - Véhicules: {instance.nb_vehicles}")
    print(f"  - Dépôts: {instance.nb_depots}")
    
    print(f"\n💰 Matrice de coûts de transition:")
    for i, row in enumerate(instance.transition_costs, 1):
        print(f"  Produit {i}: {row}")
    
    # Résoudre avec l'heuristique
    print(f"\n🔧 Résolution avec heuristique...")
    solver = MPVRPHeuristicSolver(instance)
    solution = solver.solve()
    
    # Vérifier la cohérence des coûts
    print(f"\n✅ VÉRIFICATION DES COÛTS")
    print(f"="*80)
    
    total_changeover_from_routes = 0
    total_changes_from_routes = 0
    
    for i, route in enumerate(solution['routes'], 1):
        print(f"\n📍 Route {i} - Véhicule {route.vehicle.id}:")
        print(f"  Produit initial véhicule: {route.vehicle.initial_product}")
        print(f"  Changements comptés: {route.num_product_changes}")
        print(f"  Coût de changement: {route.total_changeover_cost:.2f}")
        
        # Recalculer manuellement les changements
        manual_changes = 0
        manual_cost = 0.0
        prev_product = route.vehicle.initial_product
        
        print(f"\n  Détail des étapes:")
        for j, (step_type, site_id, x, y, product, qty) in enumerate(route.steps):
            if step_type == 'G':
                step_name = f"Garage {site_id}"
                print(f"    {j}. {step_name}")
            elif step_type == 'D':
                step_name = f"Dépôt {site_id} [charge {int(qty)}]"
                # Changement de produit ?
                if j > 0 and prev_product != product:
                    cost = instance.transition_costs[prev_product-1][product-1]
                    manual_changes += 1
                    manual_cost += cost
                    print(f"    {j}. {step_name} - Produit {product} (CHANGEMENT de {prev_product}→{product}, coût: {cost:.2f})")
                    prev_product = product
                else:
                    print(f"    {j}. {step_name} - Produit {product}")
                    prev_product = product
            else:  # Station
                step_name = f"Station {site_id} (livre {int(qty)})"
                print(f"    {j}. {step_name} - Produit {product}")
        
        print(f"\n  💡 Vérification manuelle:")
        print(f"    Changements recalculés: {manual_changes}")
        print(f"    Coût recalculé: {manual_cost:.2f}")
        print(f"    Changements dans route: {route.num_product_changes}")
        print(f"    Coût dans route: {route.total_changeover_cost:.2f}")
        
        if manual_changes == route.num_product_changes and abs(manual_cost - route.total_changeover_cost) < 0.01:
            print(f"    ✅ COHÉRENT")
        else:
            print(f"    ❌ INCOHÉRENT - ERREUR DÉTECTÉE !")
        
        total_changeover_from_routes += route.total_changeover_cost
        total_changes_from_routes += route.num_product_changes
    
    # Vérification finale
    print(f"\n" + "="*80)
    print(f"📊 MÉTRIQUES GLOBALES")
    print(f"="*80)
    print(f"Changements totaux (solution): {solution['num_product_changes']}")
    print(f"Changements totaux (routes):   {total_changes_from_routes}")
    print(f"Coût changement (solution):    {solution['total_changeover_cost']:.2f}")
    print(f"Coût changement (routes):      {total_changeover_from_routes:.2f}")
    
    coherent = (
        solution['num_product_changes'] == total_changes_from_routes and
        abs(solution['total_changeover_cost'] - total_changeover_from_routes) < 0.01
    )
    
    if coherent:
        print(f"\n✅ ✅ ✅ VALIDATION RÉUSSIE - Tous les coûts sont cohérents !")
    else:
        print(f"\n❌ ❌ ❌ VALIDATION ÉCHOUÉE - Incohérence détectée !")
    
    # Générer le fichier de solution
    print(f"\n📝 Génération du fichier de solution...")
    writer = SolutionWriter(solution, "MPVRP_TEST_s3_d1_p2.dat", instance)
    output_file = writer.write_solution(os.path.join(os.path.dirname(__file__), "test_solution_validated.dat"))
    
    # Afficher le fichier
    print(f"\n📄 Contenu du fichier de solution:")
    print("="*80)
    with open(output_file, 'r') as f:
        content = f.read()
        print(content)
    
    print("\n" + "="*80)
    print("TEST TERMINÉ")
    print("="*80)
    
    return coherent


if __name__ == "__main__":
    success = test_solution_costs()
    sys.exit(0 if success else 1)
