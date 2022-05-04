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
    aggression_detected = False

    async def on_step(self, bot: BotAI):
        # Increase supply
        if bot.supply_left < 8 and bot.already_pending(UnitTypeId.OVERLORD) == 0:
            if not bot.can_afford(UnitTypeId.OVERLORD):
                return
            bot.train(UnitTypeId.OVERLORD)

        # Look for early aggression
        if not self.aggression_detected:
            for second_base in bot.townhalls.not_ready:
                if second_base.build_progress > 0.80:
                    enemy_townhalls = bot.enemy_structures({UnitTypeId.HATCHERY, UnitTypeId.NEXUS, UnitTypeId.COMMANDCENTER})
                    if enemy_townhalls.amount < 2:
                        self.aggression_detected = True
                        await bot.chat_send("No enemy expansion detected yet: defend the base!")
                    break

        desired_techs = [economy.tech.tech_zerglings(bot, False)]
        await economy.execute_tech_coroutines(bot, desired_techs)

        if self.aggression_detected:
            saving_money_for_defense = False
            if bot.structures(UnitTypeId.SPAWNINGPOOL).ready.amount > 0:

                # Get 2 spines on b2
                if bot.townhalls.ready.amount > 1:
                    if bot.structures(UnitTypeId.SPINECRAWLER).amount + bot.already_pending(UnitTypeId.SPINECRAWLER) < 2:
                        if bot.can_afford(UnitTypeId.SPINECRAWLER):
                            second_base = bot.townhalls.closest_to(bot.game_info.map_center)
                            await bot.build(UnitTypeId.SPINECRAWLER, second_base.position.towards(bot.game_info.map_center, 3))
                        else:
                            saving_money_for_defense = True

                # Get 4 queens
                if bot.units(UnitTypeId.QUEEN).amount + bot.already_pending(UnitTypeId.QUEEN) < 4:
                    idle_hatcheries = bot.townhalls.idle
                    if idle_hatcheries.amount > 0:
                        if bot.can_afford(UnitTypeId.QUEEN):
                            idle_hatcheries.first.train(UnitTypeId.QUEEN)
                        else:
                            saving_money_for_defense = True

                # Get 8 zerglings
                if bot.units(UnitTypeId.ZERGLING).amount + bot.already_pending(UnitTypeId.ZERGLING) < 8:
                    bot.train(UnitTypeId.ZERGLING)

            if not saving_money_for_defense:
                await economy.expand_eco(bot, 19, 1)

        await economy.expand_eco(bot, 35, 1)
        bot.train(UnitTypeId.ZERGLING, int(bot.supply_left))

        if bot.units(UnitTypeId.ZERGLING).amount > 10:
            target_bases = base_identifier.enemy_3rd
            for ling in bot.units(UnitTypeId.ZERGLING).idle:
                ling.attack(target_bases[0])
                ling.attack(target_bases[1], queue=True)
            self.is_finished = True
        else:
            for unit in bot.units(UnitTypeId.ZERGLING).idle:
                unit.move(
                    bot.townhalls.closest_to(bot.game_info.map_center).position.towards(bot.game_info.map_center,
                                                                                              10))

    def prefered_follow_up_strategy(self) -> Strategy:
        return EndGame()