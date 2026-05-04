from typing import List, Tuple, Dict
from data_structures_for_search import Node, PriorityQueue, Graph, expand

heuristic = {
    'S': 3,
    'A': 2,
    'B': 1,
    'C': 0,
    'D': 1,
    'E': 0,
    'F': 2,
    'G': 1,
    'H': 15,
    'I': 0,
    'J': 3,
    'K': 0,
}


def a_star_search(
    problem: Graph,
    heuristic: Dict[str, float | int] = heuristic
) -> Tuple[Node | None, List[str]]:
    node = Node(state=problem.initial_state)
    fringe = PriorityQueue()
    fringe.enqueue(node, node.path_cost + heuristic[node.state])

    best_cost = {problem.initial_state: 0.0}
    explored = []

    while not fringe.is_empty():
        node = fringe.dequeue()
        if node.path_cost > best_cost.get(node.state, float("inf")):
            continue

        if node.state not in explored:
            explored.append(node.state)

        if problem.is_goal(node.state):
            return node, explored

        for child in expand(problem, node):
            if child.path_cost < best_cost.get(child.state, float("inf")):
                best_cost[child.state] = child.path_cost
                fringe.enqueue(child, child.path_cost + heuristic[child.state])

    return None, explored

if __name__ == "__main__":
    graph = Graph(
        initial_state='S',
        goal_states=['C', 'E', 'I', 'K']
    )
    graph.add_edge('S', 'A', 4)
    graph.add_edge('S', 'B', 3)
    graph.add_edge('A', 'C', 4)
    graph.add_edge('A', 'D', 1)
    graph.add_edge('D', 'H', 0)
    graph.add_edge('D', 'I', 1)
    graph.add_edge('D', 'J', 6)
    graph.add_edge('B', 'E', 5)
    graph.add_edge('B', 'F', 4)
    graph.add_edge('B', 'G', 1)
    graph.add_edge('G', 'K', 3)

    goal, path = a_star_search(graph)
    print(path)