from __future__ import annotations

import os
import random
import functools
import glob
import time

import numpy as np

import gymnasium
from gymnasium.spaces import Discrete

import supersuit as ss
from stable_baselines3 import PPO
from stable_baselines3.ppo import MlpPolicy
from pettingzoo.utils import parallel_to_aec

from RLEnvironment.wedding_gossip_env import wedding_gossip_environment_v1

CHECKPOINT_PATH="RLEnvironment/session_7aa24ecb/"
ENV_NAME="wedding_"

class Player():
    def __init__(self, id, team_num, table_num, seat_num, unique_gossip, color, turns):
        self.id = id
        self.team_num = team_num
        self.table_num = table_num
        self.seat_num = seat_num
        self.seat_id = self.table_num * 10 + seat_num # 0-99 format of seating

        self.color = color
        self.unique_gossip = unique_gossip
        self.gossip_list = [unique_gossip]
        self.group_score = 0
        self.individual_score = 0
        self.turns_num = turns

        # player id to seat id
        self.pos = [0 for _ in range(90)]

        # observation space vars
        self.time_stamp = 0
        self.gossip_i = 0
        self.seats = None
        self.obs_actions = [4 for _ in range(100)] 
        self.mem_buf = np.array([0, 90, 4] * 200)
        self.pos_mem = (None, None)
        self.state = None


        """
        # each tuple stores the following for seat 'seat_num' at table 'table_num'
        # 0 index - last observed action done by the player (initialized to None) - can be 'speak' or 'listen'
        # 1 index - direction of the action represented in action 0 (initialized to None) - can be 'left' or right
        # 2 index - player_id of last observed player at the seat (initialized to None)
        # 3 index - time_stamp of last observation (initialized to -1)
        self._curr_state = {seat_id: (None, None, None, -1) for seat_num in range(10)} for table_num in range(10)}

        # a hash mapping player_ids to where they are situated on the board
        # each player_id is mapped to (table_num, seat_num)
        # initialized to (None, None)
        self.player_seat_map = {p_id: (None, None) for p_id in range(90)}

        # action_to_num - to convert action into numerical value for model training purposes
        # can change the values to larger difference if this affects the model training
        self.action_to_num = {('speak', 'left'): 1,
                              ('speak', 'right'): 2,
                              ('listen', 'left'): 3,
                              ('listen', 'right'): 4}
        """
        self.action_to_val_map = {'listen-left':    0,
                                  'listen-right':   1,
                                  'talk-left':      2,
                                  'talk-right':     3}
 
        self.num_action_map = {
                0: ('listen', 'left'),
                1: ('listen', 'right'),
                2: ('talk', 'left'),
                3: ('talk', 'right'),
                4: ('move')
        }       

        try:
            latest_policy = max(
                glob.glob(f"{CHECKPOINT_PATH}{ENV_NAME}*.zip"), key=os.path.getctime
            )
        except ValueError:
            print("Policy not found.")
            exit(0)

        print(f"loading {latest_policy}")
        # load the trained model
        self.model = PPO.load(latest_policy)


    # At the beginning of a turn, players should be told who is sitting where, so that they can use that info to decide if/where to move
    def observe_before_turn(self, player_positions):
        """
            player_positions - 3-dimensional tuple: (player_id, table_num, seat_num)
        """
        self.seats = [90] * 100
        for inst in player_positions:
            self.pos[inst[0]] = inst[1] * 10 + inst[2]
            self.seats[inst[1] * 10 + inst[2]] = inst[0]
        
        # also update current seat_id, table_num, seat_num etc. 
        self.seat_id   = self.pos[self.id]
        self.table_num = self.seat_id // 10
        self.seat_num  = self.seat_id % 10

    # At the end of a turn, players should be told what everybody at their current table (who was there at the start of the turn)
    # did (i.e., talked/listened and in what direction)
    def observe_after_turn(self, player_actions):
        """
            player_actions - 2-dimensional list: [player_id, [player_action[0], player_action[1]]]. Where player_action[0] can be 'talk' or 'listen', and player_action[1] can be 'left' or 'right'
        """
        # update the global timer
        self.time_stamp += 1

        self.obs_actions = [4 for _ in range(100)]
        for inst in player_actions:
            seat = self.pos[inst[0]]
            self.obs_actions[seat] = self.action_to_val_map[inst[1][0] + '-' + inst[1][1]]

        self._update_memory()

    def get_action(self):
        # return 'talk', 'left', <gossip_number>
        # return 'talk', 'right', <gossip_number>
        # return 'listen', 'left', 
        # return 'listen', 'right', 
        # return 'move', priority_list: [[table number, seat number] ...]
        
        self.state = self._get_curr_state()

        observation = self._get_agent_obs()

        action, switch, _ = self.model.predict(observation)[0]

        i = self.gossip_i
        if switch == 1:
            self.gossip_i = min(len(self.gossip_list) - 1, i + 1)
        elif switch == 2:
            self.gossip_i = max(0, i - 1)

        if action < 2:
            return self.num_action_map[action][0], self.num_action_map[action][1]
        elif action < 4:
            goss = self.gossip_list[self.gossip_i]
            return self.num_action_map[action][0], self.num_action_map[action][1], goss
        else:
            empty = self._get_empty()
            random.shuffle(empty)
            return self.num_action_map[action], empty
        
    def _update_memory(self):
        self.mem_buf = np.concatenate((self.state, self.mem_buf[:300]))
        self.pos_mem = self.seat_id, self.pos_mem[0]

    def _get_empty(self):
        ret = []
        for seat in range(100):
            if seat not in self.pos:
                ret.append([seat//10, seat%10])

        return ret

    def _get_curr_state(self):
        state = np.array([], dtype=np.int64)
        for i in range(100):
            seat_state = [0, self.seats[i], self.obs_actions[i]]
            state = np.concatenate((state, seat_state))

        return state

    def _get_agent_obs(self):
        obs = np.concatenate((
            [self.gossip_list[self.gossip_i]-1],
            [self.time_stamp],
            self.state,
            self.mem_buf
        ))
        # set is_neighbor bit
        hist = self.seat_id, self.pos_mem[0], self.pos_mem[1]
        for i, p in enumerate(hist):
            if p:
                for nbr in range(1,4):
                    lnbr = (p // 10 * 10) + ((p - nbr) % 10)
                    rnbr = (p // 10 * 10) + ((p + nbr) % 10)
                    obs[2 + lnbr * 3 + i * 300] = 1
                    obs[2 + rnbr * 3 + i * 300] = 1

                obs[2 + p * 3 + i * 300] = 2

        return obs


    def feedback(self, feedback):
        # print('Feedback:', feedback)
        self.feedbacks = [0, 0]
        for f in feedback:
            if f[0] == 'N':
                self.feedbacks[0] += 1
            else:
                self.feedbacks[1] += 1

    def get_gossip(self, gossip_item, gossip_talker):
        # print('Get gossip:', gossip_item, gossip_talker)
        self.gossip_list.append(gossip_item)
        self.gossip_list.sort(reverse=True)
        self.gossip_i = 0
