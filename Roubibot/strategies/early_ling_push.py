import random

from helpers import base_identifier, strategy_analyser
from macro import economy
from sc2.bot_ai import BotAI
from sc2.ids.unit_typeid import UnitTypeId
from strategies.end_game import EndGame
from strategies.strategy import Strategy


def current_plus_pending_count(bot: BotAI, unit_id: UnitTypeId):
    return int(bot.units.of_type(unit_id).amount + bot.already_pending(unit_id))


class EarlyLingPush(Strategy):

    warning_printed = False

    async def on_step(self, bot: BotAI):
        # Increase supply
        if bot.supply_left < 8 and bot.already_pending(UnitTypeId.OVERLORD) == 0:
            if not bot.can_afford(UnitTypeId.OVERLORD):
                return
            bot.train(UnitTypeId.OVERLORD)

        # Spot early aggression
        known_enemy_units = strategy_analyser.get_known_enemy_units()
        enemy_army_value = 0
        for enemy in known_enemy_units:
            if enemy.type_id in strategy_analyser.harmless_units:
                continue
            enemy_value = bot.calculate_unit_value(enemy.type_id)
            enemy_army_value += enemy_value.minerals
            enemy_army_value += enemy_value.vespene

        own_army_value = 0
        for unit in bot.units.exclude_type([UnitTypeId.DRONE, UnitTypeId.OVERLORD]):
            unit_value = bot.calculate_unit_value(unit.type_id)
            own_army_value += unit_value.minerals
            own_army_value += unit_value.vespene

        if not self.warning_printed:
            if enemy_army_value > 200 and enemy_army_value > 3 * own_army_value:
                await bot.chat_send("Enemy army value is {0}, defend the base!".format(enemy_army_value))
                self.warning_printed = True

        desired_techs = [economy.tech.tech_zerglings(bot, False)]
        await economy.execute_tech_coroutines(bot, desired_techs)
        await economy.expand_eco(bot, 35, 1)

        bot.train(UnitTypeId.ZERGLING, int(bot.supply_left))

        if bot.units(UnitTypeId.ZERGLING).amount > 15:
            target_base = base_identifier.enemy_3rd[random.randint(0, 1)]
            for ling in bot.units(UnitTypeId.ZERGLING).idle:
                ling.attack(target_base)
                ling.attack(bot.enemy_start_locations[0], queue=True)
            self.is_finished = True
        else:
            for unit in bot.units(UnitTypeId.ZERGLING).idle:
                unit.move(
                    bot.townhalls.closest_to(bot.enemy_start_locations[0]).position.towards(bot.game_info.map_center,
                                                                                              10))

    def prefered_follow_up_strategy(self) -> Strategy:
        return EndGame()