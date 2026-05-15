from __future__ import annotations
from typing import Tuple, Dict, List, Optional


class Node:
    def __init__(
        self,
        state: Tuple[int, int],
        parent: Node | None = None,
        g: int = 0
    ):
        self.state = state
        self.parent = parent
        self.g = g


class TreasureMap:
    def __init__(
        self,
        width: int,
        height: int,
        start: Tuple[int, int],
        goal: Tuple[int, int],
        grid: List[List[str]],
        portal_map: Dict[Tuple[int, int], Tuple[int, int]]
    ):
        self.width = width
        self.height = height
        self.start = start
        self.goal = goal
        self.grid = grid
        self.portal_map = portal_map # {(entrance_x, entrance_y): (exit_x, exit_y)}

    @classmethod
    def from_file(cls, filename: str) -> "TreasureMap":
        with open(filename, 'r') as f:
            lines = [line.strip() for line in f if line.strip()]

        # line 1: dimensions, e.g. "5x2"
        dim_line = lines[0]
        width_str, height_str = dim_line.split('x')
        width = int(width_str)
        height = int(height_str)

        # line 2: start position, e.g. "0-0"
        start_line = lines[1]
        start_x_str, start_y_str = start_line.split('-')
        start = (int(start_x_str), int(start_y_str))

        # remaining lines: map layout
        raw_rows = lines[2:]
        grid = [list(row) for row in raw_rows]

        # find goal and digit tiles
        goal = None
        digit_positions = {}  # {'1': (x,y), '2': (x,y), ...}

        for y in range(height):
            for x in range(width):
                tile = grid[y][x]
                if tile == 'X':
                    goal = (x, y)
                elif tile.isdigit():
                    digit_positions[tile] = (x, y)

        # build portal mapping: odd digit -> next even digit
        portal_map = {}
        for digit_char, entrance_pos in digit_positions.items():
            digit = int(digit_char)
            if digit % 2 == 1:
                exit_char = str(digit + 1)
                if exit_char in digit_positions:
                    portal_map[entrance_pos] = digit_positions[exit_char]

        return cls(width, height, start, goal, grid, portal_map)


    def in_bounds(self, x, y):
        return 0 <= x < self.width and 0 <= y < self.height

    def get_tile(self, state):
        x, y = state
        return self.grid[y][x]

    def is_wall(self, tile):
        return tile == 'W'

    def is_portal_entrance(self, state):
        return state in self.portal_map

    def move_cost(self, tile):
        if tile == 'M':
            return 2
        if tile == 'B':
            return 3
        return 1

    def heuristic(self, state):
        """
        Manhattan distance to the goal
        Special case: if state is a portal entrance, use the heuristic of its exit
        """
        if self.is_portal_entrance(state):
            state = self.portal_map[state]

        x, y = state
        gx, gy = self.goal
        return abs(x - gx) + abs(y - gy)

    def get_children(self, node):
        """
        Return children in LEFT, RIGHT, UP, DOWN order.
        If the current node is standing on a portal entrance,
        the only next move is forced teleport to its exit with cost 0.
        """
        current_state = node.state

        # forced teleport
        if self.is_portal_entrance(current_state):
            exit_state = self.portal_map[current_state]
            return [Node(exit_state, parent=node, g=node.g)]

        x, y = current_state
        directions = [
            (-1, 0),  # LEFT
            (1, 0),  # RIGHT
            (0, -1),  # UP
            (0, 1)  # DOWN
        ]

        children = []

        for dx, dy in directions:
            nx, ny = x + dx, y + dy

            if not self.in_bounds(nx, ny):
                continue

            next_state = (nx, ny)
            next_tile = self.get_tile(next_state)

            if self.is_wall(next_tile):
                continue

            new_cost = node.g + self.move_cost(next_tile)
            child = Node(next_state, parent=node, g=new_cost)
            children.append(child)

        return children
