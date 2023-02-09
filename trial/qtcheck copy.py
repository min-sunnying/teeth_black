from typing import List, Tuple
from collections import deque

def largestRegion(grid: List[List[int]]) -> int:
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

def main():
    grid = [[1,1,1,1,1,1,1],
            [1,1,0,0,0,1,1],
            [1,1,0,1,0,1,1],
            [1,1,0,0,0,1,1],
            [1,1,1,1,1,1,1]]
    result = largestRegion(grid)
    print(f'Largest region of 1s has an area of {result}')

main()