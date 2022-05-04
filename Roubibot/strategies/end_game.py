from helpers import strategy_analyser
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

    workers_desired = 60
    gas_desired = 5
    army_to_push = 40

    first_push_done = False
    current_attack_group: AttackGroup = None

    banelings_desired = False
    roaches_desired = False

    async def on_step(self, bot: BotAI):

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

        # Increase supply
        if bot.supply_left < 8 and bot.already_pending(UnitTypeId.OVERLORD) < 2:
            if not bot.can_afford(UnitTypeId.OVERLORD):
                return
            bot.train(UnitTypeId.OVERLORD)

        economy.reset_saving()

        desired_techs = [economy.tech.tech_zerglings(bot, adrenal_glands=True),
                         economy.tech.tech_broodlords(bot)]
        if self.banelings_desired:
            desired_techs.append(economy.tech.tech_banelings(bot))
        if self.roaches_desired:
            desired_techs.append(economy.tech.tech_roaches(bot))
        if bot.minerals > 700:
            desired_techs.append(economy.tech.try_build_tech(bot, UnitTypeId.EVOLUTIONCHAMBER, 2))
            desired_techs.append(economy.tech.tech_melee(bot))
            desired_techs.append(economy.tech.tech_ground_armor(bot))

        await economy.execute_tech_coroutines(bot, desired_techs)
        await economy.expand_eco(bot, self.workers_desired, self.gas_desired)
        await economy.expand_army(bot)

        # Update attack group unit list
        # if self.current_attack_group is not None:
        #     self.current_attack_group.update_attacker_list()
        #     if len(self.current_attack_group.attacker_tags) == 0:
        #         self.current_attack_group = None

        # Create attack group if army large enough
        army = bot.units.of_type(
            {UnitTypeId.ZERGLING, UnitTypeId.BANELING, UnitTypeId.ROACH, UnitTypeId.CORRUPTOR,
             UnitTypeId.BROODLORD})
        if bot.supply_army > self.army_to_push or bot.supply_used > 190:
            # if self.current_attack_group is None:
            #     new_attack_group = AttackGroup()
            #     for unit in army:
            #         new_attack_group.attacker_tags.append(unit.tag)
            #
            #     self.current_attack_group = new_attack_group

            targets = bot.enemy_structures
            chosen_target: Point2 = None
            if targets.amount > 0:
                chosen_target = targets.closest_to(bot.game_info.map_center).position

            for unit in army.idle:
                if chosen_target is not None:
                    unit.attack(chosen_target)
                unit.attack(bot.enemy_start_locations[0], queue=True)

            # Increase workers and army desired
            self.workers_desired += 10
            if self.workers_desired > 90:
                self.workers_desired = 90
            self.gas_desired += 1
            if self.gas_desired > 8:
                self.gas_desired = 8
            self.army_to_push += 30

        # Update attack group target
        # if self.current_attack_group is not None:
        #     targets = bot.enemy_structures
        #     chosen_target: Point2
        #     if targets.amount > 0:
        #         chosen_target = targets.closest_to(bot.game_info.map_center).position
        #     else:
        #         chosen_target = bot.enemy_start_locations[0]
        #
        #     self.current_attack_group.target = chosen_target
        #     self.current_attack_group.attack()

        # Move remaining units to staging point
        staging_point = bot.townhalls.closest_to(bot.enemy_start_locations[0]).position.towards(
            bot.game_info.map_center,
            10)
        for unit in army.idle:
            if unit.distance_to(staging_point) > 10:
                unit.move(staging_point)
