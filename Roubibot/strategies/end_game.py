import random

from helpers import strategy_analyser, base_identifier
from macro import economy
from micro.army_group import AttackGroup
from sc2.bot_ai import BotAI
from sc2.ids.unit_typeid import UnitTypeId
from sc2.position import Point2
from strategies.strategy import Strategy


def current_plus_pending_count(bot: BotAI, unit_id: UnitTypeId):
    return int(bot.units.of_type(unit_id).amount + bot.already_pending(unit_id))


async def try_build_tech(bot: BotAI, building_id: UnitTypeId):
    if bot.structures(building_id).amount + bot.already_pending(building_id) == 0:
        if bot.can_afford(building_id):
            await bot.build(building_id, near=bot.townhalls.closest_to(bot.start_location).position.towards(bot.game_info.map_center, 5))


class EndGame(Strategy):

    workers_desired = 70
    gas_desired = 1
    army_to_push = 100

    first_push_done = False
    current_attack_group: AttackGroup = None

    banelings_desired = False
    roaches_desired = False
    ultralisks_desired = False

    async def on_step(self, bot: BotAI):

        # Determine army composition
        known_enemy_units = strategy_analyser.get_known_enemy_units()
        if not self.banelings_desired:
            for enemy in known_enemy_units:
                if enemy.type_id in [UnitTypeId.ZERGLING, UnitTypeId.MARINE]:
                    self.banelings_desired = True
                    break
        if not self.roaches_desired:
            for enemy in known_enemy_units:
                if enemy.type_id in [UnitTypeId.ZEALOT, UnitTypeId.COLOSSUS]:
                    self.roaches_desired = True
                    break
        if not self.ultralisks_desired and bot.structures(UnitTypeId.GREATERSPIRE).ready.amount > 0:
            for enemy in known_enemy_units:
                if enemy.type_id in [UnitTypeId.MARINE]:
                    self.ultralisks_desired = True
                    break

        # Increase supply
        if bot.supply_left < 8 and bot.already_pending(UnitTypeId.OVERLORD) < 2:
            if not bot.can_afford(UnitTypeId.OVERLORD):
                return
            bot.train(UnitTypeId.OVERLORD)

        # Spend money
        economy.reset_saving()
        desired_techs = [economy.tech.tech_zerglings(bot)]

        if bot.supply_used > 50:
            self.gas_desired = 2
            if self.banelings_desired:
                desired_techs.append(economy.tech.tech_banelings(bot))
            if self.roaches_desired:
                desired_techs.append(economy.tech.tech_roaches(bot))

        if bot.supply_used > 75:
            self.gas_desired = 3
            desired_techs.append(economy.tech.tech_spire(bot))
            desired_techs.append(economy.tech.try_build_tech(bot, UnitTypeId.EVOLUTIONCHAMBER, 2))
            desired_techs.append(economy.tech.tech_melee(bot))
            desired_techs.append(economy.tech.tech_ground_armor(bot))

        if bot.supply_used > 100:
            self.gas_desired = 5
            desired_techs.append(economy.tech.tech_zerglings(bot, adrenal_glands=True))
            desired_techs.append(economy.tech.tech_broodlords(bot))
            if self.ultralisks_desired:
                desired_techs.append(economy.tech.tech_ultralisks(bot))

        await economy.execute_tech_coroutines(bot, desired_techs)

        # Keep minimum army
        if bot.supply_army * 2 < bot.supply_workers:
            await economy.expand_army(bot)

        await economy.expand_eco(bot, self.workers_desired, self.gas_desired)
        await economy.expand_army(bot)

        # Attack if army large enough
        army = bot.units.of_type(
            {UnitTypeId.ZERGLING, UnitTypeId.BANELING, UnitTypeId.ROACH, UnitTypeId.CORRUPTOR,
             UnitTypeId.BROODLORD, UnitTypeId.ULTRALISK})
        if bot.supply_army > self.army_to_push or bot.supply_used > 190:

            target_structures = bot.enemy_structures
            target_bases = base_identifier.enemy_3rd

            for unit in army.idle:
                closest_base = target_bases[0]
                if unit.distance_to(target_bases[1]) < unit.distance_to(target_bases[0]):
                    closest_base = target_bases[1]
                    
                unit.attack(closest_base.position)
                unit.attack(target_structures.closest_to(unit).position, queue=True)
                unit.attack(bot.enemy_start_locations[0].position, queue=True)

            # Increase workers and army desired
            self.workers_desired += 10
            if self.workers_desired > 90:
                self.workers_desired = 90
            self.army_to_push += 30

        # Move remaining units to staging point
        staging_point = bot.townhalls.ready.closest_to(bot.enemy_start_locations[0]).position.towards(
            bot.game_info.map_center, 2)
        for unit in army.idle:
            if unit.distance_to(staging_point) > 10:
                unit.move(staging_point)
