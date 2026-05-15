import argparse
from typing import List, Tuple
from data_structures import Node, TreasureMap
from search_algorithms import SearchAgent


# ============ utils & helpers ===================
def reconstruct_path(goal_node: Node) -> List[Tuple[int, int]]:
    path = []
    current = goal_node
    while current is not None:
        path.append(current.state)
        current = current.parent
    path.reverse()
    return path

def format_expanded(expanded_order: List[Tuple[int, int]]) -> str:
    return "".join(f"({x}, {y})" for x, y in expanded_order)

def format_path(path: List[Tuple[int, int]]) -> str:
    return "[" + ", ".join(f"({x}, {y})" for x, y in path) + "]"

def print_result(
    strategy_name: str,
    expanded_order: List[Tuple[int, int]],
    goal_node: Node
) -> None:
    print(f"{strategy_name} Search Initiated")
    print(f"Expanded: {format_expanded(expanded_order)}")

    if goal_node is None:
        print("NO PATH FOUND!")
    else:
        path = reconstruct_path(goal_node)
        print(f"Path Found: {format_path(path)}")
        print(f"Taking this path will cost: {goal_node.g} Willpower")


# ========= Main logic ==================
def main(strategy: str, filename: str) -> None:
    try:
        strategy = strategy.upper()
        game_map = TreasureMap.from_file(filename)
        agent = SearchAgent(game_map, strategy)
        strategy_name, expanded_order, goal_node = agent.run()
        print_result(strategy_name, expanded_order, goal_node)
    except Exception as e:
        print(e)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Run game")
    parser.add_argument("--strategy", choices=["B", "D", "U", "G", "A", "H"], default='B', help="search algorithm.")
    parser.add_argument("--filename", default="example1.txt", help="Directory of file storing map")
    args = parser.parse_args()

    main(args.strategy, args.filename)