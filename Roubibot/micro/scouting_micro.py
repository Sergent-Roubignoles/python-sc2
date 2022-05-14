from helpers import base_identifier
from sc2.bot_ai import BotAI
from sc2.ids.unit_typeid import UnitTypeId
from sc2.position import Point2

ling_watchtower_pairs = {} # Dict with ling_tag: target_tower_tag

def secure_watchtowers(bot: BotAI):
    # Get lings that are still alive
    watchtower_lings = []
    ling_tags_to_remove = []
    for tag in ling_watchtower_pairs.keys():
        try:
            ling = bot.units.by_tag(tag)
            watchtower_lings.append(ling)
        except KeyError:
            ling_tags_to_remove.append(tag)
    for tag in ling_tags_to_remove:
        ling_watchtower_pairs.pop(tag)

    # Add 1 scout ling if necessary
    watchtowers = bot.watchtowers
    if len(ling_watchtower_pairs.keys()) < len(watchtowers):
        idle_lings = bot.units(UnitTypeId.ZERGLING).idle
        if idle_lings.amount > 0:
            ling_watchtower_pairs[idle_lings.first.tag] = None

    # Get untargeted towers
    for tower in watchtowers:
        if tower.tag not in ling_watchtower_pairs.values():
            # Assign tower to ling with no target
            for ling in ling_watchtower_pairs.keys():
                if ling_watchtower_pairs[ling] is None:
                    ling_watchtower_pairs[ling] = tower.tag
                    break

    # Move lings
    for ling in watchtower_lings:
        if ling.is_idle:
            target_tower_tag = ling_watchtower_pairs[ling.tag]
            if target_tower_tag is not None:
                try:
                    target_tower = watchtowers.by_tag(target_tower_tag)
                    ling.move(target_tower.position)
                    ling.hold_position(queue=True)
                except KeyError:
                    pass

def move_overlords(bot: BotAI):
    for base_location in bot.expansion_locations_list:
        # TODO
        pass