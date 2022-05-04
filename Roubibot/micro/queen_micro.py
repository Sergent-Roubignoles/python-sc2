import random

import numpy as np

from sc2.bot_ai import BotAI
from sc2.ids.ability_id import AbilityId
from sc2.ids.buff_id import BuffId
from sc2.ids.unit_typeid import UnitTypeId
from sc2.position import Point2


def inject_and_creep_spread(bot: BotAI, iteration: int):
    unreserved_queens = bot.units(UnitTypeId.QUEEN)

    # Keep 1 immobile queen for each hatch
    for hatchery in bot.townhalls.ready:
        reservable_queens = unreserved_queens.filter(lambda unit: not unit.is_moving).closer_than(5, hatchery)
        if reservable_queens.amount > 0:
            queen_to_reserve = reservable_queens.closest_to(hatchery)
            unreserved_queens.remove(queen_to_reserve)

    # Inject
    for hatchery in bot.townhalls.ready:
        if not hatchery.has_buff(BuffId.QUEENSPAWNLARVATIMER):
            # Try inject with nearby queen
            nearby_queens = bot.units(UnitTypeId.QUEEN).idle.filter(lambda unit: unit.energy >= 25).closer_than(5, hatchery)
            if nearby_queens.amount > 0:
                closest_queen = nearby_queens.closest_to(hatchery)
                closest_queen(AbilityId.EFFECT_INJECTLARVA, hatchery)
            else:
                # Call unreserved queen for inject
                available_queens = unreserved_queens.idle.filter(lambda unit: unit.energy >= 25)
                if available_queens.amount > 0:
                    closest_queen = available_queens.closest_to(hatchery)
                    closest_queen(AbilityId.EFFECT_INJECTLARVA, hatchery)

    # Spread creep
    if iteration % 100 == 0:
        borders_of_creep = []
        for point in get_whole_map(bot):
            if is_border_of_creep(bot, point):
                for base_location in bot.expansion_locations_list: # Do not spread on base locations
                    if point.distance_to(base_location) < 8:
                        continue
                borders_of_creep.append(point)
        random.shuffle(borders_of_creep)

        for queen in unreserved_queens.idle.filter(lambda unit: unit.energy >= 25):
            while len(borders_of_creep) > 0:
                target = borders_of_creep.pop()
                target_is_safe = True
                for structure in bot.enemy_structures: # Do not bring queens close to enemy base
                    if target.distance_to(structure) < 20:
                        target_is_safe = False
                        break
                if target_is_safe:
                    queen(AbilityId.BUILD_CREEPTUMOR_QUEEN, target)
                    break

        tumors = bot.structures(UnitTypeId.CREEPTUMORBURROWED)
        for tumor in tumors:
            if len(borders_of_creep) > 0:
                for tile in borders_of_creep:
                    if tumor.distance_to(tile) <= tumor.sight_range:
                        tumor(AbilityId.BUILD_CREEPTUMOR_TUMOR, tile)
                        break


def is_border_of_creep(bot: BotAI, position: Point2):
    if bot.has_creep(position):
        for neighbor_tile in position.neighbors8:
            if not bot.has_creep(neighbor_tile) and bot.in_placement_grid(neighbor_tile):
                return True
    return False


def get_whole_map(bot: BotAI):
    map_area = bot.game_info.playable_area
    points = [
        Point2((a, b)) for (b, a), value in np.ndenumerate(bot.game_info.pathing_grid.data_numpy)
        if value == 1 and map_area.x <= a < map_area.x + map_area.width and map_area.y <= b < map_area.y + map_area.height
    ]
    return points
