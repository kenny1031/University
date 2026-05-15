from collections import deque
from typing import Tuple, List
import heapq
from data_structures import Node, TreasureMap


class SearchAgent:
    def __init__(self, game_map: TreasureMap, strategy: str):
        self.game_map = game_map
        self.strategy = strategy
        self.counter = 0
        self.strategy_map = {
            'B': ("BFS", self._bfs),
            'D': ("DFS", self._dfs),
            'U': ("UCS", self._ucs),
            'G': ("Greedy", self._greedy),
            'A': ("A*", self._astar),
            'H': ("Hill-climbing", self._hill_climbing),
        }

    def _next_order(self) -> int:
        order = self.counter
        self.counter += 1
        return order

    def run(self) -> Tuple[str, List[Tuple[int, int]], Node]:
        if self.strategy not in self.strategy_map:
            raise ValueError("Invalid strategy")
        strategy_name, strategy_func = self.strategy_map[self.strategy]
        expanded_order, goal_node = strategy_func()
        return strategy_name, expanded_order, goal_node

    def _is_goal(self, node: Node) -> bool:
        return node.state == self.game_map.goal

    def _push_priority_node(self, heap, priority, node) -> None:
        x, y = node.state
        heapq.heappush(heap, (priority, x, y, self._next_order(), node))

    def _bfs(self) -> Tuple[List[Tuple[int, int]],
                            Node | None]:
        start_node = Node(self.game_map.start)
        fringe = deque([start_node])
        expanded = set()
        expanded_order = []

        while fringe:
            node = fringe.popleft()

            if node.state in expanded:
                continue

            expanded.add(node.state)
            expanded_order.append(node.state)

            if self._is_goal(node):
                return expanded_order, node

            children = self.game_map.get_children(node)
            for child in children:
                fringe.append(child)

        return expanded_order, None

    def _dfs(self) -> Tuple[List[Tuple[int, int]],
                            Node | None]:
        start_node = Node(self.game_map.start)
        fringe = [start_node]
        expanded = set()
        expanded_order = []

        while fringe:
            node = fringe.pop()

            if node.state in expanded:
                continue

            expanded.add(node.state)
            expanded_order.append(node.state)

            if self._is_goal(node):
                return expanded_order, node

            children = self.game_map.get_children(node)

            # reverse push so LEFT, RIGHT, UP, DOWN is expanded first
            for child in reversed(children):
                fringe.append(child)

        return expanded_order, None

    def _ucs(self) -> Tuple[List[Tuple[int, int]],
                            Node | None]:
        start_node = Node(self.game_map.start)
        fringe = []
        self._push_priority_node(fringe, start_node.g, start_node)

        expanded = set()
        expanded_order = []

        while fringe:
            _, _, _, _, node = heapq.heappop(fringe)

            if node.state in expanded:
                continue

            expanded.add(node.state)
            expanded_order.append(node.state)

            if self._is_goal(node):
                return expanded_order, node

            children = self.game_map.get_children(node)
            for child in children:
                self._push_priority_node(fringe, child.g, child)

        return expanded_order, None

    def _greedy(self) -> Tuple[List[Tuple[int, int]],
                               Node | None]:
        start_node = Node(self.game_map.start)
        fringe = []
        self._push_priority_node(fringe, self.game_map.heuristic(start_node.state), start_node)

        expanded = set()
        expanded_order = []

        while fringe:
            _, _, _, _, node = heapq.heappop(fringe)

            if node.state in expanded:
                continue

            expanded.add(node.state)
            expanded_order.append(node.state)

            if self._is_goal(node):
                return expanded_order, node

            children = self.game_map.get_children(node)
            for child in children:
                h = self.game_map.heuristic(child.state)
                self._push_priority_node(fringe, h, child)

        return expanded_order, None

    def _astar(self) -> Tuple[List[Tuple[int, int]],
                              Node | None]:
        start_node = Node(self.game_map.start)
        fringe = []
        start_f = start_node.g + self.game_map.heuristic(start_node.state)
        self._push_priority_node(fringe, start_f, start_node)

        expanded = set()
        expanded_order = []

        while fringe:
            _, _, _, _, node = heapq.heappop(fringe)

            if node.state in expanded:
                continue

            expanded.add(node.state)
            expanded_order.append(node.state)

            if self._is_goal(node):
                return expanded_order, node

            children = self.game_map.get_children(node)
            for child in children:
                f = child.g + self.game_map.heuristic(child.state)
                self._push_priority_node(fringe, f, child)

        return expanded_order, None

    def _hill_climbing(self) -> Tuple[List[Tuple[int, int]],
                                      Node | None]:
        current = Node(self.game_map.start)
        expanded = set()
        expanded_order = []

        while True:
            if current.state in expanded:
                return expanded_order, None

            expanded.add(current.state)
            expanded_order.append(current.state)

            if self._is_goal(current):
                return expanded_order, current

            current_h = self.game_map.heuristic(current.state)
            children = self.game_map.get_children(current)

            candidates = []
            for child in children:
                if child.state in expanded:
                    continue
                h = self.game_map.heuristic(child.state)
                x, y = child.state
                candidates.append((h, x, y, self._next_order(), child))

            if not candidates:
                return expanded_order, None

            candidates.sort(key=lambda item: (item[0], item[1], item[2], item[3]))
            best_h, _, _, _, best_child = candidates[0]

            if best_h < current_h:
                current = best_child
            else:
                return expanded_order, None