import sys

from crossword import *


class CrosswordCreator:
    def __init__(self, crossword):
        """
        Create new CSP crossword generate.
        """
        self.crossword = crossword
        self.domains = {
            var: self.crossword.words.copy() for var in self.crossword.variables
        }

    def letter_grid(self, assignment):
        """
        Return 2D array representing a given assignment.
        """
        letters = [
            [None for _ in range(self.crossword.width)]
            for _ in range(self.crossword.height)
        ]
        for variable, word in assignment.items():
            direction = variable.direction
            for k in range(len(word)):
                i = variable.i + (k if direction == Variable.DOWN else 0)
                j = variable.j + (k if direction == Variable.ACROSS else 0)
                letters[i][j] = word[k]
        return letters

    def print(self, assignment):
        """
        Print crossword assignment to the terminal.
        """
        letters = self.letter_grid(assignment)
        for i in range(self.crossword.height):
            for j in range(self.crossword.width):
                if self.crossword.structure[i][j]:
                    print(letters[i][j] or " ", end="")
                else:
                    print("█", end="")
            print()

    def save(self, assignment, filename):
        """
        Save crossword assignment to an image file.
        """
        from PIL import Image, ImageDraw, ImageFont

        cell_size = 100
        cell_border = 2
        interior_size = cell_size - 2 * cell_border
        letters = self.letter_grid(assignment)

        # Create a blank canvas
        img = Image.new(
            "RGBA",
            (self.crossword.width * cell_size, self.crossword.height * cell_size),
            "black",
        )
        font = ImageFont.truetype("assets/fonts/OpenSans-Regular.ttf", 80)
        draw = ImageDraw.Draw(img)

        for i in range(self.crossword.height):
            for j in range(self.crossword.width):
                rect = [
                    (j * cell_size + cell_border, i * cell_size + cell_border),
                    (
                        (j + 1) * cell_size - cell_border,
                        (i + 1) * cell_size - cell_border,
                    ),
                ]
                if self.crossword.structure[i][j]:
                    draw.rectangle(rect, fill="white")
                    if letters[i][j]:
                        _, _, w, h = draw.textbbox((0, 0), letters[i][j], font=font)
                        draw.text(
                            (
                                rect[0][0] + ((interior_size - w) / 2),
                                rect[0][1] + ((interior_size - h) / 2) - 10,
                            ),
                            letters[i][j],
                            fill="black",
                            font=font,
                        )

        img.save(filename)

    def solve(self):
        """
        Enforce node and arc consistency, and then solve the CSP.
        """
        self.enforce_node_consistency()
        self.ac3()
        return self.backtrack(dict())

    def enforce_node_consistency(self):
        """
        Update `self.domains` such that each variable is node-consistent.
        (Remove any values that are inconsistent with a variable's unary
         constraints; in this case, the length of the word.)
        """
        # new_domains = {}
        # for variable in self.crossword.variables:
        #     # Apply unary constraint, length of word must make length of variables
        #     #make a new cosntruct that contains words of the apprpriate length
        #     new_domains[variable] = set(word for word in self.crossword.words if len(word) == variable.length)
        # #Update the domains in puzzle
        # self.domains = new_domains

        for var in self.domains:
            # We will collect words to remove (not consistent with the variable's constraints)
            words_to_remove = set()
            for word in self.domains[var]:
                if len(word) != var.length:  # The word length does not fit the space.
                    words_to_remove.add(word)

            # Now, remove the inconsistent words from the domain of the variable.
            for word in words_to_remove:
                self.domains[var].remove(word)

        """for var in self.domains:
            for word in set(self.domains[var]):  # Use copy to ensure there is each variable is node-consistent
                if len(word) != var.length:
                    self.domains[var].remove(word)"""

    def revise(self, x, y):
        """
        Make variable `x` arc consistent with variable `y`.
        To do so, remove values from `self.domains[x]` for which there is no
        possible corresponding value for `y` in `self.domains[y]`.

        Return True if a revision was made to the domain of `x`; return
        False if no revision was made."""
        revised = False
        overlap = self.crossword.overlaps[x, y]
        if not overlap:
            return revised

        to_remove = set()
        for x_word in self.domains[x]:
            # check if there is a word in domain[y] that revises the overlap
            valid_overlap = False
            for y_word in self.domains[y]:
                if x_word[overlap[0]] == y_word[overlap[1]]:
                    valid_overlap = True
                    break
            if not valid_overlap:
                to_remove.add(x_word)
                revised = True

        self.domains[x] -= to_remove
        return revised

        raise NotImplementedError

    def ac3(self, arcs=None):
        """
        Update `self.domains` such that each variable is arc consistent.
        If `arcs` is None, begin with initial list of all arcs in the problem.
        Otherwise, use `arcs` as the initial list of arcs to make consistent.

        Return True if arc consistency is enforced and no domains are empty;
        return False if one or more domains end up empty.
        """
        if arcs is None:
            arcs = [
                (x, y)
                for x in self.crossword.variables
                for y in self.crossword.neighbors(x)
            ]

        while arcs:
            x, y = arcs.pop()
            if self.revise(x, y):  # If a revision was made
                if not self.domains[x]:  # If domain of x is empty
                    return False
                for neighbor in self.crossword.neighbors(x) - {
                    y
                }:  # Add neighbors of x to the arc queue
                    arcs.append((neighbor, x))

        return True  # If all arcs are processed and no domain is empty

    def assignment_complete(self, assignment):
        """
        Return True if `assignment` is complete (i.e., assigns a value to each
        crossword variable); return False otherwise.
        """
        for variable in self.crossword.variables:
            if variable not in assignment or assignment[variable] is None:
                return False
        return True

    def consistent(self, assignment):
        """
        Return True if the current assignment is consistent.
        """

        # Check if the word is distinct and not already assigned
        for variable, word in assignment.items():
            # All the variables have a length, if there are 5 letters, the slot should also have 5 letters.
            # Check word length matches the variable's length
            if variable.length != len(word):
                return False

            # Check for conflicts in binary constraints
            for neighbor in self.crossword.neighbors(variable):
                overlap = self.crossword.overlaps[variable, neighbor]

                # If overlap exists between var and neighbor
                if overlap:
                    x, y = overlap
                    # If neighbor has a value assigned, check for consistency
                    if neighbor in assignment:
                        if word[x] != assignment[neighbor][y]:
                            return False

                    # Do I need all chosen words to be unique? Test for Uniqueness~~~

        # If all checks pass, the assignment is consistent
        return True

    def order_domain_values(self, var, assignment):
        """
        Return a list of values in the domain of `var`, in order by
        the number of values they rule out for neighboring variables.
        The first value in the list, for example, should be the one
        that rules out the fewest values among the neighbors of `var`.
        """
        count_eliminations = {}

        # Go through each value in the variable's domain
        for value in self.domains[var]:
            count_eliminations[value] = 0

            # Consider each neighbor of the variable
            for neighbor in self.crossword.neighbors(var):
                if neighbor not in assignment:
                    # For each neighboring variable, count how many choices are eliminated by assigning value to var
                    for neighbor_value in self.domains[neighbor]:
                        overlap = self.crossword.overlaps[var, neighbor]
                        if overlap and value[overlap[0]] != neighbor_value[overlap[1]]:
                            # If there's a conflict, this choice of value would eliminate neighbor_value for neighbor
                            count_eliminations[value] += 1

        # Sort by values that rule out the fewest choices for neighbors
        ordered_values = sorted(
            self.domains[var], key=lambda val: count_eliminations[val]
        )

        return ordered_values

    def select_unassigned_variable(self, assignment):
        """
        Return an unassigned variable not already part of `assignment`.
        Choose the variable with the minimum number of remaining values
        in its domain. If there is a tie, choose the variable with the highest
        degree. If there is a tie, any of the tied variables are acceptable
        return values.
        """
        unassigned_variables = [
            v for v in self.crossword.variables if v not in assignment
        ]

        # If there's no unassigned variables, we're done.
        if not unassigned_variables:
            return None

        # Minimum Remaining Value (MRV) heuristic.
        mrv_dict = {var: len(self.domains[var]) for var in unassigned_variables}

        # Identify variables with the minimum remaining values
        min_remaining_values = min(mrv_dict.values())
        mrv_variables = [
            var for var, count in mrv_dict.items() if count == min_remaining_values
        ]

        if len(mrv_variables) == 1:
            return mrv_variables[0]

        degree_dict = {var: len(self.crossword.neighbors(var)) for var in mrv_variables}

        max_degree_var = max(degree_dict, key=degree_dict.get)
        return max_degree_var

    def backtrack(self, assignment):
        """
        Using Backtracking Search, take as input a partial assignment for the
        crossword and return a complete assignment if possible to do so.

        `assignment` is a mapping from variables (keys) to words (values).

        If no assignment is possible, return None.
        """
        # IF all variables are assigned, check the assigned value is complete and consistent
        if len(assignment) == len(self.crossword.variables):
            return (assignment) if self.consistent(assignment) else None

        var = self.select_unassigned_variable(assignment)

        # Try every value that is in the variables domain

        for value in self.order_domain_values(var, assignment):
            # Create Temporary assignemnt to test consistency

            if self.consistent(assignment):
                assignment[var] = value

                result = self.backtrack(assignment)

                if result is not None:
                    return result

                del assignment[var]

        return None


# Try doing the problems from class because this is not working no matter what you do...


def main():
    # Check usage
    if len(sys.argv) not in [3, 4]:
        sys.exit("Usage: python generate.py structure words [output]")

    # Parse command-line arguments
    structure = sys.argv[1]
    words = sys.argv[2]
    output = sys.argv[3] if len(sys.argv) == 4 else None

    # Generate crossword
    crossword = Crossword(structure, words)
    creator = CrosswordCreator(crossword)
    assignment = creator.solve()

    # Print result
    if assignment is None:
        print("No solution.")
    else:
        creator.print(assignment)
        if output:
            creator.save(assignment, output)


if __name__ == "__main__":
    main()
