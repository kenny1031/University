from UnionFind import UnionFind
# Read in the number of vertices (n) and edges (m)
n = int(input())
m = int(input())
mst_weight = 0
forest = UnionFind()

# E is initialised as a `dict` to make the removal of the A-edges efficient.
E = {}
for _ in range(int(m)):
    u,v,w = input().split()
    # We use sets to be invariant to edge order (undirected graph) and frozen-sets so they're hashable.
    E[frozenset((u,v))] = float(w)

n_A = int(input())
A = set()

for _ in range(n_A):
    edge = frozenset(input().split())
    A.add(edge)
    mst_weight += E.pop(edge) # Remove edge from E and add its weight to the MST

for u,v in A:
    forest.union(u,v)

E = sorted(E.items(), key = lambda kv : kv[1])

for (u,v), weight in E:
    if forest[u] != forest[v]:
        forest.union(u,v)
        mst_weight += weight
        A.add(frozenset((u,v))) # A now stores all of our MST edges, not just those that were initialised in A.
    if len(A) == (n - 1):
        break

print('{:.2f}'.format(mst_weight))
