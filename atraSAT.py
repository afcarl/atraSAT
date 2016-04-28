#!/usr/bin/python

#######################################################################
# Copyright 2015 Marc Sanchez, Meritxell Jordana, Eduard Arnedo

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#######################################################################

import sys
import copy

class DPLLProblem:

    tautology = "Tautology"

    def __init__(self, DPLLProblem=None):
        if DPLLProblem:
            self.clauses = copy.deepcopy(DPLLProblem.clauses)
            self.number_of_vars = DPLLProblem.number_of_vars
            self.unit_clauses = DPLLProblem.unit_clauses.copy()
            self.interpretation = Interpretation(DPLLProblem.interpretation)
            self.original_clauses = DPLLProblem.original_clauses
        else:
            self.clauses = {}
            self.number_of_vars = 0
            self.unit_clauses = set()
            self.original_clauses = set()

    def read(self, cnf_file):
        f = open(cnf_file, "r")
        for line in f:
            l = line.split()
            if len(l) != 0 and l[0] != 'c':
                if l[0] == 'p':
                    self.number_of_vars = int(l[2])
                else:
                    clause = set()
                    for elem in[int(lit) for lit in l[:-1]]:
                        literal = None
                        if elem > 0:
                            literal = (elem, True)
                        else:
                            literal = (abs(elem), False)
                        clause.add(literal)
                    if not DPLLProblem.clause_is_tautologic(clause):
                        self.original_clauses.add(tuple(clause))
        f.close()
        for clause in self.original_clauses:
            self.add_clause(clause)
        self.interpretation = Interpretation(self.number_of_vars)

    def add_clause(self, clause):
        for literal in clause:
            if literal not in self.clauses:
                self.clauses[literal] = set()
            self.clauses[literal].add(tuple(clause))
        if len(clause) == 1:
            self.unit_clauses.add(tuple(clause))

    def remove_clause(self, clause):
        for literal in clause:
            if literal in self.clauses:
                self.clauses[literal].remove(clause)
                if len(self.clauses[literal]) == 0:
                    del self.clauses[literal]
        if len(clause) == 1:
            self.unit_clauses.remove(clause)

    def remove_all_clauses_containing_var(self, var):
        self.remove_all_clauses_containing_lit((var, True))
        self.remove_all_clauses_containing_lit((var, False))

    def remove_all_clauses_containing_lit(self, lit):
        if lit in self.clauses:
            for clause in self.clauses[lit].copy():
                self.remove_clause(clause)

    def remove_literal_from_clauses(self, lit):
        if lit in self.clauses:
            for clause in self.clauses[lit].copy():
                new_clause = set(clause)
                new_clause.remove(lit)
                if len(new_clause) == 0:
                    return "s UNSATISFIABLE"
                self.remove_clause(clause)
                self.add_clause(new_clause)

    @staticmethod
    def clause_is_tautologic(clause_set):
        for literal in clause_set:
            if (literal[0], not literal[1]) in clause_set:
                return True
        return False

    def pure_literal(self):
        for literal in self.clauses.keys():
            if literal in self.clauses and \
                        (literal[0], not literal[1]) not in self.clauses:
                self.interpretation.set_variable(literal[0], literal[1])
                self.remove_all_clauses_containing_lit(literal)


    def unit_propagation(self):
        for clause in self.unit_clauses.copy():
            literal = list(clause)[0]
            self.interpretation.set_variable(literal[0], literal[1])
            self.remove_all_clauses_containing_lit(literal)
            if self.remove_literal_from_clauses((literal[0], not literal[1])):
                return "s UNSATISFIABLE"

    @staticmethod
    def get_resolvent_clause(c1, c2, var):
        clause = set()
        for literal in c1 + c2:
            clause.add(literal)
        if (var, False) in clause:
            clause.remove((var, False))
        if (var, True) in clause:
            clause.remove((var, True))
        if DPLLProblem.clause_is_tautologic(clause):
            return DavisPutnamProblem.tautology
        return tuple(clause)

    def formula_is_satisfied(self):
        for clause in self.original_clauses:
            if not self.clause_is_satisfied(clause):
                return False
        return True

    def clause_is_satisfied(self, clause):
        for literal in clause:
            if literal[1] == self.interpretation.values[literal[0]]:
                return True
        return False

class DavisPutnamProblem:

    @staticmethod
    def solve_problem(problem):
        problem.pure_literal()
        if problem.unit_propagation():
            return None
        if len(problem.clauses) == 0:
            if problem.formula_is_satisfied():
                return problem.interpretation
            else:
                return None
        literal = DavisPutnamProblem.choose_literal(problem)
        problem_left = DPLLProblem(problem)
        problem_right = DPLLProblem(problem)
        problem_left.add_clause(((literal),))
        problem_right.add_clause(((literal[0], not literal[1]),))
        return DavisPutnamProblem.solve_problem(problem_left) or \
                DavisPutnamProblem.solve_problem(problem_right)

    @staticmethod
    def choose_literal(problem):
        max = (None, 0)
        for literal, clauses in problem.clauses.items():
            if len(clauses) > max[1]:
                max = (literal, len(clauses))
        return max[0]

class Interpretation:

    def __init__(self, nvars):
        if isinstance(nvars, Interpretation):
            self.values = nvars.values[:]
            self.nvars = nvars.nvars
        else:
            self.values = ["UNUSED"]
            self.nvars = nvars
            for i in xrange(nvars):
                self.values.append(True)

    def show(self):
        sys.stdout.write("v")
        for i in xrange(1, len(self.values)):
            if self.values[i]:
                sys.stdout.write(" %i" % i)
            else:
                sys.stdout.write(" %i" % -i)
        sys.stdout.write(" 0\n")

    def set_variable(self, var, value):
        self.values[var] = value

if __name__ == '__main__':
    if (len(sys.argv) != 2):
        print "Use:", sys.argv[0], "<sat_problem.cnf>"
        sys.exit(1)
    davis_problem = DPLLProblem()
    davis_problem.read(sys.argv[1])
    sys.setrecursionlimit(2500)
    solution = DavisPutnamProblem.solve_problem(davis_problem)
    print "c AtraSAT Solver"
    if solution:
        print "s SATISFIABLE"
        solution.show()
    else:
        print "s UNSATISFIABLE"
