"""
MPVRP-CC Instance Parser
Lit et parse les fichiers d'instance du problème MPVRP-CC
"""

import math
from dataclasses import dataclass
from typing import List, Dict


@dataclass
class Vehicle:
    """Représente un véhicule"""
    id: int
    capacity: float
    home_garage: int
    initial_product: int


@dataclass
class Depot:
    """Représente un dépôt"""
    id: int
    x: float
    y: float
    stocks: List[float]  # Stock pour chaque produit


@dataclass
class Garage:
    """Représente un garage"""
    id: int
    x: float
    y: float


@dataclass
class Station:
    """Représente une station-service (client)"""
    id: int
    x: float
    y: float
    demands: List[float]  # Demande pour chaque produit


class MPVRPInstance:
    """Classe principale pour une instance MPVRP-CC"""
    
    def __init__(self, filename: str):
        self.filename = filename
        self.uuid = ""
        self.nb_products = 0
        self.nb_depots = 0
        self.nb_garages = 0
        self.nb_stations = 0
        self.nb_vehicles = 0
        
        self.transition_costs = []  # Matrice de coûts de changement
        self.vehicles: List[Vehicle] = []
        self.depots: List[Depot] = []
        self.garages: List[Garage] = []
        self.stations: List[Station] = []
        
        self._parse_file(filename)
    
    def _parse_file(self, filename: str):
        """Parse le fichier d'instance"""
        with open(filename, 'r') as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]
        
        idx = 0
        
        # Ligne 1: UUID
        self.uuid = lines[idx].replace('#', '').strip()
        idx += 1
        
        # Ligne 2: Paramètres globaux
        params = list(map(int, lines[idx].split()))
        self.nb_products = params[0]
        self.nb_depots = params[1]
        self.nb_garages = params[2]
        self.nb_stations = params[3]
        self.nb_vehicles = params[4]
        idx += 1
        
        # Matrice de coûts de transition (nb_products x nb_products)
        self.transition_costs = []
        for i in range(self.nb_products):
            row = list(map(float, lines[idx].split()))
            self.transition_costs.append(row)
            idx += 1
        
        # Véhicules
        for i in range(self.nb_vehicles):
            parts = lines[idx].split()
            vehicle = Vehicle(
                id=int(parts[0]),
                capacity=float(parts[1]),
                home_garage=int(parts[2]),
                initial_product=int(parts[3])
            )
            self.vehicles.append(vehicle)
            idx += 1
        
        # Dépôts
        for i in range(self.nb_depots):
            parts = list(map(float, lines[idx].split()))
            depot = Depot(
                id=int(parts[0]),
                x=parts[1],
                y=parts[2],
                stocks=parts[3:]  # Reste = stocks pour chaque produit
            )
            self.depots.append(depot)
            idx += 1
        
        # Garages
        for i in range(self.nb_garages):
            parts = list(map(float, lines[idx].split()))
            garage = Garage(
                id=int(parts[0]),
                x=parts[1],
                y=parts[2]
            )
            self.garages.append(garage)
            idx += 1
        
        # Stations
        for i in range(self.nb_stations):
            parts = list(map(float, lines[idx].split()))
            station = Station(
                id=int(parts[0]),
                x=parts[1],
                y=parts[2],
                demands=parts[3:]  # Reste = demandes pour chaque produit
            )
            self.stations.append(station)
            idx += 1
    
    def euclidean_distance(self, x1: float, y1: float, x2: float, y2: float) -> float:
        """Calcule la distance euclidienne entre deux points"""
        return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
    
    def get_distance_matrix(self) -> Dict:
        """
        Calcule la matrice de distances entre tous les sites
        Retourne un dictionnaire avec clés (type1, id1, type2, id2)
        Types: 'G' (garage), 'D' (depot), 'S' (station)
        """
        distances = {}
        
        # Liste de tous les sites avec leur type
        all_sites = []
        for g in self.garages:
            all_sites.append(('G', g.id, g.x, g.y))
        for d in self.depots:
            all_sites.append(('D', d.id, d.x, d.y))
        for s in self.stations:
            all_sites.append(('S', s.id, s.x, s.y))
        
        # Calculer toutes les distances
        for i, (type1, id1, x1, y1) in enumerate(all_sites):
            for type2, id2, x2, y2 in all_sites:
                key = (type1, id1, type2, id2)
                distances[key] = self.euclidean_distance(x1, y1, x2, y2)
        
        return distances
    
    def get_transition_cost(self, from_product: int, to_product: int) -> float:
        """Retourne le coût de changement de produit"""
        # Les produits sont indexés à partir de 1 dans l'instance
        # mais à partir de 0 dans la matrice
        return self.transition_costs[from_product - 1][to_product - 1]
    
    def display_info(self):
        """Affiche les informations de l'instance"""
        print(f"\n{'='*60}")
        print(f"Instance MPVRP-CC: {self.filename}")
        print(f"{'='*60}")
        print(f"UUID: {self.uuid}")
        print(f"\nDimensions:")
        print(f"  - Produits: {self.nb_products}")
        print(f"  - Dépôts: {self.nb_depots}")
        print(f"  - Garages: {self.nb_garages}")
        print(f"  - Stations: {self.nb_stations}")
        print(f"  - Véhicules: {self.nb_vehicles}")
        
        print(f"\nMatrice de coûts de transition:")
        for i, row in enumerate(self.transition_costs):
            print(f"  Produit {i+1}: {row}")
        
        print(f"\nVéhicules:")
        for v in self.vehicles[:3]:  # Afficher seulement les 3 premiers
            print(f"  V{v.id}: cap={v.capacity}, garage={v.home_garage}, produit_init={v.initial_product}")
        if len(self.vehicles) > 3:
            print(f"  ... et {len(self.vehicles)-3} autres véhicules")
        
        print(f"\nDemandes totales par produit:")
        total_demands = [0.0] * self.nb_products
        for station in self.stations:
            for p in range(self.nb_products):
                total_demands[p] += station.demands[p]
        for p in range(self.nb_products):
            print(f"  Produit {p+1}: {total_demands[p]:.0f}")
        
        print(f"{'='*60}\n")


if __name__ == "__main__":
    # Test du parser
    instance = MPVRPInstance("/mnt/user-data/uploads/MPVRP_S_018_s7_d1_p2.dat")
    instance.display_info()
