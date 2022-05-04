from typing import List

from sc2.bot_ai import BotAI
from sc2.position import Point2

player_spawn: Point2

enemy_spawn: Point2
enemy_natural: Point2
enemy_3rd: List[Point2]

# Determines which base is the natural, 3rd, 4th and so on

def identify_bases(bot: BotAI):
    global player_spawn
    player_spawn = bot.start_location
    global enemy_spawn
    enemy_spawn = bot.enemy_start_locations[0]

    global enemy_natural
    global enemy_3rd

    # Find enemy natural expansion
    expansion_locations: List[Point2] = bot.expansion_locations_list
    closest_to_enemy_spawn = bot.start_location
    for base_location in expansion_locations:
        if base_location.distance_to(enemy_spawn) == 0:
            continue
        if base_location.distance_to(enemy_spawn) < closest_to_enemy_spawn.distance_to(enemy_spawn):
            closest_to_enemy_spawn = base_location
    enemy_natural = closest_to_enemy_spawn

    # Find enemy 3rd bases
    enemy_3rd = []
    for base_location in expansion_locations:
        # Exclude enemy 1st and 2nd base
        if base_location.distance_to(enemy_spawn) != 0 and base_location.distance_to(enemy_natural) != 0:
            if len(enemy_3rd) < 2:
                enemy_3rd.append(base_location)
            else:
                if base_location.distance_to(enemy_natural) < base_location.distance_to(enemy_3rd[0]):
                    enemy_3rd[0] = base_location

            # Keep furthest base at index 0
            if len(enemy_3rd) >= 2:
                if enemy_3rd[0].distance_to(enemy_natural) < enemy_3rd[1].distance_to(enemy_natural):
                    temp = enemy_3rd[0]
                    enemy_3rd[0] = enemy_3rd[1]
                    enemy_3rd[1] = temp