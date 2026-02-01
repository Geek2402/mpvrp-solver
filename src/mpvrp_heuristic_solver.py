"""
MPVRP-CC Heuristic Solver
Heuristique constructive glouton pour résoudre le problème MPVRP-CC
"""

import math
import time
from typing import List, Dict, Tuple, Set
from mpvrp_parser import MPVRPInstance, Vehicle, Station
import copy


class Route:
    """Représente une route d'un véhicule"""
    
    def __init__(self, vehicle: Vehicle, home_garage_pos: Tuple[float, float]):
        self.vehicle = vehicle
        self.home_garage = vehicle.home_garage
        self.home_garage_pos = home_garage_pos
        self.current_product = vehicle.initial_product
        self.current_position = home_garage_pos
        self.remaining_capacity = vehicle.capacity
        
        # Liste des étapes: (type, id, x, y, product, quantity)
        # type: 'G' (garage), 'D' (depot), 'S' (station)
        self.steps = [('G', self.home_garage, home_garage_pos[0], home_garage_pos[1], 0, 0)]
        
        self.total_distance = 0
        self.total_changeover_cost = 0
        self.num_product_changes = 0
    
    def add_loading(self, depot_id: int, depot_pos: Tuple[float, float], 
                   product: int, quantity: float, transition_cost: float):
        """Ajoute un chargement au dépôt"""
        # Calculer distance
        dist = self._euclidean_distance(self.current_position, depot_pos)
        self.total_distance += dist
        
        # Chargement
        self.steps.append(('D', depot_id, depot_pos[0], depot_pos[1], product, quantity))
        self.current_position = depot_pos
        self.remaining_capacity = quantity
        
        # Changement de produit si nécessaire
        if self.current_product != product:
            self.total_changeover_cost += transition_cost
            self.num_product_changes += 1
            self.current_product = product
    
    def add_delivery(self, station_id: int, station_pos: Tuple[float, float], 
                    product: int, quantity: float):
        """Ajoute une livraison à une station"""
        # Calculer distance
        dist = self._euclidean_distance(self.current_position, station_pos)
        self.total_distance += dist
        
        # Livraison
        self.steps.append(('S', station_id, station_pos[0], station_pos[1], product, quantity))
        self.current_position = station_pos
        self.remaining_capacity -= quantity
    
    def return_to_garage(self, return_transition_cost: float = 0):
        """
        Retourne au garage
        IMPORTANT: Pas de changement de produit au retour - le véhicule garde son produit actuel
        """
        dist = self._euclidean_distance(self.current_position, self.home_garage_pos)
        self.total_distance += dist
        
        # Le véhicule retourne au garage avec son produit actuel
        # PAS de "retour à produit 0" - le produit actuel reste inchangé
        self.steps.append(('G', self.home_garage, self.home_garage_pos[0], 
                          self.home_garage_pos[1], self.current_product, 0))
        self.current_position = self.home_garage_pos
        
        # CORRECTION CRITIQUE: Pas de changement de produit au retour au garage !
        # Les changements se produisent uniquement lors du CHARGEMENT au dépôt
    
    def _euclidean_distance(self, pos1: Tuple[float, float], 
                          pos2: Tuple[float, float]) -> float:
        """Calcule la distance euclidienne"""
        return math.sqrt((pos2[0] - pos1[0])**2 + (pos2[1] - pos1[1])**2)
    
    def get_total_cost(self, distance_weight=1.0) -> float:
        """Calcule le coût total de la route"""
        return self.total_distance * distance_weight + self.total_changeover_cost


class MPVRPHeuristicSolver:
    """
    Solver heuristique pour MPVRP-CC
    Stratégie: Construction gloutonne avec regroupement par produit
    """
    
    def __init__(self, instance: MPVRPInstance):
        self.instance = instance
        self.routes: List[Route] = []
        self.remaining_demands = {}  # {(station_id, product): quantity}
        self.solve_time = 0
        
        # Initialiser les demandes restantes
        for s in instance.stations:
            for p in range(1, instance.nb_products + 1):
                if s.demands[p-1] > 0:
                    self.remaining_demands[(s.id, p)] = s.demands[p-1]
    
    def solve(self) -> Dict:
        """
        Résout l'instance avec l'heuristique constructive
        """
        print(f"\n🔧 Résolution heuristique du MPVRP-CC...")
        start_time = time.time()
        
        inst = self.instance
        
        # Trier les véhicules par capacité (décroissant)
        vehicles_sorted = sorted(inst.vehicles, key=lambda v: v.capacity, reverse=True)
        
        # Grouper les demandes par produit
        demands_by_product = self._group_demands_by_product()
        
        # Pour chaque produit, essayer de regrouper les livraisons
        vehicle_idx = 0
        
        for product in range(1, inst.nb_products + 1):
            if product not in demands_by_product or not demands_by_product[product]:
                continue
            
            print(f"  📦 Traitement du produit {product}...")
            
            # Trier les stations par distance au dépôt le plus proche
            stations_demands = demands_by_product[product]
            stations_demands = self._sort_stations_by_proximity(stations_demands)
            
            # Créer des routes pour ce produit
            while stations_demands and vehicle_idx < len(vehicles_sorted):
                vehicle = vehicles_sorted[vehicle_idx]
                route = self._create_route_for_product(vehicle, product, stations_demands)
                
                if route and len(route.steps) > 2:  # Plus que garage départ et arrivée
                    self.routes.append(route)
                    print(f"    ✓ Route créée pour véhicule {vehicle.id} "
                          f"({len([s for s in route.steps if s[0] == 'S'])} livraisons)")
                
                vehicle_idx += 1
        
        # S'il reste des demandes non satisfaites, les traiter
        if self.remaining_demands:
            print(f"  ⚠️ Demandes restantes: {len(self.remaining_demands)} à traiter...")
            self._handle_remaining_demands(vehicles_sorted)
        
        self.solve_time = time.time() - start_time
        
        # Générer la solution
        solution = self._build_solution()
        
        print(f"\n✅ Solution générée en {self.solve_time:.2f}s")
        print(f"  - Véhicules utilisés: {solution['num_vehicles_used']}")
        print(f"  - Changements de produit: {solution['num_product_changes']}")
        print(f"  - Distance totale: {solution['total_distance']:.2f}")
        print(f"  - Coût changement: {solution['total_changeover_cost']:.2f}")
        print(f"  - Coût total: {solution['total_cost']:.2f}")
        
        return solution
    
    def _group_demands_by_product(self) -> Dict[int, List[Tuple[int, float]]]:
        """Groupe les demandes par produit"""
        demands_by_product = {}
        
        for (station_id, product), quantity in self.remaining_demands.items():
            if product not in demands_by_product:
                demands_by_product[product] = []
            demands_by_product[product].append((station_id, quantity))
        
        return demands_by_product
    
    def _sort_stations_by_proximity(self, 
                                    stations_demands: List[Tuple[int, float]]) -> List[Tuple[int, float]]:
        """Trie les stations par proximité au premier dépôt"""
        depot = self.instance.depots[0]
        
        def distance_to_depot(station_id):
            station = self.instance.stations[station_id - 1]
            return math.sqrt((station.x - depot.x)**2 + (station.y - depot.y)**2)
        
        return sorted(stations_demands, key=lambda x: distance_to_depot(x[0]))
    
    def _create_route_for_product(self, vehicle: Vehicle, product: int,
                                  stations_demands: List[Tuple[int, float]]) -> Route:
        """Crée une route pour un véhicule livrant un produit"""
        inst = self.instance
        
        # Obtenir le garage du véhicule
        garage = inst.garages[vehicle.home_garage - 1]
        garage_pos = (garage.x, garage.y)
        
        # Créer la route
        route = Route(vehicle, garage_pos)
        
        # Choisir le dépôt le plus proche du garage
        depot = self._find_nearest_depot(garage_pos)
        depot_pos = (depot.x, depot.y)
        
        # Calculer le coût de changement si nécessaire
        transition_cost = 0
        if vehicle.initial_product != product:
            transition_cost = inst.transition_costs[vehicle.initial_product - 1][product - 1]
        
        # Capacité à charger
        load_capacity = vehicle.capacity
        current_load = 0
        deliveries_made = []
        
        # Sélectionner les stations à livrer
        for station_id, demand in stations_demands[:]:
            if (station_id, product) not in self.remaining_demands:
                continue
            
            remaining_demand = self.remaining_demands[(station_id, product)]
            deliverable = min(remaining_demand, load_capacity - current_load)
            
            if deliverable > 0.01:  # Si on peut livrer quelque chose
                current_load += deliverable
                deliveries_made.append((station_id, deliverable))
                
                # Mettre à jour la demande restante
                self.remaining_demands[(station_id, product)] -= deliverable
                if self.remaining_demands[(station_id, product)] < 0.01:
                    del self.remaining_demands[(station_id, product)]
                    stations_demands.remove((station_id, demand))
                
                if current_load >= load_capacity - 0.01:
                    break
        
        if not deliveries_made:
            return None
        
        # Construire la route optimisée (nearest neighbor)
        route.add_loading(depot.id, depot_pos, product, current_load, transition_cost)
        
        # Livrer dans l'ordre du plus proche voisin
        current_pos = depot_pos
        remaining_deliveries = deliveries_made[:]
        
        while remaining_deliveries:
            # Trouver la station la plus proche
            nearest_idx = 0
            nearest_dist = float('inf')
            
            for idx, (station_id, _) in enumerate(remaining_deliveries):
                station = inst.stations[station_id - 1]
                station_pos = (station.x, station.y)
                dist = math.sqrt((station_pos[0] - current_pos[0])**2 + 
                               (station_pos[1] - current_pos[1])**2)
                
                if dist < nearest_dist:
                    nearest_dist = dist
                    nearest_idx = idx
            
            # Livrer à cette station
            station_id, quantity = remaining_deliveries.pop(nearest_idx)
            station = inst.stations[station_id - 1]
            station_pos = (station.x, station.y)
            
            route.add_delivery(station_id, station_pos, product, quantity)
            current_pos = station_pos
        
        # Retourner au garage
        route.return_to_garage()
        
        return route
    
    def _find_nearest_depot(self, position: Tuple[float, float]):
        """Trouve le dépôt le plus proche d'une position"""
        min_dist = float('inf')
        nearest_depot = self.instance.depots[0]
        
        for depot in self.instance.depots:
            dist = math.sqrt((depot.x - position[0])**2 + (depot.y - position[1])**2)
            if dist < min_dist:
                min_dist = dist
                nearest_depot = depot
        
        return nearest_depot
    
    def _handle_remaining_demands(self, vehicles: List[Vehicle]):
        """Traite les demandes restantes non satisfaites"""
        # Grouper par produit
        demands_by_product = {}
        for (station_id, product), quantity in self.remaining_demands.items():
            if product not in demands_by_product:
                demands_by_product[product] = []
            demands_by_product[product].append((station_id, quantity))
        
        # Pour chaque produit, créer des routes supplémentaires
        for product, stations_demands in demands_by_product.items():
            # Utiliser les véhicules restants
            for vehicle in vehicles:
                if not stations_demands:
                    break
                
                route = self._create_route_for_product(vehicle, product, stations_demands)
                if route and len(route.steps) > 2:
                    self.routes.append(route)
    
    def _build_solution(self) -> Dict:
        """Construit le dictionnaire de solution"""
        solution = {
            'routes': self.routes,
            'num_vehicles_used': len(self.routes),
            'num_product_changes': sum(r.num_product_changes for r in self.routes),
            'total_distance': sum(r.total_distance for r in self.routes),
            'total_changeover_cost': sum(r.total_changeover_cost for r in self.routes),
            'total_cost': sum(r.get_total_cost() for r in self.routes),
            'solve_time': self.solve_time
        }
        
        return solution


def test_heuristic():
    """Test de l'heuristique sur l'instance small"""
    print("\n" + "="*70)
    print("TEST DE L'HEURISTIQUE CONSTRUCTIVE")
    print("="*70)
    
    instance = MPVRPInstance("/mnt/user-data/uploads/MPVRP_S_018_s7_d1_p2.dat")
    instance.display_info()
    
    solver = MPVRPHeuristicSolver(instance)
    solution = solver.solve()
    
    print(f"\n📋 Détails des routes:")
    for i, route in enumerate(solution['routes'], 1):
        print(f"\nRoute {i} - Véhicule {route.vehicle.id}:")
        print(f"  Produit initial: {route.vehicle.initial_product}")
        print(f"  Nombre d'étapes: {len(route.steps)}")
        print(f"  Distance: {route.total_distance:.2f}")
        print(f"  Coût changement: {route.total_changeover_cost:.2f}")
        
        deliveries = [s for s in route.steps if s[0] == 'S']
        print(f"  Livraisons ({len(deliveries)}):")
        for step_type, sid, x, y, prod, qty in deliveries:
            print(f"    - Station {sid}: {qty:.1f} unités de produit {prod}")


if __name__ == "__main__":
    test_heuristic()
