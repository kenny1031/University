from typing import List, Tuple, Callable, Dict
from data_structures_for_search import (
    Node, Stack, Queue, PriorityQueue, Graph, expand
)


def bfs(problem: Graph) -> Tuple[Node, List[str]] | None:
    node = Node(state=problem.initial_state)
    frontier = Queue()
    frontier.enqueue(node)
    explored = []
    while not frontier.is_empty():
        node = frontier.dequeue()

        if node.state in explored:
            continue

        explored.append(node.state)
        if problem.is_goal(node.state):
            return node, explored

        for child in expand(problem, node):
            if child.state not in explored and not frontier.contains_state(child.state):
                frontier.enqueue(child)

    return None


def ucs(problem: Graph) -> Tuple[Node, List[str]] | None:
    node = Node(state=problem.initial_state)
    frontier = PriorityQueue()
    frontier.enqueue(node, node.path_cost)
    best_cost = {problem.initial_state: 0.0}

    explored = []
    while not frontier.is_empty():
        node = frontier.dequeue()
        if node.state not in explored:
            explored.append(node.state)

        if node.path_cost > best_cost.get(node.state, float("inf")):
            continue

        if problem.is_goal(node.state):
            return node, explored

        for child in expand(problem, node):
            if child.path_cost < best_cost.get(child.state, float("inf")):
                best_cost[child.state] = child.path_cost
                frontier.enqueue(child, child.path_cost)

    return None


def dfs(problem) -> Tuple[Node | None, List[str]]:
    node = Node(state=problem.initial_state)
    frontier = Stack()
    frontier.push(node)
    explored = []

    while not frontier.is_empty():
        node = frontier.pop()
        if node.state not in explored:
            explored.append(node.state)
        else:
            continue

        if problem.is_goal(node.state):
            return node, explored

        children = expand(problem, node)
        for child in reversed(children):
            if (child.state not in explored and
                not frontier.contains_state(child.state)):
                frontier.push(child)

    return None, explored


def dls(
    problem: Graph,
    limit: int # max level dist from initial state
) -> Tuple[Node | None, List[str]]:
    node = Node(state=problem.initial_state)
    frontier = Stack()
    frontier.push(node)

    explored = []

    while not frontier.is_empty():
        node = frontier.pop()
        if node.state in explored:
            continue

        explored.append(node.state)
        if problem.is_goal(node.state):
            return node, explored

        if node.depth == limit:
            continue

        for child in reversed(expand(problem, node)):
            if (child.state not in explored and
                not frontier.contains_state(child.state)):
                frontier.push(child)

    return None, explored


def ids(problem: Graph, max_depth: int) -> Tuple[Node | None, List[str]]:
    explored = []
    for depth in range(max_depth+1):
        result, exp = dls(problem, depth)
        explored += exp
        if result is not None:
            return result, explored
    return None, explored

def best_first_search(
    problem: Graph,
    f: Callable[[Node], float]
) -> Tuple[Node | None, List[str]]:
    node = Node(state=problem.initial_state)
    frontier = PriorityQueue()
    frontier.enqueue(node, f(node))

    best_priority = {problem.initial_state: f(node)}
    explored = []

    while not frontier.is_empty():
        node = frontier.dequeue()
        current_priority = f(node)
        if node.state not in explored:
            explored.append(node.state)

        if current_priority > best_priority.get(node.state, float("inf")):
            continue

        if problem.is_goal(node.state):
            return node, explored

        for child in expand(problem, node):
            child_priority = f(child)
            if child_priority < best_priority.get(child.state, float("inf")):
                best_priority[child.state] = child_priority
                frontier.enqueue(child, child_priority)

    return None, explored

def greedy_best_first(
    problem: Graph,
    heuristic: Dict[str, float]
) -> Tuple[Node | None, List[str]]:
    return best_first_search(
        problem,
        f=lambda node: heuristic[node.state]
    )

if __name__ == '__main__':
    goals = ["G"]
    graph1 = Graph(initial_state="A", goal_states=goals)
    graph1.add_edge("A", "B", 5)
    graph1.add_edge("A", "C", 3)
    graph1.add_edge("A", "D", 1)
    graph1.add_edge("B", "E", 4)
    graph1.add_edge("B", "F", 2)
    graph1.add_edge("D", "G", 1)

    # goal_node, reached = dls(graph, limit=1)

    heuristic = {"A": 4, "B": 3, "C": 2, "D": 1, "G": 0}

    # goal_node, reached = greedy_best_first(graph, heuristic)
    goal_node, reached = ids(graph1, 1)

    print("Path:", reached)