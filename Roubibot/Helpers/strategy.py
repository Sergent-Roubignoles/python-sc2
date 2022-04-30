import random
from typing import List, Coroutine

from . import queen_helper, surrender_logic, scouting, tech
from sc2.bot_ai import BotAI
from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.upgrade_id import UpgradeId
from sc2.position import Point2

worker_ids = [UnitTypeId.SCV, UnitTypeId.DRONE, UnitTypeId.PROBE]
own_units = {}
enemy_units = {}

base_under_attack = False

async def analyse(bot: BotAI):
    global base_under_attack

    global own_units
    own_units = {}
    for unit in bot.all_own_units:
        own_units[unit.tag] = unit.type_id

    global enemy_units
    enemy_units = {}
    for unit in bot.all_enemy_units:
        enemy_units[unit.tag] = unit.type_id

    if base_under_attack:
        base_under_attack = False
        for enemy_unit in bot.enemy_units:
            closest_base = bot.townhalls.closest_to(enemy_unit)
            if closest_base.distance_to(enemy_unit) < 30:
                base_under_attack = True
                break
    else:
        for enemy_unit in bot.enemy_units:
            closest_base = bot.townhalls.closest_to(enemy_unit)
            if closest_base.distance_to(enemy_unit) < 20:
                # await bot.chat_send("Enemy {0} spotted near base! ({1})".format(enemy_unit.type_id, iteration))
                base_under_attack = True
                break