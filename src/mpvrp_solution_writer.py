"""
MPVRP-CC Solution Writer
Génère les fichiers de solution au format .dat attendu
"""

import platform
from typing import List, Dict
from mpvrp_heuristic_solver import Route


# Cache pour le CPU - SIMPLIFIÉ
_CPU_NAME_CACHE = None


def get_cpu_name():
    """
    Obtient le nom du processeur de manière ultra-simple et sûre
    Version ultra-robuste qui ne plante JAMAIS
    Compatible Windows ET Linux (WSL)
    """
    global _CPU_NAME_CACHE
    
    # Retourner le cache si disponible
    if _CPU_NAME_CACHE is not None:
        return _CPU_NAME_CACHE
    
    cpu_name = "Unknown Processor"  # Valeur par défaut absolue
    
    # Méthode 1 : Windows Registry (Windows uniquement)
    try:
        if platform.system() == "Windows":
            import winreg
            with winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"HARDWARE\DESCRIPTION\System\CentralProcessor\0",
                0,
                winreg.KEY_READ
            ) as key:
                cpu_name = winreg.QueryValueEx(key, "ProcessorNameString")[0].strip()
    except Exception:
        pass
    
    # Méthode 2 : /proc/cpuinfo (Linux/WSL)
    if cpu_name == "Unknown Processor":
        try:
            if platform.system() == "Linux":
                with open('/proc/cpuinfo', 'r') as f:
                    for line in f:
                        if 'model name' in line.lower():
                            cpu_name = line.split(':')[1].strip()
                            break
        except Exception:
            pass
    
    # Méthode 3 : platform.processor() (fallback)
    if cpu_name == "Unknown Processor":
        try:
            proc = platform.processor()
            if proc and len(proc) > 3:
                cpu_name = proc
        except Exception:
            pass
    
    # Nettoyer le résultat (AVEC protection contre tout)
    try:
        if cpu_name and isinstance(cpu_name, str) and len(cpu_name) > 3:
            cpu_name = ' '.join(str(cpu_name).split())
        else:
            cpu_name = "Unknown Processor"
    except Exception:
        cpu_name = "Unknown Processor"
    
    # Mettre en cache
    _CPU_NAME_CACHE = cpu_name
    return cpu_name


class SolutionWriter:
    """
    Écrit une solution MPVRP-CC au format .dat standard
    """
    
    def __init__(self, solution: Dict, instance_name: str, instance=None):
        self.solution = solution
        self.instance_name = instance_name
        self.instance = instance  # AJOUT: instance pour accéder aux coûts de transition
        self.output_filename = f"Sol_{instance_name}"
    
    def write_solution(self, output_path: str = None) -> str:
        """
        Écrit la solution dans un fichier .dat
        Retourne le chemin du fichier créé
        """
        if output_path is None:
            output_path = f"/home/claude/{self.output_filename}"
        
        with open(output_path, 'w') as f:
            # Écrire chaque route
            routes: List[Route] = self.solution['routes']
            
            for route in routes:
                # Ligne 1: Séquence de visites
                visit_line = self._build_visit_line(route)
                f.write(visit_line + '\n')
                
                # Ligne 2: Séquence de produits et coûts
                product_line = self._build_product_line(route)
                f.write(product_line + '\n')
                
                # Ligne vide de séparation
                f.write('\n')
            
            # Métriques finales (6 lignes)
            f.write(f"{self.solution['num_vehicles_used']}\n")
            f.write(f"{self.solution['num_product_changes']}\n")
            f.write(f"{self.solution['total_changeover_cost']:.2f}\n")
            f.write(f"{self.solution['total_distance']:.2f}\n")
            
            # CPU name avec protection maximale
            try:
                cpu = get_cpu_name()
            except Exception:
                cpu = "Unknown Processor"
            f.write(f"{cpu}\n")
            
            f.write(f"{self.solution['solve_time']:.3f}\n")
        
        print(f"\n💾 Solution sauvegardée: {output_path}")
        return output_path
    
    def _build_visit_line(self, route: Route) -> str:
        """
        Construit la ligne de visite pour une route
        Format: ID: Garage - Depot [Load] - Station (Deliver) - ... - Garage
        """
        vehicle_id = route.vehicle.id
        parts = []
        
        current_load = 0
        for step in route.steps:
            step_type, site_id, x, y, product, quantity = step
            
            if step_type == 'G':  # Garage
                parts.append(str(site_id))
            elif step_type == 'D':  # Depot - chargement
                current_load = quantity
                parts.append(f"{site_id} [{round(quantity)}]")
            elif step_type == 'S':  # Station - livraison
                parts.append(f"{site_id} ({round(quantity)})")
        
        return f"{vehicle_id}: " + " - ".join(parts)
    
    def _build_product_line(self, route: Route) -> str:
        """
        Construit la ligne de produits pour une route
        Format: ID: Prod(Cost) - Prod(Cost) - ...
        IMPORTANT: 
        - La ligne de produits doit avoir autant d'éléments que la ligne de route
        - Les produits sont indexés à partir de 0 dans le format de sortie  
        - Le coût cumulatif augmente progressivement à chaque changement de produit
        """
        vehicle_id = route.vehicle.id
        parts = []
        
        cumulative_cost = 0.0
        previous_product = route.vehicle.initial_product  # 1-indexé, produit au step précédent
        
        # Pour chaque site dans la route
        for i, (step_type, site_id, x, y, product, quantity) in enumerate(route.steps):
            
            if step_type == 'G':  # Garage
                if i == 0:
                    # Garage de départ - afficher le produit initial du véhicule (0-indexé)
                    display_product = route.vehicle.initial_product - 1
                else:
                    # Garage de retour - afficher le dernier produit transporté (0-indexé)
                    display_product = previous_product - 1
                
                parts.append(f"{display_product}({cumulative_cost:.1f})")
                
            elif step_type == 'D':  # Dépôt - chargement, possible changement de produit
                # Vérifier s'il y a changement de produit
                if i > 0 and previous_product != product:
                    # Changement de produit détecté
                    if self.instance is not None:
                        # Utiliser la matrice de coûts de transition
                        # Coût pour aller de previous_product vers product
                        transition_cost = self.instance.transition_costs[previous_product - 1][product - 1]
                        cumulative_cost += transition_cost
                
                # Mettre à jour le produit actuel
                previous_product = product
                
                # Afficher le produit chargé (0-indexé)
                display_product = product - 1
                parts.append(f"{display_product}({cumulative_cost:.1f})")
                
            elif step_type == 'S':  # Station - livraison, même produit que le chargement
                # Pas de changement de produit, on garde le même coût cumulatif
                display_product = product - 1
                parts.append(f"{display_product}({cumulative_cost:.1f})")
        
        return f"{vehicle_id}: " + " - ".join(parts)
    
    def display_solution_summary(self):
        """Affiche un résumé de la solution"""
        print(f"\n" + "="*70)
        print(f"RÉSUMÉ DE LA SOLUTION - {self.instance_name}")
        print(f"="*70)
        
        routes: List[Route] = self.solution['routes']
        
        print(f"\n📊 Métriques globales:")
        print(f"  Véhicules utilisés: {self.solution['num_vehicles_used']}")
        print(f"  Changements de produit: {self.solution['num_product_changes']}")
        print(f"  Distance totale: {self.solution['total_distance']:.2f}")
        print(f"  Coût total changements: {self.solution['total_changeover_cost']:.2f}")
        print(f"  COÛT TOTAL: {self.solution['total_cost']:.2f}")
        print(f"  Temps de résolution: {self.solution['solve_time']:.3f}s")
        
        print(f"\n🚛 Détails par véhicule:")
        for i, route in enumerate(routes, 1):
            deliveries = [s for s in route.steps if s[0] == 'S']
            total_delivered = sum(s[5] for s in deliveries)
            
            print(f"\n  Route {i} - Véhicule {route.vehicle.id}:")
            print(f"    Capacité: {route.vehicle.capacity:.0f}")
            print(f"    Quantité totale livrée: {total_delivered:.0f}")
            print(f"    Stations visitées: {len(deliveries)}")
            print(f"    Distance parcourue: {route.total_distance:.2f}")
            print(f"    Changements de produit: {route.num_product_changes}")
            print(f"    Coût changement: {route.total_changeover_cost:.2f}")
        
        print(f"\n" + "="*70)


def test_solution_writer():
    """Test du writer de solution"""
    from mpvrp_parser import MPVRPInstance
    from mpvrp_heuristic_solver import MPVRPHeuristicSolver
    
    print("\n" + "="*70)
    print("TEST DU GÉNÉRATEUR DE SOLUTION")
    print("="*70)
    
    # Résoudre une instance
    instance = MPVRPInstance("/mnt/user-data/uploads/MPVRP_S_018_s7_d1_p2.dat")
    solver = MPVRPHeuristicSolver(instance)
    solution = solver.solve()
    
    # Écrire la solution
    writer = SolutionWriter(solution, "MPVRP_S_018_s7_d1_p2.dat", instance)
    writer.display_solution_summary()
    
    output_file = writer.write_solution("/home/claude/test_solution.dat")
    
    # Afficher le contenu
    print(f"\n📄 Contenu du fichier généré:")
    print("="*70)
    with open(output_file, 'r') as f:
        content = f.read()
        print(content)


if __name__ == "__main__":
    test_solution_writer()
