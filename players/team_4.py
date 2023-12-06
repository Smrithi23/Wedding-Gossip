import random
import math

class Player():
    def __init__(self, id, team_num, table_num, seat_num, unique_gossip, color, turns):
        self.id = id
        self.team_num = team_num
        self.table_num = table_num
        self.seat_num = seat_num
        self.color = color
        self.unique_gossip = unique_gossip
        self.gossip_list = [unique_gossip]
        self.group_score = 0
        self.individual_score = 0
        self.turn_num = -1
        self.player_positions = []
        self.player_actions = []
        self.turns = turns


    def observe_before_turn(self, player_positions):
        '''At the beginning of a turn, players should be told who is sitting where, so that they can use that info to decide if/where to move'''
        self.player_positions = player_positions # list of lists, each of which is [player_id, table_num, seat_num]

    def observe_after_turn(self, player_actions):
        '''At the end of a turn, players should be told what everybody at their current table (who was there at the start of the turn) did (i.e., talked/listened in what direction, or moved)'''
        self.player_actions = player_actions # list of lists, each of which is [player_id, action_type, direction] (CCW = right, CW = left)

    def _get_command(self):
        '''Returns 'talk', 'listen', or 'move'.'''
        # TODO: Change default behavior seen below to specifications in Brainstorming doc (Stephen)
        if random.random() < 0.12:
            return 'move'
        
        talk_or_listen_prob = random.random()
        highest_gossip_prob = max(self.gossip_list) / 90 

        if talk_or_listen_prob <= 0.5:
            return 'talk'
        else:
            return 'listen'
    
    def _get_direction(self, command):
        '''Returns 'left' or 'right' for the given command (which must be 'talk' or 'listen').'''
        if self.turn_num % 2 == 0:
            if command == 'talk':
                return 'right'
            elif command == 'listen':
                return 'left'
        else:
            if command == 'talk':
                return 'left'
            elif command == 'listen':
                return 'right'
    
    def _get_gossip(self):
        '''Returns the gossip number we want to say.'''
        # desired_gossip = 90
        # desired_gossip = 90 - 89 / self.turns * self.turn_num
        desired_gossip = 89 / math.log(self.turns + 1) * math.log(self.turns - self.turn_num + 1) + 1
        return min(self.gossip_list, key=lambda gossip: abs(gossip - desired_gossip))
    
    def _get_seats(self):
        '''Returns an ordered list of empty seats to move to in the form [[table1, seat1], [table2, seat2], ...].'''
        # TODO: Change default behavior seen below to specifications in Brainstorming doc (Cristopher)
        OccupiedSeats = [[item[1], item[2]] for item in self.player_positions]
        EmptySeats = []
        for table_num in range(10):
            for seat_num in range(10):
                seat = [table_num, seat_num]
                if seat not in OccupiedSeats:
                    EmptySeats.append([table_num, seat_num])

        random.shuffle(EmptySeats) #Shuffling the list of empty seats to randomize the order of the seats to remove bias.

        #Sorting based on the seats with neighbors
        temp1 =[]
        temp2 =[]
        temp3 =[]
        for seat in EmptySeats:
            if [seat[0], seat[1] + 1] not in EmptySeats and [seat[0], seat[1] - 1] not in EmptySeats and (seat[1]+1 in range(1, 10) or seat[1]-1 in range(1, 10)):
                #If the seat has neighbors on both sides
                temp1.append(seat)
            elif ( [seat[0], seat[1] + 1] not in EmptySeats or [seat[0], seat[1] - 1] not in EmptySeats ) and (seat[1]+1 in range(1, 10) or seat[1]-1 in range(1, 10)):
                #If the seat has neighbors on one side
                temp2.append(seat) 
            else:
                #If the seat has no neighbors
                temp3.append(seat)
        
        priority_EmptySeats = temp1 + temp2 + temp3
        #print("Empty Seats: ", EmptySeats)
        #print("Priority EmptySeats: ", priority_EmptySeats)

        return priority_EmptySeats


    def get_action(self):
        '''
        Returns one of the following forms:
        - 'talk', 'left', <gossip_number>
        - 'talk', 'right', <gossip_number>
        - 'listen', 'left'
        - 'listen', 'right'
        - 'move', priority_list: [[table number, seat number] ...]
        '''
        self.turn_num += 1
        command = self._get_command()
        if command == 'talk':
            return command, self._get_direction(command), self._get_gossip()
        elif command == 'listen':
            return command, self._get_direction(command)
        elif command == 'move':
            return command, self._get_seats()
    
    def feedback(self, feedback):
        '''Respond to feedback from a person we talked to.'''
        pass

    def get_gossip(self, gossip_item, gossip_talker):
        '''Respond to gossip told to us.'''
        pass
        if gossip_item not in self.gossip_list:
            self.gossip_list.append(gossip_item)
