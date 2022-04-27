from typing import List

from . import base_identifier
from sc2.bot_ai import BotAI
from sc2.ids.unit_typeid import UnitTypeId
from sc2.position import Point2

BaseIdentifier = base_identifier.BaseIdentifier()
entry_point: Point2

def find_entry_point(bot: BotAI):
    BaseIdentifier.identify_bases(bot)

    x_distance_to_natural = abs(BaseIdentifier.enemy_spawn.x - BaseIdentifier.enemy_natural.x)
    y_distance_to_natural = abs(BaseIdentifier.enemy_spawn.y - BaseIdentifier.enemy_natural.y)
    vector: Point2
    if x_distance_to_natural > y_distance_to_natural:
        # Approach from y axis
        if BaseIdentifier.enemy_spawn.y > bot.game_info.map_center.y:
            # Approach base from below
            vector = Point2((0, -1))
        else:
            # Approach base from above
            vector = Point2((0, 1))
    else:
        # Approach from x axis
        if BaseIdentifier.enemy_spawn.x > bot.game_info.map_center.x:
            # Approach base from left
            vector = Point2((-1, 0))
        else:
            # Approach base from right
            vector = Point2((1, 0))

    global entry_point
    entry_point = Point2((BaseIdentifier.enemy_spawn.x + 40 * vector.x, BaseIdentifier.enemy_spawn.y + 40 * vector.y))


overlord_tag: int = 0

def move_overlord(bot: BotAI):
    global overlord_tag
    try:
        overlord = bot.all_own_units.by_tag(overlord_tag)
        if overlord.distance_to(entry_point) > 5:
            overlord.move(entry_point)
    except KeyError:
        idle_overlords = bot.all_own_units(UnitTypeId.OVERLORD).idle
        if idle_overlords.amount > 0:
            overlord_tag = idle_overlords.first.tag