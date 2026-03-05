"""
    Abdul Samad
    24I-0095
    AI-B
"""
import sys
import random
import json
import os
import webbrowser
import time
from agents import Agent, Environment, TraceAgent

# Set seed for random values based on current time
random.seed(int(time.time() * 1000) + os.getpid())

class PuzzlePiece:
    # A single piece of the puzzle
    def __init__(self, correct_row, correct_col, orientation=0):
        self.correct_pos = (correct_row, correct_col)
        self.orientation = orientation

    def is_correctly_placed(self, current_pos):
        # Checks if piece is at the right spot and rotated correctly
        return self.correct_pos == current_pos and self.orientation == 0

    def rotate_left(self):
        self.orientation = (self.orientation + 90) % 360

    def rotate_right(self):
        self.orientation = (self.orientation - 90) % 360
        if self.orientation < 0:
            self.orientation += 360

    def deep_copy(self):
        return PuzzlePiece(self.correct_pos[0], self.correct_pos[1], self.orientation)

class JigsawEnvironment(Environment):
    # This environment manages the puzzle pieces on a grid
    def __init__(self, size=5, max_moves=100):
        super().__init__()
        self.size = size
        self.max_moves = max_moves
        self.steps_taken = 0
        self.history = []
        self.grid = [[None for _ in range(size)] for _ in range(size)]
        self._init_puzzle()

    def _init_puzzle(self):
        # Create pieces and shuffle them randomly
        pieces = []
        for r in range(self.size):
            for c in range(self.size):
                orientation = random.choice([0, 90, 180, 270])
                pieces.append(PuzzlePiece(r, c, orientation))
        random.shuffle(pieces)
        idx = 0
        for r in range(self.size):
            for c in range(self.size):
                self.grid[r][c] = pieces[idx]
                idx += 1

    def default_location(self, thing):
        return (random.randint(0, self.size - 1), random.randint(0, self.size - 1))

    def percept(self, agent):
        # Tells the agent about the piece at its current location
        r, c = agent.location
        piece = self.grid[r][c]
        is_holding = len(agent.holding) > 0
        return {
            'position': (r, c),
            'piece_id': piece.correct_pos,
            'orientation': piece.orientation,
            'is_correct': piece.is_correctly_placed((r, c)),
            'grid_size': self.size,
            'holding': is_holding
        }

    def execute_action(self, agent, action):
        # Updates the grid or agent based on the chosen action
        if self.steps_taken >= self.max_moves:
            return
        r, c = agent.location
        if action == 'Grab' and not agent.holding:
            agent.holding.append(True)
        elif action == 'Release' and agent.holding:
            agent.holding.pop()
        elif action == 'Left' and c > 0:
            if agent.holding:
                self.grid[r][c], self.grid[r][c - 1] = self.grid[r][c - 1], self.grid[r][c]
            agent.location = (r, c - 1)
        elif action == 'Right' and c < self.size - 1:
            if agent.holding:
                self.grid[r][c], self.grid[r][c + 1] = self.grid[r][c + 1], self.grid[r][c]
            agent.location = (r, c + 1)
        elif action == 'Up' and r > 0:
            if agent.holding:
                self.grid[r][c], self.grid[r - 1][c] = self.grid[r - 1][c], self.grid[r][c]
            agent.location = (r - 1, c)
        elif action == 'Down' and r < self.size - 1:
            if agent.holding:
                self.grid[r][c], self.grid[r + 1][c] = self.grid[r + 1][c], self.grid[r][c]
            agent.location = (r + 1, c)
        elif action == 'Rotate_left':
            self.grid[r][c].rotate_left()
        elif action == 'Rotate_right':
            self.grid[r][c].rotate_right()
        self.steps_taken += 1
        self.history.append({
            'action': action, 'agent_loc': agent.location,
            'holding': bool(agent.holding), 'grid': self.get_grid_state()
        })

    def get_grid_state(self):
        state = []
        for r in range(self.size):
            row = []
            for c in range(self.size):
                p = self.grid[r][c]
                row.append({'target': p.correct_pos, 'orientation': p.orientation})
            state.append(row)
        return state

    def is_done(self):
        return self.steps_taken >= self.max_moves or self.is_solved()

    def count_correct(self):
        # Counts how many pieces are in the right position and orientation
        count = 0
        for r in range(self.size):
            for c in range(self.size):
                if self.grid[r][c].is_correctly_placed((r, c)):
                    count += 1
        return count

    def is_solved(self):
        return self.count_correct() == self.size * self.size

    def performance(self):
        if self.steps_taken == 0: return 0.0
        return self.count_correct() / self.steps_taken

    def deep_copy(self):
        # Creates a fresh copy so both agents start with the same puzzle
        new_env = JigsawEnvironment.__new__(JigsawEnvironment)
        new_env.things, new_env.agents, new_env.history = [], [], []
        new_env.size, new_env.max_moves, new_env.steps_taken = self.size, self.max_moves, 0
        new_env.grid = [[None] * self.size for _ in range(self.size)]
        for r in range(self.size):
            for c in range(self.size):
                new_env.grid[r][c] = self.grid[r][c].deep_copy()
        return new_env

    def print_state(self, title="Puzzle State"):
        # Prints out the current state of the puzzle grid
        print(f"\n{'=' * 60}")
        print(f"  {title}")
        print(f"{'=' * 60}")
        print(f"  Grid Size     : {self.size} x {self.size}")
        print(f"  Correct Pieces: {self.count_correct()} / {self.size * self.size}")
        print(f"  Moves Used    : {self.steps_taken}")

        if self.size <= 8:
            # Show the full grid if it's small enough to read
            print(f"\n  Legend: [target_pos | rotation, C=correct X=wrong]")
            for r in range(self.size):
                row_str = "  "
                for c in range(self.size):
                    p = self.grid[r][c]
                    mark = "C" if p.is_correctly_placed((r, c)) else "X"
                    row_str += f"[({p.correct_pos[0]},{p.correct_pos[1]}){p.orientation:>4}{mark}] "
                print(row_str)
        else:
            # Show just a corner for larger puzzles to save space
            corner = min(5, self.size)
            print(f"\n  Top-left {corner}x{corner} corner preview:")
            for r in range(corner):
                row_str = "  "
                for c in range(corner):
                    p = self.grid[r][c]
                    mark = "C" if p.is_correctly_placed((r, c)) else "X"
                    row_str += f"[({p.correct_pos[0]:>2},{p.correct_pos[1]:>2}){p.orientation:>4}{mark}] "
                print(row_str)
            print("  ...")
        print(f"{'=' * 60}")

def simple_reflex_program(percept):
    # Simple reflex agent that prioritizes fixing pieces and avoids wandering
    pos = percept['position']
    piece_id = percept['piece_id']
    orientation = percept['orientation']
    is_correct = percept['is_correct']
    grid_size = percept['grid_size']
    holding = percept['holding']
    r, c = pos
    target_r, target_c = piece_id

    if holding:
        # If holding a piece, move it to its target cell and correct orientation
        if (r, c) == (target_r, target_c):
            if orientation != 0:
                return 'Rotate_left' if orientation == 270 else 'Rotate_right'
            return 'Release'
        # Manhattan step towards target
        dr = target_r - r
        dc = target_c - c
        if abs(dr) >= abs(dc):
            return 'Down' if dr > 0 else 'Up'
        else:
            return 'Right' if dc > 0 else 'Left'
    else:
        # Not holding anything
        # If piece is at its target but mis‑oriented, rotate in place
        if (r, c) == (target_r, target_c) and orientation != 0:
            return 'Rotate_left' if orientation == 270 else 'Rotate_right'
        # If piece is misplaced or mis‑oriented, grab it
        if not is_correct:
            return 'Grab'
        # Current piece is correct; scan to next unchecked cell (simple raster)
        if c < grid_size - 1:
            return 'Right'
        if r < grid_size - 1:
            return 'Down'
        if c > 0:
            return 'Left'
        if r > 0:
            return 'Up'
        return 'NoOp'

class ModelBasedReflexProgram:
    # An agent that remembers observations and plans efficiently
    def __init__(self, grid_size):
        self.grid_size = grid_size
        self.model = [[None] * grid_size for _ in range(grid_size)]
        self.correct_cells = set()
        self.last_actions = []
        self.target_piece_to_fix = None

    def __call__(self, percept):
        r, c = percept['position']
        piece_id = percept['piece_id']
        orientation = percept['orientation']
        is_correct = percept['is_correct']
        holding = percept['holding']
        # Record observation
        self.model[r][c] = {'piece_id': piece_id, 'orientation': orientation}
        if is_correct:
            self.correct_cells.add((r, c))
        else:
            self.correct_cells.discard((r, c))

        if holding:
            target_r, target_c = piece_id
            if (r, c) == (target_r, target_c):
                if orientation != 0:
                    return self._record('Rotate_left' if orientation == 270 else 'Rotate_right')
                return self._record('Release')
            return self._record(self._step_towards(r, c, target_r, target_c))
        else:
            # Not holding a piece
            if (r, c) == piece_id and orientation != 0:
                return self._record('Rotate_left' if orientation == 270 else 'Rotate_right')
            if not is_correct:
                return self._record('Grab')
            nearest = self._nearest_wrong(r, c)
            if nearest:
                tr, tc = nearest
                return self._record(self._step_towards(r, c, tr, tc))
            return self._record(self._explore(r, c))

    def _nearest_wrong(self, r, c):
        best = None
        best_dist = float('inf')
        for rr in range(self.grid_size):
            for cc in range(self.grid_size):
                if (rr, cc) not in self.correct_cells and self.model[rr][cc] is not None:
                    dist = abs(rr - r) + abs(cc - c)
                    if dist < best_dist:
                        best_dist = dist
                        best = (rr, cc)
        return best

    def _step_towards(self, r, c, tr, tc):
        dr = tr - r
        dc = tc - c
        # Choose axis with larger distance first (deterministic)
        if abs(dr) >= abs(dc):
            primary = 'Down' if dr > 0 else 'Up'
            secondary = 'Right' if dc > 0 else 'Left'
        else:
            primary = 'Right' if dc > 0 else 'Left'
            secondary = 'Down' if dr > 0 else 'Up'
        # Avoid immediate back‑track
        if not self._creates_loop(primary):
            return primary
        if not self._creates_loop(secondary):
            return secondary
        return 'NoOp'

    def _explore(self, r, c):
        # Systematic exploration order, avoiding loops
        for action in ['Right', 'Down', 'Left', 'Up']:
            if self._creates_loop(action):
                continue
            nr, nc = r, c
            if action == 'Up':
                nr -= 1
            elif action == 'Down':
                nr += 1
            elif action == 'Left':
                nc -= 1
            elif action == 'Right':
                nc += 1
            if 0 <= nr < self.grid_size and 0 <= nc < self.grid_size:
                return action
        return 'NoOp'

    def _creates_loop(self, action):
        opposite = {'Left': 'Right', 'Right': 'Left', 'Up': 'Down', 'Down': 'Up'}
        if self.last_actions and self.last_actions[-1] == opposite.get(action):
            return True
        return False

    def _record(self, action):
        self.last_actions.append(action)
        if len(self.last_actions) > 10:
            self.last_actions.pop(0)
        return action

def main():
    viz = "--viz" in sys.argv
    if viz: sys.argv.remove("--viz")
    size = int(sys.argv[1]) if len(sys.argv) >= 2 else 5
    max_moves = int(sys.argv[2]) if len(sys.argv) >= 3 else 50
    env = JigsawEnvironment(size, max_moves)
    start_pos = env.default_location(None)
    e_reflex, e_model = env.deep_copy(), env.deep_copy()
    
    print("Starting Comparison")
    r_agent = TraceAgent(Agent(simple_reflex_program))
    e_reflex.add_thing(r_agent, location=start_pos)
    e_reflex.run()
    e_reflex.print_state("Simple Reflex Results")

    m_agent = TraceAgent(Agent(ModelBasedReflexProgram(size)))
    e_model.add_thing(m_agent, location=start_pos)
    e_model.run()
    e_model.print_state("Model-Based Results")

    # Show the results for both agents side-by-side
    res_reflex = e_reflex.performance()
    res_model = e_model.performance()

    print(f"\n{'=' * 60}")
    print(f"  PERFORMANCE COMPARISON")
    print(f"{'=' * 60}")
    print(f"  Reflex Agent      : No of correct pieces = {e_reflex.count_correct()}, no of moves utilized = {e_reflex.steps_taken}")
    print(f"  Model-based Agent : No of correct pieces = {e_model.count_correct()}, no of moves utilized = {e_model.steps_taken}")
    print(f"\n  Reflex Agent Performance      : {res_reflex:.4f}")
    print(f"  Model-based Agent Performance : {res_model:.4f}")
    print(f"{'=' * 60}\n")

    if viz:
        replay_data = {
            'timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
            'grid_size': size,
            'max_moves': max_moves,
            'initial_grid': env.get_grid_state(),
            'reflex': {'history': e_reflex.history, 'correct': e_reflex.count_correct()},
            'model': {'history': e_model.history, 'correct': e_model.count_correct()}
        }
        
        # Use index.html as a template for replay.html
        base_dir = os.path.dirname(os.path.abspath(__file__))
        template_path = os.path.join(base_dir, 'viz', 'index.html')
        output_path = os.path.join(base_dir, 'viz', 'replay.html')

        if os.path.exists(template_path):
            with open(template_path, 'r') as f:
                content = f.read()
            
            data_script = f"<script id='replay-data'>window.REPLAY_DATA = {json.dumps(replay_data, indent=2)};</script>"
            new_content = content.replace("<!-- DATA_PLACEHOLDER -->", data_script)
            
            with open(output_path, 'w') as f:
                f.write(new_content)
            
            print(f"Visualization saved to {output_path}")
            webbrowser.open_new_tab(os.path.abspath(output_path))
        else:
            print(f"Error: Visualizer template not found at {template_path}")

if __name__ == "__main__":
    main()


# python "d:\Semester 4\AI\A1\q1.py" 5 50 --viz
