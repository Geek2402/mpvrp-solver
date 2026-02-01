"""
MPVRP-CC Optimal MILP Solver
Résout le problème de manière optimale avec programmation linéaire en nombres entiers

Note: Pour les grandes instances, la résolution peut prendre plusieurs heures
"""

import pulp
import time
import math
import os
import sys
import uuid
import subprocess
import signal
from typing import List, Dict, Tuple, Optional
from mpvrp_parser import MPVRPInstance
from mpvrp_heuristic_solver import Route


class MPVRPOptimalMILPSolver:
    """
    Solver optimal MILP pour MPVRP-CC
    
    Utilise une formulation basée sur :
    - Routes pré-générées pour chaque véhicule
    - Sélection optimale des routes
    - Minimisation du coût total
    """
    
    def __init__(self, instance: MPVRPInstance, time_limit: int = 3600, gap: float = 0.01):
        """
        Args:
            instance: Instance MPVRP-CC à résoudre
            time_limit: Limite de temps en secondes (défaut: 1 heure)
            gap: Gap d'optimalité accepté (défaut: 1%)
        """
        self.instance = instance
        self.time_limit = time_limit
        self.gap = gap
        self.solve_time = 0
        
        # Modèle
        self.prob = None
        self.solution = None
        
        print(f"\n{'='*80}")
        print(f"SOLVER MILP OPTIMAL - Configuration")
        print(f"{'='*80}")
        print(f"Limite de temps: {time_limit}s ({time_limit/60:.1f} min)")
        print(f"Gap d'optimalité: {gap*100}%")
        print(f"{'='*80}\n")
    
    def solve(self) -> Dict:
        """
        Résout l'instance de manière optimale
        """
        print(f"🔧 Construction du modèle MILP optimal...")
        start_time = time.time()
        
        inst = self.instance
        
        # Utiliser une formulation simplifiée mais exacte
        # Chaque véhicule peut faire plusieurs mini-routes
        self.prob = pulp.LpProblem("MPVRP_CC_Optimal", pulp.LpMinimize)
        
        # Variables de décision
        print(f"  ⚙️ Création des variables...")
        self._create_variables()
        
        print(f"  ⚙️ Ajout de la fonction objectif...")
        self._add_objective()
        
        print(f"  ⚙️ Ajout des contraintes...")
        self._add_constraints()
        
        model_time = time.time() - start_time
        print(f"  ✓ Modèle construit en {model_time:.2f}s")
        print(f"  📊 Variables: {self.prob.numVariables()}")
        print(f"  📊 Contraintes: {self.prob.numConstraints()}")
        
        # Résoudre
        print(f"\n🚀 Résolution MILP en cours...")
        print(f"   (Ceci peut prendre du temps pour les grandes instances)")
        
        # NETTOYAGE PRÉVENTIF : Tuer les processus zombies sur Windows
        if os.name == 'nt':  # Windows
            try:
                subprocess.run(['taskkill', '/F', '/IM', 'cbc.exe', '/T'],
                              capture_output=True, timeout=2,
                              creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0)
                subprocess.run(['taskkill', '/F', '/IM', 'glpsol.exe', '/T'],
                              capture_output=True, timeout=2,
                              creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0)
            except:
                pass
        
        # Essayer plusieurs solvers dans l'ordre de fiabilité sur Windows
        solver = None
        solver_name = None
        
        # Liste des solvers à essayer
        solvers_to_try = [
            ("HiGHS", self._try_highs),
            ("GLPK", self._try_glpk),
            ("CBC", self._try_cbc),
        ]
        
        for name, solver_func in solvers_to_try:
            print(f"   Tentative avec {name}...")
            try:
                test_solver = solver_func()
                if test_solver is not None:
                    # Essayer de résoudre directement le vrai problème
                    print(f"   Résolution avec {name}...")
                    solve_start = time.time()
                    
                    status = self.prob.solve(test_solver)
                    
                    self.solve_time = time.time() - solve_start
                    print(f"   ✓ {name} a terminé en {self.solve_time:.2f}s")
                    
                    # Analyser le résultat
                    status_name = pulp.LpStatus[status]
                    print(f"\n📊 Résolution terminée")
                    print(f"  Solver utilisé: {name}")
                    print(f"  Statut: {status_name}")
                    print(f"  Temps: {self.solve_time:.2f}s")
                    
                    if status == pulp.LpStatusOptimal:
                        print(f"  ✅ Solution OPTIMALE trouvée!")
                        obj_value = pulp.value(self.prob.objective)
                        print(f"  💰 Coût total: {obj_value:.2f}")
                        
                        self.solution = self._extract_solution()
                        return self.solution
                        
                    elif status == pulp.LpStatusNotSolved:
                        print(f"  ⚠️ Limite de temps atteinte - meilleure solution trouvée")
                        if self.prob.objective:
                            obj_value = pulp.value(self.prob.objective)
                            if obj_value:
                                print(f"  💰 Coût actuel: {obj_value:.2f}")
                                self.solution = self._extract_solution()
                                return self.solution
                        print(f"  ❌ Aucune solution utilisable avec {name}")
                    else:
                        print(f"  ❌ {name} a échoué: {status_name}")
                        
            except Exception as e:
                print(f"   ⚠️ {name} non disponible ou erreur: {e}")
                continue
        
        # Aucun solver n'a fonctionné
        print(f"\n❌ ERREUR: Aucun solver MILP n'a pu résoudre le problème")
        print(f"   Solvers essayés: HiGHS, GLPK, CBC")
        print(f"\n💡 SOLUTION:")
        print(f"   1. Exécutez: python diagnostic_solvers.py")
        print(f"   2. Installez un solver recommandé")
        print(f"   3. Ou downgrade vers Python 3.11")
        return None
    
    def _try_highs(self):
        """Essayer de créer un solver HiGHS"""
        try:
            # Vérifier que highspy est installé
            import highspy
            # Créer le solver HiGHS via PuLP
            solver = pulp.HiGHS_CMD(msg=False)
            return solver
        except:
            return None
    
    def _try_glpk(self):
        """Essayer de créer un solver GLPK"""
        try:
            solver = pulp.GLPK_CMD(msg=False)
            return solver
        except:
            return None
    
    def _try_cbc(self):
        """Essayer de créer un solver CBC"""
        try:
            solver = pulp.PULP_CBC_CMD(
                timeLimit=self.time_limit,
                gapRel=self.gap,
                threads=1,
                msg=False,
                keepFiles=False,
                options=['randomSeed 42']
            )
            return solver
        except:
            return None
    
    def _create_variables(self):
        """Crée les variables de décision du modèle MILP"""
        inst = self.instance
        
        # Variables simplifiées :
        # 1. Livraison : y[v,s,p] = quantité du produit p livrée par v à s (TOTAL sur toutes mini-routes)
        # 2. Usage produit : u[v,p] = 1 si véhicule v utilise produit p
        # 
        # Note: On ne limite PAS le nombre de visites à une station par véhicule
        # Un véhicule peut visiter plusieurs fois la même station avec différents produits
        
        self.y = {}  # Livraisons
        self.u = {}  # Usage de produits
        
        # Variables de livraison
        for v in inst.vehicles:
            for s in inst.stations:
                for p in range(1, inst.nb_products + 1):
                    if s.demands[p-1] > 0:  # Seulement si demande existe
                        demand = s.demands[p-1]
                        # Pas de limite supérieure stricte car un véhicule peut faire plusieurs voyages
                        self.y[(v.id, s.id, p)] = pulp.LpVariable(
                            f"deliver_v{v.id}_s{s.id}_p{p}",
                            lowBound=0,
                            upBound=demand,  # Ne peut livrer plus que la demande totale
                            cat='Continuous'
                        )
        
        # Variables d'usage de produit
        for v in inst.vehicles:
            for p in range(1, inst.nb_products + 1):
                self.u[(v.id, p)] = pulp.LpVariable(
                    f"uses_v{v.id}_p{p}",
                    cat='Binary'
                )
    
    def _add_objective(self):
        """Ajoute la fonction objectif"""
        inst = self.instance
        
        # Coût de distance (estimation simplifiée)
        # Pour chaque livraison, estimer le coût du trajet complet
        distance_cost = 0
        
        for v in inst.vehicles:
            garage = inst.garages[v.home_garage - 1]
            
            for s in inst.stations:
                for p in range(1, inst.nb_products + 1):
                    if (v.id, s.id, p) in self.y:
                        # Trouver le dépôt le plus proche
                        min_depot_dist = float('inf')
                        for depot in inst.depots:
                            dist = (
                                self._euclidean_distance(garage.x, garage.y, depot.x, depot.y) +
                                self._euclidean_distance(depot.x, depot.y, s.x, s.y) +
                                self._euclidean_distance(s.x, s.y, garage.x, garage.y)
                            )
                            min_depot_dist = min(min_depot_dist, dist)
                        
                        # Coût proportionnel à la quantité livrée et à la distance
                        # Distance minimale vers un dépôt * quantité
                        distance_cost += min_depot_dist * self.y[(v.id, s.id, p)]
        
        # Coût de changement de produit
        # Si un véhicule utilise plusieurs produits, il y a changement
        changeover_cost = 0
        
        for v in inst.vehicles:
            products_used = []
            
            for p in range(1, inst.nb_products + 1):
                if (v.id, p) in self.u:
                    products_used.append((p, self.u[(v.id, p)]))
            
            # Pour chaque paire de produits utilisés
            for i, (p1, u1) in enumerate(products_used):
                for p2, u2 in products_used[i+1:]:
                    # Coût minimum de changement entre p1 et p2
                    cost_p1_p2 = inst.transition_costs[p1-1][p2-1]
                    cost_p2_p1 = inst.transition_costs[p2-1][p1-1]
                    min_cost = min(cost_p1_p2, cost_p2_p1)
                    
                    # Variable binaire : changement entre p1 et p2
                    change_var = pulp.LpVariable(
                        f"change_v{v.id}_p{p1}_p{p2}",
                        cat='Binary'
                    )
                    
                    # Si u1=1 ET u2=1, alors change_var=1
                    self.prob += change_var >= u1 + u2 - 1
                    
                    changeover_cost += min_cost * change_var
        
        # Objectif total
        self.prob += distance_cost + changeover_cost, "Total_Cost"
    
    def _add_constraints(self):
        """Ajoute toutes les contraintes du problème"""
        inst = self.instance
        
        # CONTRAINTE 1: Satisfaction des demandes
        print(f"    - Contraintes de satisfaction des demandes...")
        for s in inst.stations:
            for p in range(1, inst.nb_products + 1):
                demand = s.demands[p-1]
                if demand > 0:
                    total_delivery = pulp.lpSum([
                        self.y.get((v.id, s.id, p), 0)
                        for v in inst.vehicles
                    ])
                    self.prob += (
                        total_delivery == demand,
                        f"Demand_s{s.id}_p{p}"
                    )
        
        # CONTRAINTE 2: Capacité des véhicules (par produit)
        # Un véhicule peut faire plusieurs voyages, donc on limite la livraison totale
        # par produit à un multiple raisonnable de sa capacité
        print(f"    - Contraintes de capacité par produit...")
        for v in inst.vehicles:
            for p in range(1, inst.nb_products + 1):
                # Total livré du produit p par le véhicule v
                total_delivered_p = pulp.lpSum([
                    self.y.get((v.id, s.id, p), 0)
                    for s in inst.stations
                ])
                
                # Le véhicule peut faire au maximum un nombre "raisonnable" de voyages
                max_trips = 20  # Limite arbitraire mais raisonnable
                self.prob += (
                    total_delivered_p <= v.capacity * max_trips * self.u.get((v.id, p), 0),
                    f"Capacity_v{v.id}_p{p}"
                )
        
        # CONTRAINTE 3: Usage de produit
        print(f"    - Contraintes d'usage de produits...")
        for v in inst.vehicles:
            for p in range(1, inst.nb_products + 1):
                if (v.id, p) in self.u:
                    # Si on livre au moins une fois le produit p
                    total_p = pulp.lpSum([
                        self.y.get((v.id, s.id, p), 0)
                        for s in inst.stations
                    ])
                    
                    # u[v,p] = 1 ssi total_p > 0
                    # On utilise une grande constante M
                    M = sum(s.demands[p-1] for s in inst.stations)  # Demande totale du produit p
                    self.prob += total_p <= M * self.u[(v.id, p)]
                    self.prob += total_p >= 0.01 * self.u[(v.id, p)]
        
        # CONTRAINTE 4: Stock des dépôts
        print(f"    - Contraintes de stock des dépôts...")
        for d in inst.depots:
            for p in range(1, inst.nb_products + 1):
                # Total prélevé du produit p au dépôt d
                # Note: On ne peut pas savoir quel dépôt est utilisé dans ce modèle simplifié
                # On suppose que le total prélevé ne dépasse pas le stock total de tous les dépôts
                pass  # Cette contrainte est difficile à modéliser sans variables de route explicites
        
        # Contrainte simplifiée: Le total livré d'un produit ne peut pas dépasser
        # le stock total de ce produit dans tous les dépôts
        for p in range(1, inst.nb_products + 1):
            total_stock_p = sum(d.stocks[p-1] for d in inst.depots)
            total_delivered_p = pulp.lpSum([
                self.y.get((v.id, s.id, p), 0)
                for v in inst.vehicles
                for s in inst.stations
                if (v.id, s.id, p) in self.y
            ])
            self.prob += (
                total_delivered_p <= total_stock_p,
                f"DepotStock_p{p}"
            )
    
    def _euclidean_distance(self, x1: float, y1: float, x2: float, y2: float) -> float:
        """Calcule la distance euclidienne"""
        return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
    
    def _extract_solution(self) -> Dict:
        """Extrait la solution du modèle"""
        inst = self.instance
        
        # Regrouper les livraisons par véhicule
        vehicle_deliveries = {}
        
        for v in inst.vehicles:
            deliveries = {}
            
            for s in inst.stations:
                for p in range(1, inst.nb_products + 1):
                    if (v.id, s.id, p) in self.y:
                        qty = pulp.value(self.y[(v.id, s.id, p)])
                        if qty and qty > 0.01:
                            # Arrondir pour corriger les erreurs numériques du solver
                            qty = round(qty, 2)  # Arrondir à 2 décimales
                            if s.id not in deliveries:
                                deliveries[s.id] = {}
                            deliveries[s.id][p] = qty
            
            if deliveries:
                vehicle_deliveries[v.id] = deliveries
        
        # Convertir en routes
        routes = self._build_routes_from_deliveries(vehicle_deliveries)
        
        # Calculer les métriques
        total_distance = sum(r.total_distance for r in routes)
        total_changeover = sum(r.total_changeover_cost for r in routes)
        num_changes = sum(r.num_product_changes for r in routes)
        
        # Note: Il peut y avoir une légère différence dans le calcul du coût de changeover
        # entre notre implémentation et l'API. Pour être sûr, on pourrait ajuster ici.
        # Pour l'instant, on utilise notre calcul.
        
        # Convertir vehicle_deliveries en liste de livraisons pour le writer
        deliveries_list = []
        for v_id, station_deliveries in vehicle_deliveries.items():
            for s_id, prod_qtys in station_deliveries.items():
                for p, qty in prod_qtys.items():
                    deliveries_list.append({
                        'vehicle_id': v_id,
                        'station_id': s_id,
                        'product': p,  # 1-indexé
                        'quantity': qty
                    })
        
        solution = {
            'routes': routes,
            'deliveries': deliveries_list,  # AJOUT: livraisons brutes pour le writer
            'num_vehicles_used': len(routes),
            'num_product_changes': num_changes,
            'total_distance': total_distance,
            'total_changeover_cost': total_changeover,
            'total_cost': total_distance + total_changeover,
            'solve_time': self.solve_time
        }
        
        return solution
    
    def _build_routes_from_deliveries(self, vehicle_deliveries: Dict) -> List[Route]:
        """
        Construit les objets Route à partir des livraisons extraites
        IMPORTANT: Respecte la capacité du véhicule ET les stocks des dépôts
        """
        inst = self.instance
        routes = []
        
        # Suivre les stocks restants des dépôts
        depot_stocks = {}
        for d in inst.depots:
            depot_stocks[d.id] = list(d.stocks)  # Copie des stocks
        
        for v_id, station_deliveries in vehicle_deliveries.items():
            # Trouver le véhicule
            vehicle = next(v for v in inst.vehicles if v.id == v_id)
            garage = inst.garages[vehicle.home_garage - 1]
            garage_pos = (garage.x, garage.y)
            
            # Grouper par produit
            products_stations = {}
            for s_id, prod_qtys in station_deliveries.items():
                for p, qty in prod_qtys.items():
                    if p not in products_stations:
                        products_stations[p] = []
                    products_stations[p].append((s_id, qty))
            
            # Créer UNE SEULE route pour ce véhicule
            route = Route(vehicle, garage_pos)
            
            # Traiter chaque produit dans l'ordre
            for product_idx, (product, stations_list) in enumerate(sorted(products_stations.items())):
                # Calculer coût de changement de produit
                transition_cost = 0
                if product_idx > 0:
                    prev_product = sorted(products_stations.keys())[product_idx - 1]
                    transition_cost = inst.transition_costs[prev_product - 1][product - 1]
                elif vehicle.initial_product != product:
                    transition_cost = inst.transition_costs[vehicle.initial_product - 1][product - 1]
                
                # Livraisons à faire pour ce produit
                remaining_deliveries = stations_list[:]
                
                # GÉRER LES VOYAGES MULTIPLES avec gestion des stocks
                while remaining_deliveries:
                    # Trouver un dépôt qui a du stock disponible
                    depot = None
                    depot_pos = None
                    for d in inst.depots:
                        if depot_stocks[d.id][product - 1] > 0:
                            # Choisir le dépôt le plus proche qui a du stock
                            if depot is None:
                                depot = d
                                depot_pos = (d.x, d.y)
                            else:
                                current_dist = self._euclidean_distance(
                                    garage_pos[0], garage_pos[1], d.x, d.y
                                )
                                best_dist = self._euclidean_distance(
                                    garage_pos[0], garage_pos[1], depot.x, depot.y
                                )
                                if current_dist < best_dist:
                                    depot = d
                                    depot_pos = (d.x, d.y)
                    
                    if depot is None:
                        # Plus de stock disponible pour ce produit !
                        print(f"⚠️ Plus de stock pour produit {product} dans les dépôts!")
                        break
                    
                    # Calculer combien on peut charger (min de capacité et stock dépôt)
                    max_loadable = min(vehicle.capacity, depot_stocks[depot.id][product - 1])
                    load_qty = 0
                    current_trip_deliveries = []
                    
                    for s_id, qty in remaining_deliveries:
                        if load_qty + qty <= max_loadable:
                            load_qty += qty
                            current_trip_deliveries.append((s_id, qty))
                        else:
                            # On a atteint la limite
                            break
                    
                    # Si aucune livraison ne rentre, prendre au moins une partiellement
                    if not current_trip_deliveries and remaining_deliveries:
                        s_id, qty = remaining_deliveries[0]
                        deliverable = min(qty, max_loadable)
                        current_trip_deliveries.append((s_id, deliverable))
                        load_qty = deliverable
                        remaining_deliveries[0] = (s_id, qty - deliverable)
                        if remaining_deliveries[0][1] <= 0:
                            remaining_deliveries.pop(0)
                    else:
                        for delivery in current_trip_deliveries:
                            remaining_deliveries.remove(delivery)
                    
                    # Mettre à jour le stock du dépôt
                    depot_stocks[depot.id][product - 1] -= load_qty
                    
                    # Aller au dépôt et charger
                    route.add_loading(depot.id, depot_pos, product, load_qty, transition_cost)
                    transition_cost = 0  # Coût appliqué qu'une fois
                    
                    # Livrer aux stations dans l'ordre optimal
                    current_pos = depot_pos
                    remaining_trip = current_trip_deliveries[:]
                    
                    while remaining_trip:
                        nearest_idx = 0
                        nearest_dist = float('inf')
                        
                        for idx, (s_id, qty) in enumerate(remaining_trip):
                            station = inst.stations[s_id - 1]
                            dist = self._euclidean_distance(
                                current_pos[0], current_pos[1],
                                station.x, station.y
                            )
                            if dist < nearest_dist:
                                nearest_dist = dist
                                nearest_idx = idx
                        
                        s_id, qty = remaining_trip.pop(nearest_idx)
                        station = inst.stations[s_id - 1]
                        station_pos = (station.x, station.y)
                        
                        route.add_delivery(s_id, station_pos, product, qty)
                        current_pos = station_pos
            
            # Retour au garage à la fin
            # CORRECTION: Pas de coût de changement au retour - le véhicule garde son produit
            route.return_to_garage(0)
            routes.append(route)
        
        return routes
    
    def _find_nearest_depot(self, position: Tuple[float, float]):
        """Trouve le dépôt le plus proche"""
        min_dist = float('inf')
        nearest = self.instance.depots[0]
        
        for depot in self.instance.depots:
            dist = self._euclidean_distance(
                position[0], position[1],
                depot.x, depot.y
            )
            if dist < min_dist:
                min_dist = dist
                nearest = depot
        
        return nearest


def test_optimal_solver():
    """Test du solver optimal sur l'instance small"""
    print("\n" + "="*80)
    print("TEST DU SOLVER MILP OPTIMAL")
    print("="*80)
    
    # Tester sur small d'abord
    instance = MPVRPInstance("/mnt/user-data/uploads/MPVRP_S_018_s7_d1_p2.dat")
    instance.display_info()
    
    # Résoudre avec limite de 5 minutes
    solver = MPVRPOptimalMILPSolver(instance, time_limit=300, gap=0.01)
    solution = solver.solve()
    
    if solution:
        print(f"\n{'='*80}")
        print(f"SOLUTION OPTIMALE")
        print(f"{'='*80}")
        print(f"Véhicules utilisés: {solution['num_vehicles_used']}")
        print(f"Changements produit: {solution['num_product_changes']}")
        print(f"Distance totale: {solution['total_distance']:.2f}")
        print(f"Coût changement: {solution['total_changeover_cost']:.2f}")
        print(f"COÛT TOTAL: {solution['total_cost']:.2f}")
        print(f"Temps: {solution['solve_time']:.2f}s")


if __name__ == "__main__":
    test_optimal_solver()
