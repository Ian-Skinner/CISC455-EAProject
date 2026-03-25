import random


class Fire:

    def __init__(self, treeGrid, burnProb = 0.75, jumpProb = 0.9, jump2Prob = 0.8, x = None, y= None):

        # initializes a fire. A "fire" object is called on a singular tile.
        # burnProb is the probability the fire continues to burn each frame.
        # jumpProb is the probability (originally 90%) that a fire will jump a singular tile each frame.
        # jump2Prob is this value ^ but two tiles in any direciton (originally 23%) each frame.
        # x and y are the coordinates of the fire.

        

        if x is None:
            self.x = random.randint(0,treeGrid.size-1)
        else:
            self.x = x

        if y is None:
            self.y = random.randint(0,treeGrid.size-1)
        else: 
            self.y = y


        if not (0 <= self.x < treeGrid.size and 0 <= self.y < treeGrid.size):
            self.isValid = False
            return

        if treeGrid.genome[treeGrid.idx(self.x, self.y)] != 1:
            self.isValid = False
            return 
        
       
            

        self.treeGrid = treeGrid

        self.burnProb = burnProb
        self.jumpProb = jumpProb
        self.jump2Prob = jump2Prob


        treeGrid.genome[treeGrid.idx(self.x, self.y)] = 2  # burning
        self.isValid = True


    def update(self):
        # Returns False if this object should be removed from the working registry

        burnCheck = random.random()

        jumpChecks = [0,0,0,0]
        jump2Check = random.random()

        jumpChecks[0] = random.random()
        jumpChecks[1] = random.random()
        jumpChecks[2] = random.random()
        jumpChecks[3] = random.random()

        newFires = []

        c = random.randint(1,4)
        for j in jumpChecks:
            if j < self.jumpProb:
                match c:
                    case 1:
                        newFires.append(Fire(self.treeGrid, x = self.x + 1, y = self.y))
                    case 2:
                        newFires.append(Fire(self.treeGrid, x = self.x - 1, y = self.y))
                    case 3:
                        newFires.append(Fire(self.treeGrid, x = self.x, y = self.y + 1))
                    case 4:
                        newFires.append(Fire(self.treeGrid, x = self.x, y = self.y - 1))

                c += 1

                if c == 5:
                    c = 1


        c = random.randint(1,4)
        if jump2Check < self.jump2Prob:
            dir1 = random.choice([-1,1])
            dir2 = random.choice([-1,1])
            newFires.append(Fire(self.treeGrid, x = self.x + dir1, y = self.y + dir2))


        if burnCheck > self.burnProb:
            self.treeGrid.genome[self.treeGrid.idx(self.x, self.y)] = 3  # burnt 
            return (False, newFires)
        return (True, newFires)

        




