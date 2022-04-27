from typing import List
from sc2.bot_ai import BotAI
from sc2.ids.unit_typeid import UnitTypeId
from sc2.position import Point2

# Determines which base is the natural, 3rd, 4th and so on
class BaseIdentifier:
    player_spawn: Point2

    enemy_spawn: Point2
    enemy_natural: Point2
    enemy_3rd: List[Point2]

    def identify_bases(self, bot: BotAI):
        self.player_spawn = bot.start_location

        self.enemy_spawn = bot.enemy_start_locations[0]

        # Find enemy natural expansion
        expansion_locations: List[Point2] = bot.expansion_locations_list
        closest_to_enemy_spawn = bot.start_location
        for base_location in expansion_locations:
            if base_location.distance_to(self.enemy_spawn) == 0:
                continue
            if base_location.distance_to(self.enemy_spawn) < closest_to_enemy_spawn.distance_to(self.enemy_spawn):
                closest_to_enemy_spawn = base_location
        self.enemy_natural = closest_to_enemy_spawn

        # Find enemy 3rd bases
        self.enemy_3rd = []
        for base_location in expansion_locations:
            # Exclude enemy 1st and 2nd base
            if base_location.distance_to(self.enemy_spawn) != 0 and base_location.distance_to(self.enemy_natural) != 0:
                if len(self.enemy_3rd) < 2:
                    self.enemy_3rd.append(base_location)
                else:
                    if base_location.distance_to(self.enemy_natural) < base_location.distance_to(self.enemy_3rd[0]):
                        self.enemy_3rd[0] = base_location

                # Keep furthest base at index 0
                if len(self.enemy_3rd) >= 2:
                    if self.enemy_3rd[0].distance_to(self.enemy_natural) < self.enemy_3rd[1].distance_to(self.enemy_natural):
                        temp = self.enemy_3rd[0]
                        self.enemy_3rd[0] = self.enemy_3rd[1]
                        self.enemy_3rd[1] = temp