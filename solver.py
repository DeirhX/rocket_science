# Determines the least number of actions that need to be taken to achieve desired combination of resources
# Each action consumes one or more resources and produces one or more of the following: comms, data, navigation
# Resources are as follows: power, astronauts, comms, data, navigation
# Game starts with non-zero amount of power and zero of comms, data, and navigation
# Resources are consumed and produced in integer amounts
# Each game has a set of actions that can be performed, denoted by letters
# Each action has a cost and a reward
# Cost is a set of resources that are consumed in form of [number][resource], using letters from above
# Example cost: 1P, 2A, 3D, 4N
# Rewards use the same format
# Example line: 1P, 2A, 3D, 4N => 5C, 6D, 7N

# Rules:
# - Game is divided into rounds
# - Each round, player can perform a constant number of actions
# - Each action consumes resources and can be performed only if there are enough resources
# - Each action produces resources
# - Actions can be performed in any order and any number of times
# - Power can be only consumed, not produced
# - Astronauts can be only consumed, but restored at the end of each round
# - Goal is to achieve a certain minimum number of comms, data, and navigation

# Input:
# - Number of rounds, number of actions per round
# - Starting resources
# - Target (minimum) resources
# - List of actions

# Output:
# - Sequence of indices of actions to achieve target resources

# Example input:
# 3 4
# 10P 3A
# 5C 2D 1N
# 1C 1D => 2D 2N
# 1P => 3C 
# 1P => 2D

# Example output:
# 2 3 4

import time

class Resources:
    def __init__(self, resources : dict):
        self.lookup = resources

    def __repr__(self):
        return f'Resources: {self.lookup}'

    def __add__(self, other):
        return Resources({resource: self.lookup[resource] + other.lookup[resource] for resource in other.lookup})
    
    def __sub__(self, other):
        return Resources({resource: self.lookup[resource] - other.lookup[resource] for resource in other.lookup})

    def exclude(self, resource_name):
        return Resources({resource: self.lookup[resource] for resource in self.lookup if resource != resource_name})

    def parse(line):
        # Split the line into resources
        resources = line.split(' ')
        # Convert resources to dictionary
        resources = {item[-1]: int(item[:-1]) for item in resources}
        return Resources(resources)

class Action:
    def __init__(self, cost: Resources, reward: Resources):
        self.cost = cost
        self.reward = reward

    def __repr__(self):
        return f'Cost: {self.cost}, Reward: {self.reward}, Rating: {self.rate()}'

    def parse(line):
        # Split the line into cost and reward
        cost, reward = line.split('=>')
        # Split cost and reward into individual items
        cost = cost.strip().split(' ')
        reward = reward.strip().split(' ')
        # Convert cost and reward to dictionaries
        cost = {item[-1]: int(item[:-1]) for item in cost}
        reward = {item[-1]: int(item[:-1]) for item in reward}
        return Action(Resources(cost), Resources(reward))
    
    def rate(self):
        return sum(self.reward.lookup.values()) - sum(self.cost.exclude('A').lookup.values()) - self.cost.lookup.get('P', 0)


class GameState:
    def __init__(self, resources: Resources, moves: int):
        self.resources = resources
        self.moves = moves

    def __repr__(self):
        return f'Resources: {self.resources}, Moves made: {self.moves}'

    def get_moves(self):
        return self.moves
    
    def diff_with_target(self, target: Resources):
        return target - self.resources
    
    def rate(self, target: Resources):
        return sum(self.resources.exclude('A').lookup.values()) - self.moves - sum(target.lookup.values()) + 2 * self.resources.lookup.get('P', 0) - target.lookup.get('P', 0)

    def is_solved(self, target: Resources):
        return all([self.resources.lookup[resource] >= target.lookup[resource] for resource in target.lookup])

    def can_be_solved(self, remaining_rounds : int, target_resources: Resources, max_resources_per_round : Resources):
        return all([self.resources.lookup[resource] + remaining_rounds * max_resources_per_round.lookup[resource] >= target_resources.lookup[resource] for resource in max_resources_per_round.lookup])
    
    def can_perform_action(self, action: Action):
        return all([self.resources.lookup[resource] >= action.cost.lookup[resource] for resource in action.cost.lookup])
    
    def perform_action(self, action: Action):
        # Update the resources
        for resource in action.cost.lookup:
            self.resources.lookup[resource] -= action.cost.lookup[resource]
        for resource in action.reward.lookup:
            self.resources.lookup[resource] += action.reward.lookup[resource]
        self.moves += 1

# derived from GameState
class GameSequence(GameState):
    def __init__(self, resources: Resources, sequence):
        super().__init__(resources, len(sequence))
        self.sequence = sequence

    def __repr__(self):
        return f'Resources: {self.resources}, Actions: {len(self.sequence)}, Sequence: {self.sequence}'
    
    def copy(self):
        return GameSequence(Resources(self.resources.lookup.copy()), list(self.sequence))

    def get_moves(self):
        return len(self.sequence)

    def perform_action(self, action):
        super().perform_action(action)
        # Update the sequence
        self.sequence.append(action)

class Game:
    def __init__(self, rounds: int, actions_per_round: int, start: Resources, target: Resources, actions: list):
        self.rounds = rounds
        self.actions_per_round = actions_per_round
        self.start = start
        self.target = target
        self.actions = sorted(actions, key=lambda action: -action.rate())
        self.max_resources_per_round = Resources(self._get_maximum_resources_per_round())

    def __repr__(self):
        return f'Game: {self.rounds}, {self.actions_per_round}, {self.start}, {self.target}, {self.actions}'

    def parse_from_file(file):
        # Read the lines without the newline character
        lines = [line.rstrip('\n') for line in file]
        # Get the number of rounds and actions per round
        rounds, actions_per_round = lines[0].split(' ')
        rounds = int(rounds)
        actions_per_round = int(actions_per_round)
        # Get the starting resources
        start = Resources.parse(lines[1])
        # Get the target resources
        target = Resources.parse(lines[2])
        # Get the actions
        actions = [Action.parse(line) for line in lines[3:]]
        return Game(rounds, actions_per_round, start, target, actions)

    def is_solved(self, current_resources: Resources):
        return all([current_resources.lookup[resource] >= self.target.lookup[resource] if self.target.lookup[resource] > 0 else current_resources.lookup[resource] < self.target.lookup[resource] for resource in self.target.lookup])
    
    def can_be_solved(self, state: GameState):
        return state.can_be_solved(self.remaining_rounds(state), self.target, self.max_resources_per_round)

    def remaining_rounds(self, state: GameState):
        return self.rounds * self.actions_per_round - state.get_moves()

    def _get_maximum_resources_per_round(self):
        # Get the maximum resources per round
        maximum_resources_per_round = {}
        for action in self.actions:
            for resource in action.reward.lookup:
                if resource not in maximum_resources_per_round or maximum_resources_per_round[resource] < action.reward.lookup[resource]:
                    maximum_resources_per_round[resource] = action.reward.lookup[resource]
        return maximum_resources_per_round

    def advance_round(self, current_resources: Resources):
        # Restore the astronauts
        if 'A' in current_resources.lookup:
            current_resources.lookup['A'] = self.start.lookup['A']
        if 'R' in current_resources.lookup:
            current_resources.lookup['R'] = 0
        if 'H' in current_resources.lookup:
            current_resources.lookup['H'] -= 2

    def simulate_sequence(self, sequence: GameSequence):
        # Initialize the current resources
        current_resources = Resources(self.start.lookup.copy())
        round = 0
        # Iterate over actions
        for action in sequence.sequence:
            if round % self.actions_per_round == 0 and round != 0:
                self.advance_round(current_resources)
            # Check if there are enough resources to perform the action and perform it only if corresponding resource is not already at the target
            for resource in action.cost.lookup:
                current_resources.lookup[resource] -= action.cost.lookup[resource]
                if current_resources.lookup[resource] < 0:
                    return None
            for resource in action.reward.lookup:
                current_resources.lookup[resource] += action.reward.lookup[resource]
        return current_resources

    def solve(self):
        # Initialize the current resources
        current_resources = Resources(self.start.lookup.copy())
        # Initialize the sequence of actions
        state = GameSequence(current_resources, [])
        # Iterate over rounds
        for _ in range(self.rounds):
            # Iterate over actions per round
            for _ in range(self.actions_per_round):
                # Iterate over actions
                for action in self.actions:
                    # Check if there are enough resources to perform the action and perform it only if corresponding resource is not already at the target
                    if state.can_perform_action(action) and not all([current_resources.lookup[resource] >= self.target.lookup[resource] for resource in action.reward]):
                        state.perform_action(action)
                        break
                if state.is_solved(self.target):
                    break
            if state.is_solved(self.target):
                break
            # Restore the astronauts
            self.advance_round(current_resources)
        return state.sequence
    
    def find_min_steps(self) -> GameSequence:
        # Initialize the memoization table
        memo = {}
        # Initialize the best solution
        best_solution = None
        # Measure time taken
        start_time = time.time()

        def backtrack(remaining_rounds: int, state: GameSequence) -> GameSequence:
            nonlocal best_solution
            if best_solution is not None and (len(state.sequence) > len(best_solution.sequence) or state.resources.lookup['P'] <= best_solution.resources.lookup['P']):
                return None

            # Check if the current state is already computed
            hashed_state = (remaining_rounds, tuple(sorted(state.resources.lookup.items())))
            if hashed_state in memo:
                return memo[hashed_state]

            if state.is_solved(self.target):
                best_solution = state
                print(f"Found solution rating {state.rate(self.target)} ({state.get_moves()} moves) at memo size: {len(memo)}") # + ", " + str(state))
                return state

            if remaining_rounds == 0 or not self.can_be_solved(state):
                return None

            min_steps = None
            # Attempt each action in the current round
            for action in self.actions:
                if state.can_perform_action(action):
                    # Make a copy of the state parameter
                    new_state = state.copy()
                    new_state.perform_action(action)

                    # Restore astronauts and other effects at the end of the phase
                    if new_state.get_moves() % self.actions_per_round == 0 and new_state.get_moves() != 0:
                        self.advance_round(new_state.resources)

                    steps = backtrack(remaining_rounds - 1, new_state)
                    min_steps = steps if steps is not None and (min_steps is None or len(steps.sequence) < len(min_steps.sequence)) else min_steps

            # Memoize and return the minimum steps
            memo[(remaining_rounds, tuple(sorted(state.resources.lookup.items())))] = min_steps
            if len(memo) % 10000 == 0:
                print("Memo size: " + str(len(memo)))
            return min_steps

        result = backtrack(self.rounds * self.actions_per_round, GameSequence(self.start, []))
        return (result, len(memo), time.time() - start_time)
    
def main():
    # Read the game from the file
    with open('space-station-brutal.txt', 'r') as file:
        game = Game.parse_from_file(file)
    # Solve the game
    sequence, search_depth, time_taken = game.find_min_steps()
    print(sequence)
    print(f'Search depth: {str(search_depth)}, time taken: {str(round(time_taken * 1000) / 1000)} seconds')
    print(f'Rating: {sequence.rate(game.target)}')
    print(f'Extra resources: {sequence.resources - game.target}')
    print(f'Simulated outcome: {game.simulate_sequence(sequence)}')

def test_solve():
    # Test 1
    game = Game(3, 4, Resources({'P': 10, 'A': 3, 'C': 0, 'D': 0, 'N': 0}), Resources({'C': 5, 'D': 2, 'N': 1}), [
        Action({'D': 1, 'N': 1}, {'C': 3}),
        Action({'D': 1}, {'N': 3, 'C': 2}),
        Action({'C': 1}, {'N': 2}),
        Action({'P': 1}, {'C': 3}),
        Action({'P': 1}, {'D': 2})
    ])
    sequence = game.find_min_steps()
    print(sequence)

if __name__ == '__main__':
    main()
    # test_solve()