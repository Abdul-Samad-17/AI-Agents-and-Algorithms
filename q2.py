"""
    Abdul Samad
    24I-0095
    AI-B
"""
import random
import time
import heapq
import collections
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from copy import deepcopy

import json

# The Maze class handles the grid, obstacles, and moving positions
class DynamicMaze:
    def __init__(self, size=20, obstacle_prob=0.3):
        self.size = max(size, 20)
        self.grid = np.zeros((self.size, self.size), dtype=object)
        self.obstacles = set()
        self.S, self.G = None, None
        self.move_count = 0
        self._setup_maze(obstacle_prob)
    
    def _setup_maze(self, prob):
        # We keep trying until a valid path exists from start to goal
        while True:
            self.grid[:] = 0
            self.obstacles.clear()
            for r in range(self.size):
                for c in range(self.size):
                    if random.random() < prob:
                        self.grid[r, c] = 1
                        self.obstacles.add((r, c))
            self.S = self._find_empty()
            while True:
                self.G = self._find_empty()
                if self.S != self.G and (abs(self.S[0]-self.G[0]) + abs(self.S[1]-self.G[1])) >= 15:
                    break
            self.grid[self.S], self.grid[self.G] = 'S', 'G'
            if self.has_path(self.S, self.G): break
    
    def _find_empty(self):
        while True:
            r, c = random.randint(0, self.size-1), random.randint(0, self.size-1)
            if self.grid[r, c] == 0: return (r, c)

    def has_path(self, start, goal):
        # A simple BFS to check if the goal is reachable
        q = collections.deque([start])
        visited = {start}
        while q:
            curr = q.popleft()
            if curr == goal: return True
            for n in self.get_neighbors(curr):
                if n not in visited:
                    visited.add(n); q.append(n)
        return False

    def update(self, bonus=True):
        # Updates moving things every few steps
        self.move_count += 1
        if self.move_count % 10 == 0:
            cell = self._find_empty()
            self.grid[cell] = 1; self.obstacles.add(cell)
        if self.move_count % 15 == 0 and self.obstacles:
            obs = random.choice(list(self.obstacles))
            adj = self._get_adj_empty(obs)
            if adj:
                self.grid[obs] = 0; self.obstacles.remove(obs)
                new = random.choice(adj)
                self.grid[new] = 1; self.obstacles.add(new)
        if bonus and self.move_count % 20 == 0:
            target = random.choice(['S', 'G'])
            old = self.S if target == 'S' else self.G
            adj = self._get_adj_empty(old)
            if adj:
                new = random.choice(adj)
                self.grid[old] = 0
                if target == 'S': self.S = new
                else: self.G = new
                self.grid[new] = target

    def _get_adj_empty(self, pos):
        return [ (pos[0]+dr, pos[1]+dc) for dr, dc in [(0,1),(0,-1),(1,0),(-1,0)]
                 if 0 <= pos[0]+dr < self.size and 0 <= pos[1]+dc < self.size 
                 and self.grid[pos[0]+dr, pos[1]+dc] == 0 ]

    def get_neighbors(self, pos):
        return [ (pos[0]+dr, pos[1]+dc) for dr, dc in [(0,1),(0,-1),(1,0),(-1,0)]
                 if 0 <= pos[0]+dr < self.size and 0 <= pos[1]+dc < self.size 
                 and self.grid[pos[0]+dr, pos[1]+dc] != 1 ]

# We track metrics like steps, nodes expanded, and time for each search
class Result:
    def __init__(self, name):
        self.name, self.steps, self.exp, self.success, self.time, self.mem, self.reroutes = name, 0, 0, False, 0, 0, 0
        self.history = []

    def to_dict(self):
        return {
            "name": self.name,
            "success": self.success,
            "steps": self.steps,
            "exp": self.exp,
            "time": f"{self.time:.4f}",
            "history": self.history
        }

def run_agent(name, maze_obj):
    # The agent runs a search, moves, and re-plans if a path is blocked
    maze = deepcopy(maze_obj)
    res = Result(name)
    start = time.time()
    curr = maze.S
    path_taken = [curr]
    algos = {"BFS": bfs, "DFS": dfs, "UCS": ucs, "DLS": dls, "IDS": ids, "Greedy": greedy, "A*": astar}
    
    # Save initial state
    res.history.append({
        "grid": maze.grid.tolist(),
        "pos": curr,
        "path": [],
        "taken": path_taken[:]
    })

    while curr != maze.G and res.steps < maze.size * maze.size:
        ok, path, exp, mem, _ = algos[name](maze, curr, maze.G)
        res.exp += exp; res.mem = max(res.mem, mem)
        
        if not ok or len(path) < 2: 
            break
        
        # Follow the path until it ends or is blocked
        for i in range(1, len(path)):
            nxt = path[i]
            if maze.grid[nxt] == 1: 
                res.reroutes += 1
                break
            
            curr = nxt
            path_taken.append(curr)
            res.steps += 1
            maze.update()
            
            # Record state after each move
            res.history.append({
                "grid": maze.grid.tolist(),
                "pos": curr,
                "path": path[i:], # Remaining path planned
                "taken": path_taken[:]
            })
            
            if curr == maze.G: 
                break
            
            # Check if next step in planned path is now blocked
            if i+1 < len(path) and maze.grid[path[i+1]] == 1:
                res.reroutes += 1
                break
                
    res.success = (curr == maze.G); res.time = time.time() - start
    return res

# --- Algorithms ---

def bfs(m, s, g):
    f, c, e = collections.deque([s]), {s: None}, 0
    while f:
        curr = f.popleft(); e += 1
        if curr == g: return True, _path(c, curr), e, len(c), []
        for n in m.get_neighbors(curr):
            if n not in c: c[n] = curr; f.append(n)
    return False, [], e, len(c), []

def dfs(m, s, g):
    f, c, e = [s], {s: None}, 0
    while f:
        curr = f.pop(); e += 1
        if curr == g: return True, _path(c, curr), e, len(c), []
        for n in m.get_neighbors(curr):
            if n not in c: c[n] = curr; f.append(n)
    return False, [], e, len(c), []

def ucs(m, s, g):
    f, c, costs, e = [(0, s)], {s: None}, {s: 0}, 0
    while f:
        cost, curr = heapq.heappop(f); e += 1
        if curr == g: return True, _path(c, curr), e, len(c), []
        for n in m.get_neighbors(curr):
            if n not in costs or costs[curr]+1 < costs[n]:
                costs[n] = costs[curr]+1; c[n] = curr; heapq.heappush(f, (costs[n], n))
    return False, [], e, len(c), []

def dls(m, s, g, limit=30):
    def rdls(node, depth, c, v, st):
        st['e'] += 1
        if node == g: return True
        if depth == 0: return False
        for n in m.get_neighbors(node):
            if n not in v:
                v.add(n); c[n] = node
                if rdls(n, depth-1, c, v, st): return True
        return False
    st, c, v = {'e': 0}, {s: None}, {s}
    ok = rdls(s, limit, c, v, st)
    return ok, (_path(c, g) if ok else []), st['e'], len(v), []

def ids(m, s, g):
    total_e, max_m = 0, 0
    for d in range(30):
        ok, p, e, me, _ = dls(m, s, g, d)
        total_e += e; max_m = max(max_m, me)
        if ok: return True, p, total_e, max_m, []
    return False, [], total_e, max_m, []

def greedy(m, s, g):
    f, c, e = [(abs(s[0]-g[0])+abs(s[1]-g[1]), s)], {s: None}, 0
    while f:
        _, curr = heapq.heappop(f); e += 1
        if curr == g: return True, _path(c, curr), e, len(c), []
        for n in m.get_neighbors(curr):
            if n not in c:
                c[n] = curr; heapq.heappush(f, (abs(n[0]-g[0])+abs(n[1]-g[1]), n))
    return False, [], e, len(c), []

def astar(m, s, g):
    f, c, costs, e = [(abs(s[0]-g[0])+abs(s[1]-g[1]), s)], {s: None}, {s: 0}, 0
    while f:
        _, curr = heapq.heappop(f); e += 1
        if curr == g: return True, _path(c, curr), e, len(c), []
        for n in m.get_neighbors(curr):
            if n not in costs or costs[curr]+1 < costs[n]:
                costs[n] = costs[curr]+1; c[n] = curr
                heapq.heappush(f, (costs[n]+abs(n[0]-g[0])+abs(n[1]-g[1]), n))
    return False, [], e, len(c), []

def _path(c, curr):
    p = []
    while curr is not None: p.append(curr); curr = c.get(curr)
    return p[::-1]

def main():
    print("Initializing Dynamic Maze Search")
    base = DynamicMaze(20, 0.3)
    algos = ["BFS", "DFS", "UCS", "DLS", "IDS", "Greedy", "A*"]
    all_results = []
    
    for a in algos:
        print(f"Running {a}...")
        res = run_agent(a, base)
        print(f"{a}: Success={res.success}, Steps={res.steps}, Nodes={res.exp}, Reroutes={res.reroutes}")
        all_results.append(res.to_dict())
    
    # Export to JSON for visualization
    with open("q2_replay.json", "w") as f:
        json.dump({
            "grid_size": base.size,
            "results": all_results,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }, f, indent=2)
    print("Results exported to q2_replay.json")

if __name__ == "__main__":
    main()
