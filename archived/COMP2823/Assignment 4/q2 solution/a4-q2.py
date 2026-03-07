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
    a = frozenset(input().split())
    A.add(a)
    # Remove a from E and add its weight to the MST.
    mst_weight += E.pop(a)
	
for u,v in A:
    forest.union(u,v)

n_B = int(input())
B = {input() for _ in range(n_B)}
B_first_seen = B.copy() # We create a destructible copy of B to keep track of when we see some b in B.

# We want to find the edge of smallest weight for all b in B connecting to some e in E\B.
E = sorted(E.items(), key = lambda kv : kv[1])

for (u, v), weight in E:
    if (u in B) or (v in B):
        if u in B and v in B: continue #If it's an edge (b,b') where b, b' in B
        elif u in B_first_seen:
            B_first_seen.remove(u)
            mst_weight += weight
            A.add(frozenset((u,v)))
        elif v in B_first_seen:
            B_first_seen.remove(v)
            mst_weight += weight
            A.add(frozenset((u,v)))
    elif forest[u] != forest[v]:
        forest.union(u,v)
        mst_weight += weight
        A.add(frozenset((u,v))) # A now stores all of our MST edges, not just those that were initialised in A.
    if len(A) == (n - 1):
        break
		
print('{:.2f}'.format(mst_weight))
