import random


class Player():
    def __init__(self, id, team_num, table_num, seat_num, unique_gossip, color, turns):
        self.id = id
        self.team_num = team_num
        self.table_num = table_num
        self.seat_num = seat_num
        self.color = color
        self.unique_gossip = unique_gossip
        self.gossip_list = [Gossip(unique_gossip)]
        self.current_gossip = Gossip(unique_gossip)
        self.group_score = 0
        self.individual_score = 0

        self.consecutive_shakes = 0  # track consecutive shakes
        self.turn_number = 0  # track the turn number
        self.shake_pct = 0  # tracks the pct of shakes in the last listen
        self.latest_playerpositions = []

    # At the beginning of a turn, players should be told who is sitting where, so that they can use that info to decide if/where to move

    def observe_before_turn(self, player_positions):
        self.latest_playerpositions = player_positions

    # At the end of a turn, players should be told what everybody at their current table (who was there at the start of the turn)
    # did (i.e., talked/listened in what direction, or moved)

    def observe_after_turn(self, player_actions):
        pass

    def get_action(self):
        self.turn_number += 1

        # TODO: change so that it moves when shake pct is high
        # if self.shake_pct >= .88:
        if random.randint(0,2) == 1:
            self.shake_pct = 0  # Reset the shake count
            # Logic to move to a new seat
            priList = self.__find_empty_seat()
            return 'move', priList

        if random.randint(0,1) == 0:
            self.current_gossip = self.__get_new_gossip()
            return self.__talk()
        return self.__listen()
    
    def __find_empty_seat(self):
        '''
        currently picking a seat randomly
        '''

        occupied_seats = set()

        # Collect the occupied seats
        for player_position in self.latest_playerpositions:
            table_num, seat_num = player_position[1], player_position[2]
            occupied_seats.add((table_num, seat_num))

        empty_seats = []

        # iterate through tables and seats to find empty seats
        for table_num in range(0, 10):
            for seat_num in range(0, 10):
                if (table_num, seat_num) not in occupied_seats:
                    empty_seats.append([table_num, seat_num])

        # so that it doesn't keep trying to go to the first few tables
        random.shuffle(empty_seats)

        return empty_seats
            
    def __listen(self):
        # on even turns listen right
        if self.turn_number % 2 == 0:
            return 'listen', 'right'
        return 'listen', 'left'
            
    def __talk(self):
        # on even turns talk left
        if self.turn_number % 2 == 0:
            return 'talk', 'left', self.current_gossip.get_item()
        return 'talk', 'right', self.current_gossip.get_item()
    
    def __get_new_gossip(self):
        for gossip in self.gossip_list:
            if len(gossip.shakes) < 30:
                return gossip
        return gossip[0]

    def feedback(self, feedback):
        # log each feedback for current gossip
        nods = 0
        shakes = 0
        for response in feedback:
            # nod
            if response[0] == 'N':
                nods += 1
                self.current_gossip.add_nod(int(response[9:]), self.turn_number)
            # shake
            else:
                shakes += 1
                self.current_gossip.add_shake(int(response[11:]), self.turn_number)
        if nods == 0 and shakes == 0:
            self.shake_pct = 0
        else:
            self.shake_pct = shakes/(nods + shakes)
        if self.shake_pct == 1 and len(self.gossip_list) > 1:
            self.gossip_list.pop(0)

    def get_gossip(self, gossip_item, gossip_talker):
        gossip = self.__get_gossip(gossip_item)
        # log new gossip!
        if gossip == None:
            gossip = Gossip(gossip_item)
            gossip.add_heard(gossip_talker, self.turn_number)
            self.gossip_list.append(gossip)
            self.gossip_list.sort(key=lambda x: x.get_item(), reverse=True)
        # alter existing gossip
        else:
            gossip.add_heard(gossip_talker, self.turn_number)

    def __get_gossip(self, gossip_item):
        for gossip in self.gossip_list:
            if gossip.get_item() == gossip_item:
                return gossip

# everytime we hear gossip we store talker, item and turn we received it
# can also use this to keep track of feedback we receive for particular gossip


class Gossip():
    def __init__(self, gossip_item: int):
        self.gossip_item = gossip_item
        # which players nod their head and on what turn
        self.nods = []
        # which players shake their head and on what turn
        self.shakes = []
        # which players told us this gossip on what turn
        self.heard = []

    def get_item(self):
        return self.gossip_item

    def add_nod(self, player: int, turn: int):
        self.nods.append([player, turn])

    def add_shake(self, player: int, turn: int):
        self.shakes.append([player, turn])

    def add_heard(self, player: int, turn: int):
        self.heard.append([player, turn])
