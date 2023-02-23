import numpy as np
from typing import List
from collections import deque

class Calculation:
    def __init__(self):
        pass

    #calculate the each volumn
    def calculate(self):
        # how to interpolate?
        for idx1, e1 in enumerate(self.save_croped):
            outside_result=self.calculate_layer(np.array(e1).tolist())
            inside_result=e1.shape[0]*e1.shape[1]-outside_result
            all1s = np.count_nonzero(e1==1)
            white_space=e1.shape[0]*e1.shape[1]-all1s
            black_space=inside_result-white_space
            slicenum=self.crop_image[idx1][1]
            self.dic_crop[slicenum]=(inside_result, black_space)
        white_volume=self.dic_crop.copy()
        white_volume[self.white_start[0][1]]=(0, 0)
        white_volume[self.white_end[0][1]]=(0, 0)
        black_volume=self.dic_crop.copy()
        black_volume[self.black_start[0][1]]=(0, 0)
        black_volume[self.black_end[0][1]]=(0, 0)
        # print(white_volume, black_volume)
        self.calculate_done(white_volume, black_volume)

    def calculate_layer(self, grid: List[List[int]]) -> int:
        m = len(grid)
        n = len(grid[0])

        # creating a queue that will help in bfs traversal
        q = deque()
        area = 0
        ans = 0
        for i in range(m):
            for j in range(n):
                # if the value at any particular cell is 1 then
                # from here we need to do the BFS traversal
                if grid[i][j] == 1:
                    ans = 0
                    # pushing the pair(i,j) in the queue
                    q.append((i, j))
                    # marking the value 1 to -1 so that we
                    # don't again push this cell in the queue
                    grid[i][j] = -1
                    while len(q) > 0:
                        t = q.popleft()
                        ans += 1
                        x, y = t[0], t[1]
                        # now we will check in all 8 directions
                        if x + 1 < m:
                            if grid[x + 1][y] == 1:
                                q.append((x + 1, y))
                                grid[x + 1][y] = -1
                        if x - 1 >= 0:
                            if grid[x - 1][y] == 1:
                                q.append((x - 1, y))
                                grid[x - 1][y] = -1
                        if y + 1 < n:
                            if grid[x][y + 1] == 1:
                                q.append((x, y + 1))
                                grid[x][y + 1] = -1
                        if y - 1 >= 0:
                            if grid[x][y - 1] == 1:
                                q.append((x, y - 1))
                                grid[x][y - 1] = -1
                        if x + 1 < m and y + 1 < n:
                            if grid[x + 1][y + 1] == 1:
                                q.append((x + 1, y + 1))
                                grid[x + 1][y + 1] = -1
                        if x - 1 >= 0 and y + 1 < n:
                            if grid[x - 1][y + 1] == 1:
                                q.append((x - 1, y + 1))
                                grid[x - 1][y + 1] = -1
                        if x - 1 >= 0 and y - 1 >= 0:
                            if grid[x - 1][y - 1] == 1:
                                q.append((x - 1, y - 1))
                                grid[x - 1][y - 1] = -1
                        if x + 1 < m and y - 1 >= 0:
                            if grid[x + 1][y - 1] == 1:
                                q.append((x + 1, y - 1))
                                grid[x + 1][y - 1] = -1
                    area = max(area, ans)
        return area

    #fix the eq
    def calculate_done(self, w, b):
        white_volume=0
        black_volume=0
        for key in iter(sorted(w.keys())):
            white_volume+=(key-next(iter(sorted(w.keys()))))*self.gap.value()/3*(w[key][0]+w[next(iter(sorted(w.keys())))][0]+(w[key][0]*w[next(iter(sorted(w.keys())))][0])**(1/2))
        for key in iter(sorted(b.keys())):
            black_volume+=(key-next(iter(sorted(b.keys()))))*self.gap.value()/3*(b[key][1]+b[next(iter(sorted(b.keys())))][1]+(b[key][1]*b[next(iter(sorted(b.keys())))][1])**(1/2))
        self.resultcanine.append(str(abs(white_volume)))
        self.resultcavity.append(str(abs(black_volume)))
        if (abs(white_volume)-abs(black_volume))==0:
            return
        self.resultratio.append(str(abs(black_volume)/(abs(white_volume)-abs(black_volume))))
