import random
from typing import List

from . import queen_helper,surrender_logic, scouting
from sc2.bot_ai import BotAI
from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.upgrade_id import UpgradeId
from sc2.position import Point2

saving_money = False

async def try_build_tech(bot: BotAI, building_id: UnitTypeId, count = 1):
    global saving_money
    if bot.structures(building_id).amount + bot.already_pending(building_id) < count:
        if bot.can_afford(building_id):
            await bot.build(building_id, near=bot.townhalls.closest_to(bot.start_location).position.towards(
                bot.game_info.map_center, 7))
        else:
            saving_money = True

async def try_queue_research(bot: BotAI, structure_id: UnitTypeId, upgrade_id: UpgradeId):
    global saving_money
    if upgrade_id not in bot.state.upgrades:
        idle_structures = bot.structures(structure_id).idle
        if idle_structures.amount > 0:
            if bot.can_afford(upgrade_id):
                idle_structures.first.research(upgrade_id)
            else:
                saving_money = True

async def tech_lair(bot: BotAI):
    global saving_money
    if bot.structures(UnitTypeId.LAIR).amount > 0:
        return
    if bot.structures(UnitTypeId.SPAWNINGPOOL).amount > 0:
        starting_base = bot.townhalls.closest_to(bot.start_location)
        if starting_base.is_idle:
            if bot.can_afford(UnitTypeId.LAIR):
                starting_base.train(UnitTypeId.LAIR)
            else:
                saving_money = True
    else:
        await try_build_tech(bot, UnitTypeId.SPAWNINGPOOL)

def is_lair_tech_unlocked(bot: BotAI):
    return bot.structures(UnitTypeId.LAIR).ready.amount + bot.structures(UnitTypeId.HIVE).ready.amount > 0

def is_hive_tech_unlocked(bot: BotAI):
    return bot.structures(UnitTypeId.HIVE).ready.amount > 0

async def tech_hive(bot: BotAI):
    global saving_money
    if bot.structures(UnitTypeId.HIVE).amount > 0:
        return
    lairs = bot.structures(UnitTypeId.LAIR)
    if lairs.amount > 0:
        if bot.structures(UnitTypeId.INFESTATIONPIT).amount > 0:
            lair = lairs.first
            if lair.is_idle:
                if bot.can_afford(UnitTypeId.HIVE):
                    lair.train(UnitTypeId.HIVE)
                else:
                    saving_money = True
        else:
            await try_build_tech(bot, UnitTypeId.INFESTATIONPIT)
    else:
        await tech_lair(bot)

async def tech_melee(bot: BotAI):
    if UpgradeId.ZERGMELEEWEAPONSLEVEL3 not in bot.state.upgrades:
        if UpgradeId.ZERGMELEEWEAPONSLEVEL2 not in bot.state.upgrades:
            if UpgradeId.ZERGMELEEWEAPONSLEVEL1 not in bot.state.upgrades:
                await try_queue_research(bot, UnitTypeId.EVOLUTIONCHAMBER, UpgradeId.ZERGMELEEWEAPONSLEVEL1)
            else:
                if is_lair_tech_unlocked(bot):
                    await try_queue_research(bot, UnitTypeId.EVOLUTIONCHAMBER, UpgradeId.ZERGMELEEWEAPONSLEVEL2)
        else:
            if is_hive_tech_unlocked(bot):
                await try_queue_research(bot, UnitTypeId.EVOLUTIONCHAMBER, UpgradeId.ZERGMELEEWEAPONSLEVEL3)

async def tech_ground_armor(bot: BotAI):
    if UpgradeId.ZERGGROUNDARMORSLEVEL3 not in bot.state.upgrades:
        if UpgradeId.ZERGGROUNDARMORSLEVEL2 not in bot.state.upgrades:
            if UpgradeId.ZERGGROUNDARMORSLEVEL1 not in bot.state.upgrades:
                await try_queue_research(bot, UnitTypeId.EVOLUTIONCHAMBER, UpgradeId.ZERGGROUNDARMORSLEVEL1)
            else:
                if is_lair_tech_unlocked(bot):
                    await try_queue_research(bot, UnitTypeId.EVOLUTIONCHAMBER, UpgradeId.ZERGGROUNDARMORSLEVEL2)
        else:
            if is_hive_tech_unlocked(bot):
                await try_queue_research(bot, UnitTypeId.EVOLUTIONCHAMBER, UpgradeId.ZERGGROUNDARMORSLEVEL3)

async def tech_zerglings(bot: BotAI, adrenal_glands = False):
    if bot.structures(UnitTypeId.SPAWNINGPOOL).amount > 0:
        await try_queue_research(bot, UnitTypeId.SPAWNINGPOOL, UpgradeId.ZERGLINGMOVEMENTSPEED)
        if adrenal_glands:
            if is_hive_tech_unlocked(bot):
                await try_queue_research(bot, UnitTypeId.SPAWNINGPOOL, UpgradeId.ZERGLINGATTACKSPEED)
            else:
                await tech_hive(bot)
    else:
        await try_build_tech(bot, UnitTypeId.SPAWNINGPOOL)


async def tech_banelings(bot: BotAI):
    if bot.structures(UnitTypeId.BANELINGNEST).amount > 0:
        if is_lair_tech_unlocked(bot):
            await try_queue_research(bot, UnitTypeId.BANELINGNEST, UpgradeId.BANELINGSPEED)
        else:
            await tech_lair(bot)
    else:
        if bot.structures(UnitTypeId.SPAWNINGPOOL).amount > 0:
            await try_build_tech(bot, UnitTypeId.BANELINGNEST)
        else:
            await try_build_tech(bot, UnitTypeId.SPAWNINGPOOL)
