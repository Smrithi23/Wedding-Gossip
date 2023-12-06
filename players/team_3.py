import random
from queue import PriorityQueue

#maintian memory of actions we did to other players, dictionary
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
        self.turns = 0
        self.totalTurns = turns

        self.priorityGossip = PriorityQueue()
        self.priorityGossip.put(self.unique_gossip)
        
        self.currGossip = unique_gossip #the highest gossip we currently have
        self.prevGossip = unique_gossip #the gossip we start with or the highest gossip we got from the prev table
        self.heardPlayers = [] #players we have heard from
        self.move = False  #are we moving this turn
        self.prevTable = table_num #the table we were just at
        self.emptySeats = [] #the current empty seats, updated every turn at _turn()
        self.uniquePlayerSeed = random.randint(1, 9) # we will have 9 distinct player types

        self.memory = {} #Dictionary to store all interactions with other players
        self.player_positions = [] #Store received player positions
        self.count = 0

        #add in memory (dictionary, key: player id, array: list of actions ("listen/speak", "gossip value")

    # At the beginning of a turn, players should be told who is sitting where, so that they can use that info to decide if/where to move
    def observe_before_turn(self, player_positions):
        heardPlayers = 0
        self.player_positions = player_positions

        #if we are trying to move, see if we did actually move on the prev turn
        if self.move:
            if self.prevTable != self.table_num:
                self.move = False
                self.prevTable = self.table_num

        #see how many players at the current table we have already heard from
        for player in player_positions:
            player_id = player[0]
            table_num = player[1]
            if table_num == self.table_num:
                if player_id in self.heardPlayers:
                    heardPlayers += 1
        if heardPlayers > 5: 
            self.move = True


        self.emptySeats = self._emptySeats(player_positions)
        pass

    def get_player(self, seat, table):
        for player in self.player_positions:
            if player[1]==table and player[2]==seat :
                return player[0]

    def _emptySeats(self, player_positions):
        playerSeats = [[position[1], position[2]] for position in player_positions]
        emptySeats = []
        for table in range(0, 10):
            for seat in range(0, 10):
                currSeat = [table, seat]
                if currSeat not in playerSeats:
                    emptySeats.append([table, seat])
        return emptySeats

    # At the end of a turn, players should be told what everybody at their current table (who was there at the start of the turn)
    # did (i.e., talked/listened in what direction, or moved)
    def observe_after_turn(self, player_actions):
        pass

    def add_to_memory(self, key, value):
        if key in self.memory:
            # Check if tuple x already exists in the list for key y
            if value not in self.memory[key]:
                # If x is not in the list, append it
                self.memory[key].append(value)
        else:
            # If key y is not in memory, create a new entry with x as the first element of the list
            self.memory[key] = [value]


    def get_action(self):
        # return 'talk', 'left', <gossip_number>
        # return 'talk', 'right', <gossip_number>
        # return 'listen', 'left', 
        # return 'listen', 'right', 
        # return 'move', priority_list: [[table number, seat number] ...]
        self.turns+=1
        direction = random.randint(0, 1)

        #DEBUG memory & number of times we listen
        # if self.turns == self.totalTurns and self.uniquePlayerSeed==7:
        #     print(self.memory)
        #     print("count: "+(str)(self.count))

        #move every x turns or when your new gossip is 20 greater than previous gossip maximum
        if self.turns % (self.uniquePlayerSeed+5) == 0 or (self.currGossip-self.prevGossip) > 19 or self.move:
            self.prevGossip = self.currGossip
            # if self.uniquePlayerSeed==7:
            #     print("move")
            return 'move', self.emptySeats

        # talk
        if self.currGossip/90 > random.random():

            #get random gossip from the top 3 highest gossip
            maxGossipRange = 2 if self.priorityGossip.qsize() > 2 else 0
            gossipNum = random.randint(0, maxGossipRange)
            gossip = self.priorityGossip.queue[gossipNum]

            # left
            if direction == 0:
                if self.seat_num==0 :
                    seat = 9
                else:
                    seat = self.seat_num-1
                
                key = self.get_player(seat, self.table_num)
                value = ("talk", gossip)
                self.add_to_memory(key, value)

                return 'talk', 'left', gossip
            # right
            else:
                if self.seat_num==9 :
                    seat = 0
                else:
                    seat = self.seat_num+1
                
                key = self.get_player(seat, self.table_num)
                value = ("talk", gossip)
                self.add_to_memory(key, value)

                return 'talk', 'right', gossip
        
        # listen
        else:
            # left
            self.count+=1
            if direction == 0:
                return 'listen', 'left'
            # right
            else:
                return 'listen', 'right'
    
    def feedback(self, feedback):
        pass

    def get_gossip(self, gossip_item, gossip_talker):
        self.gossip_list.append(gossip_item)

        #Save to memory
        value = ( "listen", gossip_item)
        self.add_to_memory(gossip_talker, value)

        self.priorityGossip.put(gossip_item)
        self.heardPlayers.append(gossip_talker)
        self.currGossip = self.priorityGossip.queue[0]

        pass
    