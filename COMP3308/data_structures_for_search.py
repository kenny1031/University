from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Optional, List, Dict

@dataclass
class Node:
    state: str
    parent: Optional['Node'] = None
    action: Optional[Any] = None
    path_cost: float = 0.0
    depth: int = field(init=False)

    def __post_init__(self) -> None:
        self.depth = 0 if self.parent is None else self.parent.depth + 1

    def path(self) -> List[Node]:
        current = self
        path = []
        while current is not None:
            path.append(current)
            current = current.parent
        path.reverse()
        return path

    def solution(self) -> List[Any]:
        return [node.state for node in self.path()]

# =========================
# Queue for BFS,
@dataclass
class Queue:
    data: List[Node] = field(default_factory=list)
    front: int = 0 # Pointer to the index of front item

    def enqueue(self, item: Any) -> None:
        self.data.append(item)

    def dequeue(self) -> Any:
        if self.is_empty():
            raise IndexError("Queue is empty")
        item = self.data[self.front]
        self.front += 1
        return item

    def is_empty(self) -> bool:
        return self.front >= len(self.data)

    def __len__(self) -> int:
        return len(self.data) - self.front

    def contains_state(self, state: Any) -> bool:
        for i in range(self.front, len(self.data)):
            if self.data[i].state == state:
                return True
        return False

# =========================
# Stack for DFS, DLS, IDS
@dataclass
class Stack:
    data: List[Node] = field(default_factory=list)

    def push(self, item: Node) -> None:
        self.data.append(item)

    def pop(self) -> Node:
        if self.is_empty():
            raise IndexError("Stack is empty")
        return self.data.pop()

    def is_empty(self) -> bool:
        return len(self.data) == 0

    def __len__(self) -> int:
        return len(self.data)

    def contains_state(self, state: str) -> bool:
        for i in range(len(self.data)):
            if self.data[i].state == state:
                return True
        return False

# ==============================
# Priority Queue for UCS, Greedy
@dataclass
class HeapItem:
    priority: float
    item: Any

@dataclass
class PriorityQueue:
    heap: List[HeapItem] = field(default_factory=list)

    def is_empty(self) -> bool:
        return len(self.heap) == 0

    def __len__(self) -> int:
        return len(self.heap)

    def enqueue(self, item: Any, priority: float) -> None:
        self.heap.append(HeapItem(priority, item))
        self._sift_up(len(self.heap) - 1)

    def dequeue(self) -> Any:
        if self.is_empty():
            raise IndexError("pop from empty priority queue")

        root_item = self.heap[0].item
        last = self.heap.pop()

        if not self.is_empty():
            self.heap[0] = last
            self._sift_down(0)

        return root_item

    def _sift_up(self, index: int) -> None:
        while index > 0:
            parent = (index - 1) // 2
            if self.heap[index].priority < self.heap[parent].priority:
                self.heap[index], self.heap[parent] = self.heap[parent], self.heap[index]
                index = parent
            else:
                break

    def _sift_down(self, index: int) -> None:
        n = len(self.heap)
        while True:
            left = 2 * index + 1
            right = 2 * index + 2
            smallest = index
            if (left < n and
                self.heap[left].priority < self.heap[smallest].priority):
                smallest = left
            if (right < n and
                self.heap[right].priority < self.heap[smallest].priority):
                smallest = right
            if smallest == index:
                break
            self.heap[index], self.heap[smallest] = (
                self.heap[smallest],
                self.heap[index]
            )
            index = smallest

# ====================================
# Graph for search problem formulation
@dataclass(frozen=True)
class Edge:
    destination: str
    cost: float

@dataclass
class Graph:
    initial_state: str
    goal_states: List[str] # must be given when initialising the graph instance
    adjacency_list: Dict[str, List[Edge]] = field(default_factory=dict)

    def add_vertex(self, vertex: str) -> None:
        if vertex not in self.adjacency_list:
            self.adjacency_list[vertex] = []

    def add_edge(
        self,
        source: str,
        destination: str,
        cost: float
    ) -> None:
        if source not in self.adjacency_list:
            self.adjacency_list[source] = []

        if destination not in self.adjacency_list:
            self.adjacency_list[destination] = []

        self.adjacency_list[source].append(Edge(destination, cost))

    def neighbours(self, vertex: str) -> List[Edge]:
        return self.adjacency_list[vertex]

    def is_goal(self, vertex: str) -> bool:
        return vertex in self.goal_states


def expand(problem: Graph, node: Node) -> List[Node]:
    """Generate all child nodes of a node."""
    children = []
    for edge in problem.neighbours(node.state):
        child = Node(
            state=edge.destination,
            parent=node,
            action=f"{node.state}->{edge.destination}",
            path_cost=node.path_cost + edge.cost,
        )
        children.append(child)
    return children


if __name__ == '__main__':
    pq = PriorityQueue()
    pq.enqueue('A', 2)
    pq.enqueue('B', 3)
    pq.enqueue('C', 4)
    pq.enqueue('D', 5)
    pq.enqueue('E', 7)
    pq.enqueue('F', 6)

    print([pq.dequeue() for _ in range(pq.__len__())])
    # Expect ['A', 'B', 'C', 'D', 'F', 'E']
