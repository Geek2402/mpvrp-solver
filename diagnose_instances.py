#!/usr/bin/env python3
"""
Script de diagnostic pour analyser les instances MPVRP-CC
Calcule le M nécessaire théorique pour chaque instance
"""

import sys
import os
import math

# Ajouter le répertoire src au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from mpvrp_parser import MPVRPInstance


def analyze_instance(instance_file):
    """
    Analyse une instance et calcule le M nécessaire
    """
    print(f"\n{'='*80}")
    print(f"ANALYSE DE: {os.path.basename(instance_file)}")
    print(f"{'='*80}")
    
    # Charger l'instance
    instance = MPVRPInstance(instance_file)
    
    print(f"\n📊 Dimensions:")
    print(f"  Stations: {instance.nb_stations}")
    print(f"  Produits: {instance.nb_products}")
    print(f"  Véhicules: {instance.nb_vehicles}")
    print(f"  Dépôts: {instance.nb_depots}")
    
    # Analyser les capacités des véhicules
    capacities = [v.capacity for v in instance.vehicles]
    print(f"\n🚛 Capacités des véhicules:")
    print(f"  Min: {min(capacities):.0f}")
    print(f"  Max: {max(capacities):.0f}")
    print(f"  Moyenne: {sum(capacities)/len(capacities):.0f}")
    
    # Analyser les demandes par produit
    print(f"\n📦 Demandes par produit:")
    max_m_needed = 0
    
    for p in range(1, instance.nb_products + 1):
        total_demand = sum(s.demands[p-1] for s in instance.stations)
        
        # Calculer M nécessaire avec le plus petit véhicule
        min_capacity = min(capacities)
        m_with_min_vehicle = math.ceil(total_demand / min_capacity) if min_capacity > 0 else 999
        
        # Calculer M nécessaire avec capacité moyenne
        avg_capacity = sum(capacities) / len(capacities)
        m_with_avg_vehicle = math.ceil(total_demand / avg_capacity) if avg_capacity > 0 else 999
        
        max_m_needed = max(max_m_needed, m_with_min_vehicle)
        
        print(f"  Produit {p}:")
        print(f"    Demande totale: {total_demand:>12,.0f}")
        print(f"    M (véhicule min): {m_with_min_vehicle:>3} voyages")
        print(f"    M (véhicule moy): {m_with_avg_vehicle:>3} voyages")
    
    # Évaluation
    print(f"\n🎯 Évaluation:")
    print(f"  M maximum nécessaire: {max_m_needed} voyages")
    
    if max_m_needed <= 20:
        status = "✅ M=20 SUFFISANT"
        color = "Vert"
    elif max_m_needed <= 50:
        status = "⚠️  M=20 TROP PETIT (utiliser M dynamique)"
        color = "Orange"
    else:
        status = "🔴 M=20 TRÈS INSUFFISANT (utiliser M dynamique)"
        color = "Rouge"
    
    print(f"  Statut: {status}")
    print(f"  Risque d'échec avec M=20: {color}")
    
    # Recommandation
    print(f"\n💡 Recommandation:")
    if max_m_needed <= 20:
        print(f"  Cette instance devrait fonctionner avec M=20 fixe")
    else:
        recommended_m = int(max_m_needed * 1.5)  # Marge de 50%
        print(f"  Utiliser M dynamique ou M fixe ≥ {recommended_m}")
    
    return {
        'file': os.path.basename(instance_file),
        'stations': instance.nb_stations,
        'products': instance.nb_products,
        'vehicles': instance.nb_vehicles,
        'max_m_needed': max_m_needed,
        'safe_with_m20': max_m_needed <= 20
    }


def main():
    if len(sys.argv) < 2:
        print("Usage: python diagnose_instances.py <instance1.dat> [instance2.dat] ...")
        print("\nExemples:")
        print("  python diagnose_instances.py MPVRP_S_050_s6_d2_p3.dat")
        print("  python diagnose_instances.py instances/*.dat")
        return 1
    
    results = []
    
    for instance_file in sys.argv[1:]:
        if not os.path.exists(instance_file):
            print(f"❌ Fichier introuvable: {instance_file}")
            continue
        
        try:
            result = analyze_instance(instance_file)
            results.append(result)
        except Exception as e:
            print(f"❌ Erreur lors de l'analyse: {e}")
            continue
    
    # Résumé
    if len(results) > 1:
        print(f"\n{'='*80}")
        print("📊 RÉSUMÉ DES ANALYSES")
        print(f"{'='*80}\n")
        
        print(f"{'Instance':<40} {'Stations':<10} {'M Nécessaire':<15} {'M=20 OK?'}")
        print(f"{'-'*80}")
        
        safe_count = 0
        unsafe_count = 0
        
        for r in results:
            status = "✅" if r['safe_with_m20'] else "❌"
            if r['safe_with_m20']:
                safe_count += 1
            else:
                unsafe_count += 1
            
            print(f"{r['file']:<40} {r['stations']:<10} {r['max_m_needed']:<15} {status}")
        
        print(f"\n{'='*80}")
        print(f"Total: {len(results)} instances")
        print(f"  ✅ Sûres avec M=20: {safe_count} ({100*safe_count//len(results)}%)")
        print(f"  ❌ Risquées avec M=20: {unsafe_count} ({100*unsafe_count//len(results)}%)")
        print(f"{'='*80}\n")
        
        if unsafe_count > 0:
            print("⚠️  ATTENTION: Certaines instances nécessitent M > 20")
            print("   → Utilisez le calcul dynamique de M dans le solver")
        else:
            print("✅ Toutes les instances peuvent fonctionner avec M=20")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
