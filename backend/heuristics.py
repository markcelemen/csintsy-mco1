def manhattan(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

def composite_heuristic(pos_a, goal, positions, metadata, weights):
    distance = manhattan(pos_a, positions[goal])
    meta = metadata.get(goal, {"price": 100, "quality": 3.0, "reviews": 50})

    price = meta["price"]
    quality = meta["quality"]
    reviews = meta["reviews"]

    alpha = weights["alpha"]
    beta = weights["beta"]
    gamma = weights["gamma"]
    delta = weights["delta"]

    return alpha * distance + beta * (1 / price) + gamma * quality + delta * reviews