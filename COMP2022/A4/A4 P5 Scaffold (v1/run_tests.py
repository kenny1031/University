#Testing script
#Assumes minisat installed (try: apt-get install -y minisat)
#Assumes a4p5.py (in the same directory)
#Assumes ../results exists (ie. create a results directory one level up from this file)

#Output is written to ../results/results.json, check it out

#You can modify this file if you want, eg. to add more tests

from a4p5 import instance_to_formula, assignment_to_solution, solution_to_assignment
from objects5 import *
import json
import subprocess

class FormatError(Exception):
    pass

def assert_format(b,s):
    if not b:
        raise FormatError(s)

def check_cnf(form):
    if type(form) != Conjunction:
        return False
    for i in form.forms:
        if not check_clause(i):
            return False
    return True

def check_clause(form):
    if type(form) != Disjunction:
        return False
    for i in form.forms:
        if not check_literal(i):
            return False
    return True

def check_literal(form):
    if type(form) == Atom:
        return True
    if type(form) == Negation:
        if type(form.form == Atom):
            return True
    return False

def run(instance, expect_sat, example_soln):
    satpassed = False
    a2spassed = False
    s2apassed = False
    form = instance_to_formula(instance)
    assert_format(isinstance(form,Formula),"Function instance_to_formula must return a Formula object")
    assert_format(check_cnf(form), "Function instance_to_formula must return a CNF formula")

    a = list(form.atoms_used())
    a.sort()
    d = {}
    for i in range(len(a)):
        d[a[i]] = i+1
    f = open("formula.txt","w")
    f.write(f"p cnf {len(a)} {len(form.forms)}\n")
    for i in form.forms:
        f.write(" ".join(map(lambda x: str(d[x.value]) if type(x) == Atom else '-'+str(d[x.form.value]), i.forms)))
        f.write(" 0\n")
    f.close()
    #print(form)
    s = subprocess.run(["minisat","formula.txt","assignment.txt"], capture_output=True)
    #Uncomment the following to check the output from minisat
    #print(s.stdout)
    f = open("assignment.txt","r")
    x = f.readline()
    if x == "UNSAT\n":
        sat = False
    elif x == "SAT\n":
        sat = True
    else:
        assert False
    if sat == expect_sat:
        satpassed = True
    else:
        satpassed = False
    if sat and satpassed:
        assignment = f.readline().strip()
        assignment = map(int,filter(lambda x: x[0] != '-', assignment.split(" ")[:-1]))
        assignment = map(lambda x: a[x-1],assignment)
        assignment = Assignment(set(assignment))
        solution = assignment_to_solution(form,assignment)
        assert_format(isinstance(solution,Solution),"Function assignment_to_solution must return a Solution object")
        k = len(instance.r)
        assert_format(len(solution.l) == k, "assignment_to_solution returned a Solution of the wrong length")
        #check solution
        n = instance.n
        matrix = []
        for i in range(n):
            line = [False] * n
            matrix.append(line)
        a2spassed = True
        for i in range(k):
            for j in range(solution.l[i][0], solution.l[i][0] + instance.r[i][0]):
                for k in range(solution.l[i][1], solution.l[i][1] + instance.r[i][1]):
                    if j >= n or k >= n: #cell goes outside grid
                        a2spassed = False
                        continue
                    if matrix[j][k]:
                        a2spassed = False
                    matrix[j][k] = True
    if sat and satpassed:
        assignment = solution_to_assignment(form,example_soln)
        assert_format(isinstance(assignment,Assignment),"Function solution_to_assignment must return an Assignment object")
        answer = form.evaluate(assignment)
        s2apassed = answer

    return (satpassed, a2spassed, s2apassed)

tests = []

#List of test cases (feel free to add more)
cases = [
(Instance(3,[(2,2),(2,1),(1,2)]),True, Solution([(0,0),(0,2),(2,0)])),
(Instance(3,[(2,2),(2,2),(1,1)]),False, None),
(Instance(5,[(3,2),(3,2),(2,3),(2,3)]),True, Solution([(0,0),(2,3),(0,2),(3,0)])),
(Instance(5,[(3,3),(3,3)]),False, None),
]

for i in range(len(cases)):
    case = cases[i]

    errored = False
    try:
        satpassed, a2spassed, s2apassed = run(case[0], case[1], case[2])
    except Exception as e:
        errored = True
        error = e

    if errored:
        publictest = {}
        publictest["number"] = f"Error in submission on test {i}"
        publictest["visibility"] = "visible"
        publictest["score"] = 0
        publictest["maxscore"] = 0.001
        publictest["output"] = "The following error occured on the public test:\n"
        for e in error.args:
            publictest["output"] += str(e)
    else:
        correct = satpassed and (not case[1] or (a2spassed and s2apassed))
    
        publictest = {}
        publictest["number"] = f"Public test {i}"
        publictest["visibility"] = "visible"
        publictest["score"] = 0.001 if correct else 0
        publictest["maxscore"] = 0.001
        publictest["output"] = "Your code ran without error.\n"
        if satpassed:
            publictest["output"] += f"You correctly output a {'un' if not case[1] else ''}satisfiable formula.\n"
        else:
            publictest["output"] += f"However, you incorrectly claimed the formula was {'un' if case[1] else ''}satisfiable.\n"
        if satpassed and case[1]:
            if a2spassed:
                publictest["output"] += f"You correctly converted a satisfying assignment into a solution.\n"
            else:
                publictest["output"] += f"However, when given a satisfying assignment you gave an invalid solution.\n"
            if s2apassed:
                publictest["output"] += f"You correctly converted a solution into a satisfying assignment.\n"
            else:
                publictest["output"] += f"However, when given a solution you gave an unsatisfying assignment.\n"
    print(publictest["number"], publictest["output"])
    tests.append(publictest)

final = {"tests": tests}

f = open("../results/results.json","w")
f.write(json.dumps(final))
f.close()

print("Tester done")
