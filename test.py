import itertools
import pulp

class Consumer:
    def __init__(self, c_id: str, schedule: list[float]):
        self.c_id = c_id
        self.schedule = schedule

class Generator:
    def __init__(self, g_id: str, schedule: list[float], cost_per_hour: float):
        self.g_id = g_id
        self.schedule = schedule
        self.cost_per_hour = cost_per_hour

def optimize_hour(hour: int, consumers: list[Consumer], generators: list[Generator]):
    total_demand = sum(c.schedule[hour] for c in consumers)

    total_generation = sum(g.schedule[hour] for g in generators)

    disconnected_consumers = []    
    if total_demand > total_generation:
        sorted_consumers = sorted(consumers, key=lambda c: c.schedule[hour])
        while sorted_consumers and total_demand>total_generation:
            total_demand -= sorted_consumers[-1].schedule[hour]
            disconnected_consumers.append(sorted_consumers[-1].c_id)
            sorted_consumers.pop()
    
    best_cost = float('inf')
    best_gen_combo = []
        
    for mask in itertools.product([False, True], repeat=len(generators)):
        gen_combo = list(itertools.compress(generators, mask))
        gen_energy = sum(g.schedule[hour] for g in gen_combo)
        if gen_energy >= total_demand:
            cost = sum(g.cost_per_hour for g in gen_combo)
            if cost < best_cost:
                best_cost = cost
                best_gen_combo = gen_combo
    
    return {
        "hour": hour,
        "active_generators": [g.g_id for g in best_gen_combo],
        "cost": best_cost,
        "disconnected_consumers": disconnected_consumers,
        "status": "DEFICIT" if disconnected_consumers else "OK"
    }

def optimize_hour_pulp(hour: int, consumers: list[Consumer], generators: list[Generator]):
    total_demand = sum(c.schedule[hour] for c in consumers)

    generators_info=[[g.schedule[hour] for g in generators],[g.cost_per_hour for g in generators]]
    total_generation = sum(generators_info[0])

    disconnected_consumers = []    
    if total_demand>total_generation:
        sorted_consumers = sorted(consumers, key=lambda c: c.schedule[hour])
        while sorted_consumers and total_demand>total_generation:
            total_demand -= sorted_consumers[-1].schedule[hour]
            disconnected_consumers.append(sorted_consumers[-1].c_id)
            sorted_consumers.pop()
    
    
    prob = pulp.LpProblem("Minimize_Generation_Cost", pulp.LpMinimize)
    x = pulp.LpVariable.dicts("Gen", range(len(generators)), cat="Binary")
    prob += pulp.lpSum([generators_info[1][i] * x[i] for i in range(len(generators))])
    prob += pulp.lpSum([generators_info[0][i] * x[i] for i in range(len(generators))]) >= total_demand
    prob.solve(pulp.PULP_CBC_CMD(msg=False))
    active_gens = [generators[i] for i in range(len(generators)) if x[i].value() == 1.0]
    best_cost = pulp.value(prob.objective)
    
    return {
        "hour": hour,
        "active_generators": [g.g_id for g in active_gens],
        "cost": best_cost,
        "disconnected_consumers": disconnected_consumers,
        "status": "DEFICIT" if disconnected_consumers else "OK"
    }
    

def print_results(results):
    for res in results:
        status_mark = "✅" if res['status'] == "OK" else "⚠️"
        print(f"Час {res['hour']:02d}:00 {status_mark}")
        print(f"  Включенные генераторы: {', '.join(res['active_generators']) if res['active_generators'] else 'Нет'}")
        print(f"  Стоимость энергии: {res['cost']} у.е.")
        if res['disconnected_consumers']:
            print(f"  Отключенные потребители: {', '.join(res['disconnected_consumers'])}")
        print("-" * 40)

if __name__ == "__main__":
    test1_consumers=[Consumer(f"Consumer_{i}", [15.0]*24) for i in range(1, 11)]
    test1_generators = [
        Generator("Diesel_1", [100]*24, 500),
        Generator("Diesel_2", [80]*24, 400),
        Generator("Solar_1", [0]*6 + [40, 60, 80, 100, 100, 80, 60, 40] + [0]*10, 50)
    ]
    
    base_consumption = [10, 15, 20, 50, 60, 100, 120, 150, 200, 300]
    test2_consumers=[Consumer(f"Consumer_{i+1}", [base_consumption[i]] * 24) for i in range(len(base_consumption))]
    test2_generators = [
        Generator("Diesel_1", [250]*24, 1000.0),
        Generator("Diesel_2", [200]*24, 850.0),
        Generator("Solar_1", [0]*7 + [50, 100, 100, 100, 50] + [0]*12, 30),
        Generator("Solar_2", [0]*7 + [50, 100, 100, 100, 50] + [0]*12, 30)
    ]
    
    test3_consumers=[Consumer(f"Consumer_{i}", [15.0]*24) for i in range(1, 11)]
    base_gen = [10, 15, 20, 50, 60, 100, 120, 150, 200, 300, 8, 18, 28, 38, 48, 58, 68, 78, 88,98,108]
    test3_generators=[Generator(f"Diesel_{i+1}", [base_gen[i]]*24, 100 + base_gen[i] / 5) for i in range(len(base_gen))]
    
    results1 = [optimize_hour_pulp(h, test1_consumers, test1_generators) for h in range(24)]
    results2 = [optimize_hour(h, test2_consumers, test2_generators) for h in range(24)]
    #results2 = [optimize_hour(h, test3_consumers, test3_generators) for h in range(24)]
    print_results(results1)
    print("\n\n")
    print_results(results2)