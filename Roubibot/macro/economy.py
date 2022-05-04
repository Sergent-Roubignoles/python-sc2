from typing import List, Coroutine

from macro import tech
from sc2.bot_ai import BotAI
from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId

saving_money = False

async def expand_eco(bot: BotAI, desired_workers: int, desired_gas: int):
    await bot.distribute_workers()

    global saving_money

    # Build more hatcheries
    exploitable_mineral_fields = []
    for mineral_field in bot.mineral_field:
        for hatchery in bot.townhalls.ready:
            if mineral_field.distance_to(hatchery) < 10:
                exploitable_mineral_fields.append(mineral_field)

    desired_mineral_fields = (desired_workers - 3 * desired_gas) / 2
    if len(exploitable_mineral_fields) < desired_mineral_fields:
        if not bot.already_pending(UnitTypeId.HATCHERY):
            next_expansion = await bot.get_next_expansion()
            if next_expansion is not None:
                if bot.can_afford(UnitTypeId.HATCHERY):
                    await bot.build(UnitTypeId.HATCHERY, next_expansion)
                else:
                    saving_money = True
                    return # Save for hatchery

    # Build more extractors
    await get_gas(bot, desired_gas)

    # Build minimum queens
    current_queens = bot.units(UnitTypeId.QUEEN).amount + bot.already_pending(UnitTypeId.QUEEN)
    desired_queens = bot.townhalls.amount * 1.5
    if current_queens < desired_queens:
        if not bot.can_afford(UnitTypeId.QUEEN) or bot.structures(UnitTypeId.SPAWNINGPOOL).ready.amount == 0:
            saving_money = True
            return # Save or wait for spawning pool
        idle_townhalls = bot.townhalls.ready.idle
        if idle_townhalls.amount > 0:
            idle_townhalls.random.train(UnitTypeId.QUEEN)

    # Build more drones
    current_workers = int(bot.supply_workers + bot.already_pending(UnitTypeId.DRONE))
    if current_workers < desired_workers and bot.can_afford(UnitTypeId.DRONE):
        bot.train(UnitTypeId.DRONE)

    # Get 1 extra hatchery if floating minerals
    if bot.minerals > 700 and not bot.already_pending(UnitTypeId.HATCHERY):
        extra_mineral_fields = desired_mineral_fields - len(exploitable_mineral_fields)
        if not extra_mineral_fields >= 8:
            next_expansion = await bot.get_next_expansion()
            if next_expansion is not None:
                if bot.can_afford(UnitTypeId.HATCHERY):
                    await bot.build(UnitTypeId.HATCHERY, next_expansion)

async def get_gas(bot: BotAI, desired_gas: int):
    global saving_money

    exploitable_extractors = bot.gas_buildings.filter(lambda unit: unit.has_vespene)
    if exploitable_extractors.amount + bot.already_pending(UnitTypeId.EXTRACTOR) < desired_gas:
        unexploited_geysers = []
        for geyser in bot.vespene_geyser:
            for hatchery in bot.townhalls.ready:
                if geyser.distance_to(hatchery) < 10:
                    unexploited_geysers.append(geyser)
                    continue
        if len(unexploited_geysers) > 0:
            target_geyser = unexploited_geysers[0]
            if bot.can_afford(UnitTypeId.EXTRACTOR):
                bot.workers.closest_to(target_geyser).build_gas(target_geyser)
            else:
                saving_money = True
                return # Save for extractor

async def expand_army(bot: BotAI):
    if bot.supply_used == 200:
        return

    global saving_money

    # Ultralisks
    if not saving_money and bot.structures(UnitTypeId.ULTRALISKCAVERN).ready.amount > 0:
        ultralisks = bot.units(UnitTypeId.ULTRALISK).amount + bot.already_pending(UnitTypeId.ULTRALISK)
        if ultralisks * 6 < 0.15 * bot.supply_army:
            if bot.can_afford(UnitTypeId.ULTRALISK):
                bot.train(UnitTypeId.ULTRALISK)
            else:
                saving_money = True

    # Broodlords
    if not saving_money and bot.structures(UnitTypeId.GREATERSPIRE).ready.amount > 0:
        corruptors = bot.units(UnitTypeId.CORRUPTOR)
        if corruptors.amount > 1:
            if bot.can_afford(UnitTypeId.BROODLORD):
                corruptors.first(AbilityId.MORPHTOBROODLORD_BROODLORD)
            else:
                saving_money = True

    # Corruptors
    if not saving_money and bot.structures({UnitTypeId.SPIRE, UnitTypeId.GREATERSPIRE}).ready.amount > 0:
        corruptor_count = bot.units(UnitTypeId.CORRUPTOR).amount + bot.already_pending(UnitTypeId.CORRUPTOR)
        broodlord_count = bot.units(UnitTypeId.BROODLORD).amount + bot.already_pending(UnitTypeId.BROODLORD)
        if (corruptor_count + broodlord_count) * 4 < 0.33 * bot.supply_army:
            if bot.can_afford(UnitTypeId.CORRUPTOR):
                bot.train(UnitTypeId.CORRUPTOR)
            else:
                saving_money = True

    # Banelings
    if not saving_money and bot.structures(UnitTypeId.BANELINGNEST).ready.amount > 0:
        zerglings = bot.units(UnitTypeId.ZERGLING)
        # Keep 66/33 ling-bane ratio
        if bot.can_afford(UnitTypeId.BANELING) and zerglings.amount > 2 *bot.units({UnitTypeId.BANELING, UnitTypeId.BANELINGCOCOON}).amount:
            zerglings.closest_to(bot.start_location)(AbilityId.MORPHZERGLINGTOBANELING_BANELING)

    # Roaches
    if not saving_money and bot.structures(UnitTypeId.ROACHWARREN).ready.amount > 0:
        if bot.can_afford(UnitTypeId.ROACH):
            bot.train(UnitTypeId.ROACH)

    # Zerglings
    if not saving_money:
        bot.train(UnitTypeId.ZERGLING)

async def execute_tech_coroutines(bot: BotAI, techs: List[Coroutine]):
    tech.saving_money = False

    for coroutine in techs:
        await coroutine

def reset_saving():
    global saving_money
    saving_money = False
    tech.saving_money = False