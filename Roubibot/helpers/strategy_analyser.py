from sc2.unit import Unit
from sc2.bot_ai import BotAI
from sc2.ids.unit_typeid import UnitTypeId
from sc2.position import Point2

harmless_units = [UnitTypeId.SCV, UnitTypeId.MULE, UnitTypeId.DRONE,
                  UnitTypeId.EGG, UnitTypeId.OVERLORD, UnitTypeId.OVERSEER, UnitTypeId.QUEEN, UnitTypeId.LARVA,
                  UnitTypeId.PROBE, UnitTypeId.OBSERVER]
allied_unit_dictionary = {}
known_enemy_unit_dictionary = {}

async def update_unit_list(bot: BotAI):

    global allied_unit_dictionary
    for unit in bot.units:
        if unit.type_id != UnitTypeId.EGG:
            allied_unit_dictionary[unit.tag] = unit

    global known_enemy_unit_dictionary
    for unit in bot.enemy_units:
        known_enemy_unit_dictionary[unit.tag] = unit

def get_known_enemy_units() -> list[Unit]:
    known_enemy_units: list[Unit] = []
    for unit in known_enemy_unit_dictionary.values():
        known_enemy_units.append(unit)
    return known_enemy_units

def on_unit_destroyed(unit_tag: int):
    if unit_tag in allied_unit_dictionary:
        del allied_unit_dictionary[unit_tag]
    if unit_tag in known_enemy_unit_dictionary:
        del known_enemy_unit_dictionary[unit_tag]
