#!/usr/bin/env python3
"""
Test d'une instance avec changements de produit obligatoires
"""

import sys
import os

# Ajouter le répertoire src au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from mpvrp_parser import MPVRPInstance
from mpvrp_heuristic_solver import MPVRPHeuristicSolver
from mpvrp_solution_writer import SolutionWriter


def main():
    print("\n" + "="*80)
    print("TEST AVEC CHANGEMENTS DE PRODUIT")
    print("="*80)
    
    instance_file = os.path.join(os.path.dirname(__file__), '..', 'examples', 'MPVRP_CHANGES_s4_d1_p2.dat')
    
    if not os.path.exists(instance_file):
        print(f"\n❌ Instance de test non trouvée: {instance_file}")
        print(f"   Créez l'instance ou modifiez le chemin dans le test.")
        return
    
    instance = MPVRPInstance(instance_file)
    
    print(f"\n📊 Instance:")
    print(f"  Produits: {instance.nb_products}")
    print(f"  Stations: {instance.nb_stations}")
    print(f"  Véhicules: {instance.nb_vehicles}")
    
    print(f"\n💰 Matrice de transition:")
    print(f"  P1→P1: {instance.transition_costs[0][0]:.1f}")
    print(f"  P1→P2: {instance.transition_costs[0][1]:.1f}  ⚠️ Coût de changement")
    print(f"  P2→P1: {instance.transition_costs[1][0]:.1f}  ⚠️ Coût de changement")
    print(f"  P2→P2: {instance.transition_costs[1][1]:.1f}")
    
    print(f"\n📋 Demandes par station:")
    for i, s in enumerate(instance.stations, 1):
        print(f"  Station {s.id}:")
        print(f"    - Produit 1: {s.demands[0]:.0f}")
        print(f"    - Produit 2: {s.demands[1]:.0f}")
    
    # Résoudre
    print(f"\n🔧 Résolution...")
    solver = MPVRPHeuristicSolver(instance)
    solution = solver.solve()
    
    # Analyser les changements
    print(f"\n📊 ANALYSE DES CHANGEMENTS DE PRODUIT")
    print("="*80)
    
    for route in solution['routes']:
        print(f"\n🚛 Véhicule {route.vehicle.id}:")
        print(f"  Produit initial: {route.vehicle.initial_product}")
        
        products_sequence = []
        for step_type, site_id, x, y, product, qty in route.steps:
            if step_type == 'D':  # Chargement
                products_sequence.append(product)
        
        print(f"  Séquence de produits chargés: {products_sequence}")
        print(f"  Nombre de chargements: {len(products_sequence)}")
        
        # Calculer les changements attendus
        expected_changes = 0
        expected_cost = 0.0
        prev_prod = route.vehicle.initial_product
        
        for prod in products_sequence:
            if prod != prev_prod:
                cost = instance.transition_costs[prev_prod-1][prod-1]
                expected_changes += 1
                expected_cost += cost
                print(f"  ➡️ Changement {prev_prod} → {prod}, coût: {cost:.1f}")
                prev_prod = prod
        
        print(f"\n  Changements attendus: {expected_changes}")
        print(f"  Coût attendu: {expected_cost:.2f}")
        print(f"  Changements comptés: {route.num_product_changes}")
        print(f"  Coût compté: {route.total_changeover_cost:.2f}")
        
        if expected_changes == route.num_product_changes and abs(expected_cost - route.total_changeover_cost) < 0.01:
            print(f"  ✅ CORRECT")
        else:
            print(f"  ❌ ERREUR !")
    
    # Générer la solution
    print(f"\n📝 Génération du fichier de solution...")
    writer = SolutionWriter(solution, "MPVRP_CHANGES_s4_d1_p2.dat", instance)
    output_file = writer.write_solution(os.path.join(os.path.dirname(__file__), "solution_with_changes.dat"))
    
    print(f"\n📄 Fichier de solution généré:")
    print("="*80)
    with open(output_file, 'r') as f:
        print(f.read())


if __name__ == "__main__":
    main()
