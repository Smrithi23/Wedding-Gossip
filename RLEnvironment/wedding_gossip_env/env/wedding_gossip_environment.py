import random
import functools
from copy import copy
import numpy as np

from gymnasium.spaces import MultiDiscrete

from pettingzoo import ParallelEnv
from pettingzoo.utils import agent_selector, wrappers
from pettingzoo.test import parallel_api_test
from collections import defaultdict

# Action Constants
LISTEN_L = 0
LISTEN_R = 1
TALK_L = 2
TALK_R = 3
MOVE = 4
# Observation Constants (0-3 same as action)
NONE = 4

# Reward Params
ALPHA = 1
BETA = 1
GAMMA = 10
DELTA = 2

# Truncation condition
N_TURNS = 2048

class WeddingGossipEnvironment(ParallelEnv):
    metadata = {"render_modes": ["human"], 
                "name": "wedding_gossip_environment_v2"}

    def __init__(self, render_mode=None):
        self.possible_agents = ["player_" + str(r) for r in range(90)]
        self.agents = copy(self.possible_agents)

        # optional: a mapping between agent name and player_ID
        self.agent_name_mapping = dict(
            zip(self.possible_agents, 
                list(range(len(self.possible_agents)))
            )
        )
        self.render_mode = render_mode
        
        """
            obs = [self_pos, curr_goss, seating, nods, shakes]
        """
        self.observation_spaces = dict(
            zip(
                self.agents,
                [
                    MultiDiscrete(np.array([100, 90] + [91 for _ in range(100)] + [4, 4, 2049]))
                ]
                * 90,
            )
        )

        """
            action = [action, switch_goss, move_pref]
        """
        self.action_spaces = dict(
            zip(
                self.agents,
                [
                    MultiDiscrete(np.array([5, 2, 10]))
                ]
                * 90,
            )
        )

    def reset(self, seed=None, options=None):
        """
        Reset needs to initialize the `agents` attribute and must set up the
        environment so that render(), and step() can be called without issues.
        Here it initializes the `num_moves` variable which counts the number of
        hands that are played.
        Returns the observations for each agent
        """
        self.timestep = 0

        self.agents = copy(self.possible_agents)

        # a hash mapping player_ids to where they are situated on the board
        # each player_id is mapped to a number from 0-99. 
        # table_num = value % 10 (0-9)
        # seat_num = value / 10 (0-9)
        self.pos = random.sample(range(100), k=90)
        # update the self.seating list - 100 size list based on pos
        self.seating = None
        self._init_seating()

        self.agent_gossips = [[] for _ in range(90)]
        self.curr_gossips = [0 for _ in range(90)]

        self.obs_actions = [4 for _ in range(90)] 

        observations = {}
        gossip = random.sample(range(90), 90)
        for i, a in enumerate(self.agents):
            obs = np.array([self.pos[i], gossip[i]] + self.seating + [0, 0, 0])
            observations[a] = obs
            self.agent_gossips[self.agent_name_mapping[a]].append(gossip[i])

        # Get dummy infos. Necessary for proper parallel_to_aec conversion
        infos = {a: {} for a in self.agents}

        return observations, infos

    def step(self, actions):
        """
        step(action) takes in an action for each agent and should return the
        - observations
        - rewards
        - terminations
        - truncations
        - infos
        dicts where each dict looks like {agent_1: item_1, agent_2: item_2}
        """
        # If a user passes in actions with no agents, then just return empty observations, etc.
        if not actions:
            self.agents = []
            return {}, {}, {}, {}, {}

        self.timestep += 1

        rewards = {}
        """ reward function
        listen gossip i: + i * ALPHA
        talk gossip i: + i * num_nods - num_shake * BETA
        move: +GAMMA if success else -DELTA
        end: 1000000 / timestep (everyone has all gossip)
        """

        self.obs_actions = [4 for _ in range(90)]
        feedback = [[] for _ in range(90)]
        moves = []

        # check switch gossip
        for agent, action in actions.items():
            aid = self.agent_name_mapping[agent]
            if action[1] and len(self.agent_gossips[aid]) - 1 > self.curr_gossips[aid]:
                self.curr_gossips[aid] += 1
        
        # process listens -> talk -> move in order
        for agent, action in sorted(actions.items(), key=(lambda x: x[1][0])):
            # get action 
            act, _, seat = action
            aid = self.agent_name_mapping[agent]

            rewards[agent] = 0
            self.obs_actions[aid] = act

            # listen
            if act < 2:
                neighbors = self._get_left_neighbors(self.pos[aid]) if act == 0 else self._get_right_neighbors(self.pos[aid])

                possible_gossips = []
                for n in neighbors:
                    n_act = actions["player_" + str(n)][0]
                    n_goss = self.agent_gossips[n][self.curr_gossips[n]]
                    complement = 2 if act == 1 else 3
                    if n_act == complement:
                        if n_goss in self.agent_gossips[aid]:
                            feedback[n].append(False)
                        else:
                            possible_gossips.append((n_goss, n))
                heard_gossip = max(possible_gossips)[0] if possible_gossips else -1
                if heard_gossip >= 0:
                    i = 0
                    while i < len(self.agent_gossips[aid]) and self.agent_gossips[aid][i] > heard_gossip:
                        i += 1
                    self.agent_gossips[aid].insert(i, heard_gossip)
                for g, i in possible_gossips:
                    feedback[i].append((g == heard_gossip))
                rewards[agent] += (heard_gossip + 1) * ALPHA
            # talk 
            elif act < 4:
                # check if gossip to share is present in the player's gossip list
                goss = self.agent_gossips[aid][self.curr_gossips[aid]]
                # check for confirmation! If the said gossip was well-received, then give positive reward!
                for f in feedback[aid]:
                    rewards[agent] += goss if f else -BETA
            # move
            else:
                move_choice_order = []
                move_choice_order.append(seat)
                # fill out the rest - 
                for i in random.sample(range(10), 10):
                    if i not in move_choice_order:
                        move_choice_order.append(i)
                moves.append((aid, move_choice_order))

        self.available = self._get_available_seats()

        # resolve moves
        random.shuffle(moves)
        for aid, pref in moves:
            rewards["player_" + str(aid)] += GAMMA if self._move_player(aid, pref) else - DELTA

        observations = {}
        for a in self.agents:
            aid = self.agent_name_mapping[a]
            goss = self.agent_gossips[aid][self.curr_gossips[aid]]
            # gossips = [(1 if g in self.agent_gossips[aid] else 0) for g in range(90)]
            # tbl = aid // 10
            # tbl_actions = [(obs_actions[self.agent_name_mapping[n]] if self.pos[self.agent_name_mapping[n]] // 10 == tbl else 4) for n in self.agents]
            observations[a] = np.array([self.pos[aid], goss] + self.seating + [feedback[aid].count(True), feedback[aid].count(False), self.timestep])

        # Check termination conditions
        terminations = {agent: False for agent in self.agents}

        # Check truncation conditions (overwrites termination conditions)
        truncations = {a: (self.timestep >= N_TURNS) for a in self.agents}

        # Exit condition
        if any(terminations.values()) or all(truncations.values()):
            infos = {a: {"terminal_observation": observations} for a in self.agents}
            self.agents = []
        else:
            infos = {a: {} for a in self.agents}

        self.render()

        return observations, rewards, terminations, truncations, infos

    def render(self):
        print("===== SEATING / MOVES =====")
        print(f"Turn {self.timestep}")
        for i in range(10):
            table = []
            for j in range(i*10,(i+1)*10):
                player = self.seating[j]
                move = self.obs_actions[player] if player < 90 else 4
                table.append((player, move))
            print(f'Table {i}: {table}')
        print("===== GOSSIP INVENTORY =====")
        for i, g in enumerate(self.agent_gossips):
            print(f"Player {i}: {g}")
    
    def close(self):
        pass

    @functools.lru_cache(maxsize=None)
    def observation_space(self, agent):
        """
            array([seating, gossip, table actions])
        """
        return self.observation_spaces[agent]

    @functools.lru_cache(maxsize=None)
    def action_space(self, agent):
        """
            array([action, gossip, seat1, seat2])
        """
        return self.action_spaces[agent]

    def _get_available_seats(self):
        """
            A function that looks at self.pos, and returns a tuple of size 10 containing the available seats.
        """
        return list(set(range(100)).difference(set(self.pos)))

    def _init_seating(self):
        # a function to create and update the self.seating list - 100 size list. 90 represents empty seat!
        self.seating = [90 for _ in range(100)]
        for pid, seat in enumerate(self.pos):
            self.seating[seat] = pid

    def _get_left_neighbors(self, seat_id, _count=3):
        if _count > 9:
            print("CANT HAVE MORE THAN 9 LEFT NEIGHBORS!")
        
        neighbor_ids = []
        for i in range(1, _count+1):
            curr_seat_id = (seat_id // 10 * 10) + ((seat_id - i) % 10)
            if self.seating[curr_seat_id] < 90:
                neighbor_ids.append(self.seating[curr_seat_id])
        return neighbor_ids

    def _get_right_neighbors(self, seat_id, _count=3):
        if _count > 9:
            print("CANT HAVE MORE THAN 9 RIGHT NEIGHBORS!")
        
        neighbor_ids = []
        for i in range(1, _count+1):
            curr_seat_id = (seat_id // 10 * 10) + ((seat_id + i) % 10)
            if self.seating[curr_seat_id] < 90:
                neighbor_ids.append(self.seating[curr_seat_id])
        return neighbor_ids

    def _move_player(self, aid, priority_list):
        curr_seat = self.pos[aid]

        if len(priority_list) > 10:
            return False 

        for move in priority_list:
            new_seat = self.available[move]
            # check if new position is occupied
            if self.seating[new_seat] < 90:
                # move player from old position to new position
                self.seating[curr_seat] = 90 
                self.seating[new_seat] = aid

                # update player
                self.pos[aid] = new_seat 

                return True

        return False 

if __name__ == "__main__":
    env = WeddingGossipEnvironment()
    parallel_api_test(env, num_cycles=1_000_000)
