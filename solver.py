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

class Action:
    def __init__(self, cost, reward):
        self.cost = cost
        self.reward = reward

    def __repr__(self):
        return f'Cost: {self.cost}, Reward: {self.reward}'

    def parse(line):
        # Split the line into cost and reward
        cost, reward = line.split('=>')
        # Split cost and reward into individual items
        cost = cost.split(' ')
        reward = reward.split(' ')
        # Convert cost and reward to dictionaries
        cost = {item[-1]: int(item[:-1]) for item in cost}
        reward = {item[-1]: int(item[:-1]) for item in reward}
        return Action(cost, reward)

class Resources:
    def __init__(self, resources):
        self.resources = resources

    def __repr__(self):
        return f'Resources: {self.resources}'

    def parse(line):
        # Split the line into resources
        resources = line.split(' ')
        # Convert resources to dictionary
        resources = {item[-1]: int(item[:-1]) for item in resources}
        return Resources(resources)


class GameState:
    def __init__(self, resources, sequence):
        self.resources = resources
        self.sequence = sequence

    def __repr__(self):
        return f'Resources: {self.resources}, Sequence: {self.sequence}'

    def is_solved(self, target):
        return all([self.resources.resources[resource] >= target.resources[resource] for resource in target.resources])
    
    def can_perform_action(self, action):
        return all([self.resources.resources[resource] >= action.cost[resource] for resource in action.cost])
    
    def perform_action(self, action):
        # Update the resources
        for resource in action.reward:
            self.resources.resources[resource] += action.reward[resource]
        # Append the action to the sequence
        self.sequence.append(action)

class Game:
    def __init__(self, rounds, actions_per_round, start, target, actions):
        self.rounds = rounds
        self.actions_per_round = actions_per_round
        self.start = start
        self.target = target
        self.actions = actions

    def __repr__(self):
        return f'Game: {self.rounds}, {self.actions_per_round}, {self.start}, {self.target}, {self.actions}'

    def parse_from_file(file):
        # Read the lines
        lines = file.readlines()
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

    def is_solved(self, current_resources):
        return all([current_resources.resources[resource] >= self.target.resources[resource] for resource in self.target.resources])
    
    def solve(self):
        # Initialize the current resources
        current_resources = self.start
        # Initialize the sequence of actions
        state = GameState(current_resources, [])
        # Iterate over rounds
        for _ in range(self.rounds):
            # Iterate over actions per round
            for _ in range(self.actions_per_round):
                # Iterate over actions
                for action in self.actions:
                    # Check if there are enough resources to perform the action and perform it only if corresponding resource is not already at the target
                    if state.can_perform_action(action) and not all([current_resources.resources[resource] >= self.target.resources[resource] for resource in action.reward]):
                        state.perform_action(action)
                        break
                if state.is_solved(self.target):
                    break
            if state.is_solved(self.target):
                break
            # Restore the astronauts
            current_resources.resources['A'] = self.start.resources['A']
        return state.sequence
    
    # def find_min_steps(self):
    #     # Initialize the memoization table
    #     memo = {}

    #     def backtrack(remaining_rounds, resources, current_step):
    #         # Check if the current state is already computed
    #         state = (remaining_rounds, tuple(sorted(resources.items())))
    #         if state in memo:
    #             return memo[state]

    #         # Check if the target is reached or exceeded
    #         if all(resources[resource] >= target_resources[resource] for resource in 'CDN'):
    #             return current_step

    #         # If no more rounds, return infinity
    #         if remaining_rounds == 0:
    #             return float('inf')

    #         min_steps = float('inf')
    #         # Attempt each action in the current round
    #         for cost, reward in actions:
    #             if can_perform_action(resources, cost):
    #                 new_resources = perform_action(resources.copy(), cost, reward)

    #                 # Restore astronauts at the end of each round
    #                 if current_step % actions_per_round == 0 and current_step != 0:
    #                     new_resources['A'] = starting_resources['A']

    #                 steps = backtrack(remaining_rounds - 1, new_resources, current_step + 1)
    #                 min_steps = min(min_steps, steps)

    #         # Memoize and return the minimum steps
    #         memo[state] = min_steps
    #         return min_steps

    #     return backtrack(num_rounds, starting_resources, 0)



def main():
    # Read the game from the file
    with open('rules.txt', 'r') as file:
        game = Game.parse_from_file(file)
    # Solve the game
    sequence = game.solve()
    # Print the sequence
    print(sequence)

def test_solve():
    # Test 1
    game = Game(3, 4, Resources({'P': 10, 'A': 3, 'C': 0, 'D': 0, 'N': 0}), Resources({'C': 5, 'D': 2, 'N': 1}), [
        Action({'D': 1, 'N': 1}, {'C': 3}),
        Action({'D': 1}, {'N': 3, 'C': 2}),
        Action({'C': 1}, {'N': 2}),
        Action({'P': 1}, {'C': 3}),
        Action({'P': 1}, {'D': 2})
    ])
    sequence = game.solve()
    print(sequence)

if __name__ == '__main__':
    # main()
    test_solve()