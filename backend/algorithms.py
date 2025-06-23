import heapq
from heuristics import manhattan, composite_heuristic

def uniform_cost_search(graph, start, goals):
    goals_set = set(goals)
    queue = [(0, [start])]
    visited = set()

    while queue:
        cost, path = heapq.heappop(queue)
        node = path[-1]

        if node in goals_set:
            return path, cost

        if node in visited:
            continue
        visited.add(node)

        for neighbor, weight in graph.get(node, {}).items():
            if neighbor not in visited:
                heapq.heappush(queue, (cost + weight, path + [neighbor]))

    return None, float('inf')

def a_star_search(graph, positions, start, goals, metadata, weights):
    goals_set = set(goals)
    queue = [(0, 0, [start])]
    visited = set()

    while queue:
        est_total, cost, path = heapq.heappop(queue)
        node = path[-1]

        if node in goals_set:
            return path, cost

        if node in visited:
            continue
        visited.add(node)

        for neighbor, weight in graph.get(node, {}).items():
            if neighbor not in visited:
                g = cost + weight
                h = min(composite_heuristic(positions[neighbor], goal, positions, metadata, weights) for goal in goals)
                heapq.heappush(queue, (g + h, g, path + [neighbor]))

    return None, float('inf')