#!/usr/bin/env python3
"""
MPVRP-CC Intelligent Solver
Choisit automatiquement entre solver optimal et heuristique selon la taille de l'instance

Pour garantir l'optimalité :
- Small instances (< 20 stations) : MILP optimal, limite 10 min
- Medium instances (20-60 stations) : MILP optimal, limite 30 min
- Large instances (> 60 stations) : MILP optimal, limite 2 heures
                                     ou Heuristique rapide si option --fast
"""

import sys
import os
import argparse
import time
from pathlib import Path

from mpvrp_parser import MPVRPInstance
from mpvrp_optimal_solver import MPVRPOptimalMILPSolver
from mpvrp_heuristic_solver import MPVRPHeuristicSolver
from mpvrp_solution_writer import SolutionWriter


def classify_instance_size(instance: MPVRPInstance) -> str:
    """
    Classifie la taille de l'instance
    
    Returns:
        'small', 'medium', ou 'large'
    """
    n_stations = instance.nb_stations
    n_products = instance.nb_products
    
    # Critère basé sur le nombre de stations et produits
    complexity = n_stations * n_products
    
    if n_stations <= 20:
        return 'small'
    elif n_stations <= 60:
        return 'medium'
    else:
        return 'large'


def get_optimal_time_limit(size: str, custom_limit: int = None) -> int:
    """
    Retourne la limite de temps recommandée selon la taille
    
    Args:
        size: 'small', 'medium', ou 'large'
        custom_limit: Limite personnalisée (optionnel)
    
    Returns:
        Limite de temps en secondes
    """
    if custom_limit:
        return custom_limit
    
    limits = {
        'small': 600,      # 10 minutes
        'medium': 1800,    # 30 minutes
        'large': 7200      # 2 heures
    }
    
    return limits.get(size, 3600)


def solve_instance_optimal(instance_file: str, 
                          output_dir: str = None,
                          time_limit: int = None,
                          use_heuristic: bool = False,
                          gap: float = 0.01) -> str:
    """
    Résout une instance avec le meilleur solver disponible
    
    Args:
        instance_file: Chemin vers l'instance
        output_dir: Répertoire de sortie
        time_limit: Limite de temps personnalisée (secondes)
        use_heuristic: Forcer l'utilisation de l'heuristique
        gap: Gap d'optimalité accepté (défaut: 1%)
    
    Returns:
        Chemin vers la solution générée
    """
    print(f"\n{'='*80}")
    print(f"RÉSOLUTION OPTIMALE DE: {os.path.basename(instance_file)}")
    print(f"{'='*80}")
    
    # Parser l'instance
    instance = MPVRPInstance(instance_file)
    instance.display_info()
    
    # Classifier la taille
    size = classify_instance_size(instance)
    print(f"\n📏 Taille de l'instance: {size.upper()}")
    
    # Déterminer la limite de temps
    if time_limit is None:
        time_limit = get_optimal_time_limit(size)
    
    print(f"⏱️  Limite de temps: {time_limit}s ({time_limit/60:.1f} min)")
    
    # Choisir le solver
    if use_heuristic:
        print(f"🔧 Utilisation: HEURISTIQUE (mode rapide)")
        solver = MPVRPHeuristicSolver(instance)
        solution = solver.solve()
        is_optimal = False
    else:
        print(f"🔧 Utilisation: SOLVER MILP OPTIMAL (gap: {gap*100}%)")
        try:
            solver = MPVRPOptimalMILPSolver(instance, time_limit=time_limit, gap=gap)
            solution = solver.solve()
            is_optimal = True
            
            if solution is None:
                print(f"\n⚠️ Solver optimal n'a pas trouvé de solution")
                print(f"🔄 Basculement vers l'heuristique...")
                solver = MPVRPHeuristicSolver(instance)
                solution = solver.solve()
                is_optimal = False
                
        except Exception as e:
            print(f"\n❌ Erreur du solver optimal: {e}")
            print(f"🔄 Basculement vers l'heuristique...")
            solver = MPVRPHeuristicSolver(instance)
            solution = solver.solve()
            is_optimal = False
    
    # Générer le fichier solution
    instance_name = os.path.basename(instance_file)
    writer = SolutionWriter(solution, instance_name, instance)
    writer.display_solution_summary()
    
    # Indiquer si c'est optimal
    if is_optimal:
        print(f"\n✅ Cette solution est OPTIMALE ou proche de l'optimal (gap < {gap*100}%)")
    else:
        print(f"\n⚠️ Cette solution est HEURISTIQUE (bonne mais pas garantie optimale)")
    
    # Sauvegarder
    if output_dir is None:
        output_dir = "/mnt/user-data/outputs"
    
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, f"Sol_{instance_name}")
    
    solution_file = writer.write_solution(output_file)
    
    return solution_file


def solve_all_instances_optimal(input_dir: str, 
                                output_dir: str = None,
                                time_limit: int = None,
                                use_heuristic: bool = False,
                                gap: float = 0.01):
    """
    Résout toutes les instances d'un répertoire
    """
    if output_dir is None:
        output_dir = "/mnt/user-data/outputs"
    
    # Trouver toutes les instances
    input_path = Path(input_dir)
    instance_files = sorted(list(input_path.glob("MPVRP_*.dat")))
    
    if not instance_files:
        print(f"❌ Aucune instance trouvée dans {input_dir}")
        return
    
    print(f"\n{'='*80}")
    print(f"RÉSOLUTION OPTIMALE DE {len(instance_files)} INSTANCES")
    print(f"{'='*80}")
    
    results = []
    total_start = time.time()
    
    for i, instance_file in enumerate(instance_files, 1):
        print(f"\n{'#'*80}")
        print(f"[{i}/{len(instance_files)}] Instance: {instance_file.name}")
        print(f"{'#'*80}")
        
        try:
            solution_file = solve_instance_optimal(
                str(instance_file),
                output_dir,
                time_limit,
                use_heuristic,
                gap
            )
            results.append({
                'instance': instance_file.name,
                'solution': solution_file,
                'status': 'OK'
            })
        except Exception as e:
            print(f"\n❌ Erreur: {e}")
            import traceback
            traceback.print_exc()
            results.append({
                'instance': instance_file.name,
                'solution': None,
                'status': f'ERREUR: {e}'
            })
    
    total_time = time.time() - total_start
    
    # Résumé final
    print(f"\n{'='*80}")
    print(f"RÉSUMÉ FINAL")
    print(f"{'='*80}")
    print(f"Temps total: {total_time:.2f}s ({total_time/60:.1f} min)")
    print(f"Instances résolues: {sum(1 for r in results if r['status'] == 'OK')}/{len(results)}")
    print(f"\nDétails:")
    for result in results:
        icon = "✅" if result['status'] == 'OK' else "❌"
        print(f"  {icon} {result['instance']}: {result['status']}")
    
    print(f"\n📁 Solutions dans: {output_dir}")


def main():
    """Point d'entrée principal"""
    parser = argparse.ArgumentParser(
        description="Résout les instances MPVRP-CC de manière optimale",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:
  # Résolution optimale d'une instance
  python %(prog)s instance.dat
  
  # Résolution de toutes les instances
  python %(prog)s --all ./instances/
  
  # Mode heuristique rapide
  python %(prog)s --all ./instances/ --fast
  
  # Limite de temps personnalisée
  python %(prog)s instance.dat --time-limit 3600
  
  # Gap d'optimalité plus strict
  python %(prog)s instance.dat --gap 0.001
        """
    )
    
    parser.add_argument(
        'input',
        help="Fichier d'instance ou répertoire"
    )
    parser.add_argument(
        '--output', '-o',
        help="Répertoire de sortie (défaut: /mnt/user-data/outputs)",
        default="/mnt/user-data/outputs"
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help="Résoudre toutes les instances du répertoire"
    )
    parser.add_argument(
        '--fast',
        action='store_true',
        help="Mode rapide: utiliser l'heuristique au lieu du solver optimal"
    )
    parser.add_argument(
        '--time-limit', '-t',
        type=int,
        help="Limite de temps en secondes (défaut: auto selon taille)"
    )
    parser.add_argument(
        '--gap', '-g',
        type=float,
        default=0.01,
        help="Gap d'optimalité accepté (défaut: 0.01 = 1%%)"
    )
    
    args = parser.parse_args()
    
    # Vérifier l'entrée
    if not os.path.exists(args.input):
        print(f"❌ Fichier/répertoire non trouvé: {args.input}")
        sys.exit(1)
    
    # Résoudre
    if args.all or os.path.isdir(args.input):
        solve_all_instances_optimal(
            args.input,
            args.output,
            args.time_limit,
            args.fast,
            args.gap
        )
    else:
        solve_instance_optimal(
            args.input,
            args.output,
            args.time_limit,
            args.fast,
            args.gap
        )
    
    print(f"\n✨ Terminé!")


if __name__ == "__main__":
    if len(sys.argv) == 1:
        print("="*80)
        print("MPVRP-CC SOLVER OPTIMAL")
        print("="*80)
        print("\nUsage:")
        print("  # Résolution optimale d'une instance")
        print("  python mpvrp_optimal_main.py instance.dat")
        print()
        print("  # Résolution de toutes les instances")
        print("  python mpvrp_optimal_main.py --all ./instances/")
        print()
        print("  # Mode heuristique rapide")
        print("  python mpvrp_optimal_main.py --all ./instances/ --fast")
        print()
        print("  # Avec limite de temps personnalisée (1 heure)")
        print("  python mpvrp_optimal_main.py instance.dat --time-limit 3600")
        print()
        print("Options:")
        print("  --all          Résoudre toutes les instances")
        print("  --fast         Utiliser l'heuristique rapide")
        print("  --time-limit   Limite de temps en secondes")
        print("  --gap          Gap d'optimalité (0.01 = 1%)")
        print("  --output       Répertoire de sortie")
        print()
        print("Limites de temps par défaut:")
        print("  Small  (< 20 stations)  : 10 minutes")
        print("  Medium (20-60 stations) : 30 minutes")
        print("  Large  (> 60 stations)  : 2 heures")
        print("="*80)
        sys.exit(0)
    
    main()
