from objects5 import *

#Modify the functions instance_to_formula, assignment_to_solution, solution_to_assignment! Do not change the function names or arguments.
#You may construct additional functions as desired.
#See objects5.py to learn what the objects contain and how to use and construct them.

def instance_to_formula(instance: Instance):
    #input: Instance object
    #output: Formula object; must be in strict CNF: a Conjunction of Disjunctions of literals: Atom or Negation(Atom)
    n = instance.n
    rectangles = instance.r
    clauses = []
    
    # If each rectangles can fit in the square
    for i, (width, height) in enumerate(rectangles):
        temp_clauses = []
        for x in range(n - width + 1):
            for y in range(n - height + 1):
                temp_clauses.append(Atom(f"R{i}_:_{x}_{y}"))
        if temp_clauses:
            clauses.append(Disjunction(temp_clauses))
    
    # If there is no overlap between rectangles
    for i, (w1, h1) in enumerate(rectangles):
        for x1 in range(n - w1 + 1):
            for y1 in range(n - h1 + 1):
                for j in range(i + 1, len(rectangles)):
                    w2, h2 = rectangles[j]
                    for x2 in range(n - w2 + 1):
                        for y2 in range(n - h2 + 1):
                            if (x1 < (x2 + w2) and (x1 + w1) > x2 and y1 < (y2 + h2) and (y1 + h1) > y2):
                                clause = Disjunction([
                                    Negation(Atom(f"R{i}_:_{x1}_{y1}")),
                                    Negation(Atom(f"R{j}_:_{x2}_{y2}"))
                                ])
                                clauses.append(clause)
    formula = Conjunction(clauses)
    return formula
    


def assignment_to_solution(formula, assignment):
    #input: Formula object, Assignment object
    #The input Formula is returned from a previous call to instance_to_formula
    #output: Solution object
    positions = []
    for var in assignment.s:
        if var.startswith("R"):
            parts = var.split("_:_")
            rect_index = int(parts[0][1:])
            x, y = map(int, parts[1].split("_"))
            while len(positions) <= rect_index:
                positions.append(None)
            positions[rect_index] = (x, y)
    
    positions = [pos for pos in positions if pos != None]
    
    return Solution(positions)




def solution_to_assignment(formula, solution):
    #input: Formula object, Solution object
    #The input Formula is returned from a previous call to instance_to_formula
    #output: Assignment object
    assigned_true_vars = set()
    for rect_index, (x, y) in enumerate(solution.l):
        assigned_true_vars.add(f"R{rect_index}_:_{x}_{y}")
    return Assignment(assigned_true_vars)






#See run_tests.py for how to test your code locally
