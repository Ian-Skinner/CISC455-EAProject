import tkinter as tk
import random
from fire import Fire

class TreeGrid:
    EMPTY = 0
    TREE = 1
    BURNING = 2
    BURNT = 3

    def __init__(self, size, genome=None):
        self.height = size
        self.width = size
        self.size = size

        # Use a flat genome where 0 = empty, 1 = tree
        # Burning not part of genome as EA does not care about burning state
        if genome is None:
            self.genome = [self.EMPTY] * (self.width * self.size)
        else:
            self.setGenome(genome)

        self.grid = self.decode(self.genome)


    # map a row and column to a flat index
    def idx(self, r, c):
        return r * self.size + c

    # map a flat index to a row and column
    def rc(self, i):
        return divmod(i, self.size)


    def setGenome(self, genome):
        genome = list(genome)
        self.genome = genome


    # decode the flat genome into a 2D grid
    def decode(self, genome):
        grid = [[self.EMPTY for _ in range(self.width)] for _ in range(self.height)]
        for i, gene in enumerate(genome):
            row, col = self.rc(i)
            grid[row][col] = gene
        return grid

    # encode the 2D grid into a flat genome
    def encode(self, grid=None):
        if grid is None:
            grid = self.grid
        genome = [self.EMPTY] * (self.width * self.height)
        for row in range(self.height):
            for col in range(self.width):
                v = grid[row][col]
                genome[self.idx(row, col)] = self.TREE if v == self.TREE else self.EMPTY
        return genome
    
    # Resets the grid 
    def applyGenome(self, genome):
        self.setGenome(genome)
        self.grid = self.decode(genome)

    def printGrid(self):
        for row in self.grid:
            print(' '.join(str(cell) for cell in row))



def Crossover(parent1, parent2):

    num_trees = parent1.genome.count(1)

    child1 = TreeGrid(parent1.size)
    child2 = TreeGrid(parent2.size)

    child1.genome = parent1.genome.copy()
    child2.genome = parent2.genome.copy()

    row1 = random.randint(0, parent1.size - 1)
    row2 = random.randint(0, parent1.size - 1)
    col1 = random.randint(0, parent1.size - 1)
    col2 = random.randint(0, parent1.size - 1)

    for i in range(min(row1, row2),max(row1, row2)):
        for j in range(min(col1,col2) ,max(col1,col2)):
            temp = child1.genome[child1.idx(i,j)]
            child1.genome[child1.idx(i,j)] = child2.genome[child2.idx(i,j)]
            child2.genome[child2.idx(i,j)] = temp

    for c in [child1, child2]:

        current_trees = c.genome.count(1)

        while current_trees < num_trees:
            c.genome[random.randint(0, len(c.genome) - 1)] = 1

        while current_trees > num_trees:
            c.genome[random.randint(0, len(c.genome) - 1)] = 0

    

    

    


    





class GridVisualizer:

    COLORS = {
        TreeGrid.EMPTY: "#9e9e9e",
        TreeGrid.TREE: "#2e7d32",
        TreeGrid.BURNING: "#fb8c00"
    }

    def __init__(self, tree_grid: TreeGrid, cell_size: int = 28, title: str = "Tree Grid", master=None):
        self.tree_grid = tree_grid
        self.cell_size = cell_size

        self.root = tk.Tk() if master is None else tk.Toplevel(master)
        self.root.title(title)

        w = tree_grid.width * cell_size
        h = tree_grid.height * cell_size

        self.canvas = tk.Canvas(self.root, width=w, height=h, highlightthickness=0)
        self.canvas.pack()

        # Keep rectangle ids so redraw is fast
        self._rects = [[None for _ in range(tree_grid.width)] for _ in range(tree_grid.height)]
        self._build()
        self.render()

    def _build(self):
        cs = self.cell_size
        for r in range(self.tree_grid.height):
            for c in range(self.tree_grid.width):
                x1, y1 = c * cs, r * cs
                x2, y2 = x1 + cs, y1 + cs
                rect_id = self.canvas.create_rectangle(
                    x1, y1, x2, y2,
                    outline="#616161",
                    width=1
                )
                self._rects[r][c] = rect_id

    def render(self):
        for r in range(self.tree_grid.height):
            for c in range(self.tree_grid.width):
                v = self.tree_grid.grid[r][c]
                color = self.COLORS.get(v, "#000000")
                self.canvas.itemconfig(self._rects[r][c], fill=color)

    def mainloop(self):
        self.root.mainloop()


class Placement:
    """
    Represents a candidate tree arrangement for the evolutionary algorithm.

    Stores a grid as a flat binary genome (0 = empty, 1 = tree) and provides
    utilities to generate, copy, and convert it into a TreeGrid for simulation.

    Used as the individual in the population, modified by mutation/crossover,
    and evaluated based on fire spread.
    """
    def __init__(self, size, num_trees=None):
        self.size = size
        self.genome_length = size * size
        self.num_trees = num_trees

    def random_genome(self):
        if self.num_trees is None:
            return [random.randint(0, 1) for _ in range(self.genome_length)]
        
        genome = [0] * self.genome_length
        tree_positions = random.sample(range(self.genome_length), self.num_trees)
        
        for pos in tree_positions:
            genome[pos] = 1
        
        return genome

    def generate_population(self, pop_size):
        return [self.random_genome() for _ in range(pop_size)]

    def repair(self, genome):
        if self.num_trees is None:
            return genome

        genome = list(genome)
        current_trees = sum(genome)

        if current_trees > self.num_trees:
            tree_indices = [i for i, g in enumerate(genome) if g == 1]
            remove = random.sample(tree_indices, current_trees - self.num_trees)
            for i in remove:
                genome[i] = 0

        elif current_trees < self.num_trees:
            empty_indices = [i for i, g in enumerate(genome) if g == 0]
            add = random.sample(empty_indices, self.num_trees - current_trees)
            for i in add:
                genome[i] = 1

        return genome


# Fitness val. is an avg of surviving trees over multiple fire simulations (currently 10)

def evaluate_fitness(genome, size, num_runs=100):
    
    # counter of all trees survived (accumulates over runs, doesn't reset)
    total_surviving = 0

    for _ in range(num_runs):
        grid = TreeGrid(size=size, genome=genome[:])  # copy the genome so original is untouched

        # Find initial fire spot
        fire = Fire(grid)
        while not fire.isValid:
            fire = Fire(grid)

        fires = [fire]

        # Run fire simulation
        while fires:
            new_fires = []

            for f in fires:
                alive = f.update()

                # if tree still burning, add to new_fires
                if alive[0]:
                    new_fires.append(f)

                # locate all newly burning tiles, add to new_fires
                new_fires.extend(x for x in alive[1] if x.isValid)

            # replace fire list with updated one. old burnt-out fires/tiles are shuffled out    
            fires = new_fires

        # count how many ints in the genome are still trees (1) and add them to the accumulator
        total_surviving += grid.genome.count(1)

    return total_surviving / num_runs



def mutate(genome, stepSize):
    # Flip 0 (empty) to 1 (tree) and 1 (tree) to 0 (empty) depending on mutation step size
    # stepSize is the probability of mutation for each gene, between 0 and 1

    return [1 - cell if random.random() < stepSize else cell for cell in genome]

def evolutionaryLoop(parentGenome, currentFitness, iterations):
    genome = parentGenome
    stepSize = 0.05 # initial value for first mutation

    successCount = 0
    trialCount = 0

    for i in range(iterations):
        #Mutate
        mutatedGenome = mutate(genome, stepSize)
        mutatedGenomeFitness = evaluate_fitness(mutatedGenome, GRID_SIZE)

        # Check success of mutation
        if mutatedGenomeFitness > currentFitness:
            successCount += 1
            genome = mutatedGenome
            currentFitness = mutatedGenomeFitness

        trialCount += 1

        # Apply 1/5 success rule to adjust mutation step size every WINDOW_SIZE iterations
        if trialCount == WINDOW_SIZE:
            successRate = successCount / trialCount

            if successRate > TARGET_SUCCESS_RATE:
                stepSize *= ADJUSTMENT_FACTOR
            elif successRate < TARGET_SUCCESS_RATE:
                stepSize /= ADJUSTMENT_FACTOR

            stepSize = max(0.001, min(0.5, stepSize))

            successCount = 0
            trialCount = 0

    return genome, currentFitness

"""
SET INITIAL PARAMETERS
"""
GRID_SIZE = 20 # size of the grid (square grid, so this is both width and height)
NUM_TREES = 200 # number of trees to place in the grid.

"""
GENERATE INITIAL RANDOM GENOME
"""
placement = Placement(size=GRID_SIZE, num_trees=NUM_TREES)
genome = placement.random_genome()

InitialGenome = TreeGrid(size=GRID_SIZE, genome=genome)
viewerInitial = GridVisualizer(InitialGenome, cell_size=20, title="Initial Tree Arrangement")

"""
EVALUATE FITNESS OF INITIAL GENOME
"""
fitnessValue = evaluate_fitness(genome, GRID_SIZE)
print("Fitness value for initial genome is: ", fitnessValue)


"""
MUTATE THE GENOME
using 1/5 success rule for variable mutation step size
"""
TARGET_SUCCESS_RATE = 0.2
ADJUSTMENT_FACTOR = 1.5
WINDOW_SIZE = 20 
mutatedGenome, newFitness = evolutionaryLoop(genome, fitnessValue, iterations=1000)

print("Fitness value for mutated genome is: ", newFitness)

FinalGenome = TreeGrid(size=GRID_SIZE, genome=mutatedGenome)
viewerFinal = GridVisualizer(FinalGenome, cell_size=20, title="Final Tree Arrangement", master=viewerInitial.root)

viewerInitial.mainloop()



# ignite one random tree
first_fire = Fire(InitialGenome)
second_fire = Fire(InitialGenome)
fires = []
fires.append(first_fire)
fires.append(second_fire)

for i in range(len(fires)):
    while True:
        try:
            fires[i].burnProb
        except:
            fires[i] = Fire(InitialGenome)
        else:
            break

def tick():
    # print("tick")
    global fires

    new_fires = []
    for f in fires:
        # print(f)
        alive = f.update()
        if alive[0]:
            new_fires.append(f)
        new_fires.extend(x for x in alive[1] if x.isValid)


    fires = new_fires

    InitialGenome.grid = InitialGenome.decode(InitialGenome.genome)
    viewerInitial.render()

    if fires:
        viewerInitial.root.after(200, tick)
    else:
        print("Simulation complete.")

# viewerInitial.root.after(200, tick)
# viewerInitial.mainloop()
