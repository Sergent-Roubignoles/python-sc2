from helpers import base_identifier
from sc2.bot_ai import BotAI
from sc2.ids.unit_typeid import UnitTypeId
from sc2.position import Point2

entry_point: Point2

def find_entry_point(bot: BotAI):
    base_identifier.identify_bases(bot)

    x_distance_to_natural = abs(base_identifier.enemy_spawn.x - base_identifier.enemy_natural.x)
    y_distance_to_natural = abs(base_identifier.enemy_spawn.y - base_identifier.enemy_natural.y)
    vector: Point2
    if x_distance_to_natural > y_distance_to_natural:
        # Approach from y axis
        if base_identifier.enemy_spawn.y > bot.game_info.map_center.y:
            # Approach base from below
            vector = Point2((0, -1))
        else:
            # Approach base from above
            vector = Point2((0, 1))
    else:
        # Approach from x axis
        if base_identifier.enemy_spawn.x > bot.game_info.map_center.x:
            # Approach base from left
            vector = Point2((-1, 0))
        else:
            # Approach base from right
            vector = Point2((1, 0))

    global entry_point
    entry_point = Point2((base_identifier.enemy_spawn.x + 40 * vector.x, base_identifier.enemy_spawn.y + 40 * vector.y))


overlord_tag: int = 0

def move_overlord(bot: BotAI):
    global overlord_tag
    try:
        overlord = bot.units.by_tag(overlord_tag)
        if overlord.distance_to(entry_point) > 5:
            overlord.move(entry_point)
    except KeyError:
        idle_overlords = bot.units(UnitTypeId.OVERLORD).idle
        if idle_overlords.amount > 0:
            overlord_tag = idle_overlords.first.tag