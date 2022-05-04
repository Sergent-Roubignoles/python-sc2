from helpers import strategy_analyser, base_identifier
from macro import economy
from sc2.bot_ai import BotAI
from sc2.ids.unit_typeid import UnitTypeId
from .early_ling_push import EarlyLingPush
from .strategy import Strategy


class OpenPoolFirst(Strategy):
    finished = False
    scout_sent = False

    async def on_step(self, bot: BotAI):
        await bot.distribute_workers()

        # Train overlords
        if bot.supply_left <= 1 and bot.already_pending(UnitTypeId.OVERLORD) == 0:
            if not bot.can_afford(UnitTypeId.OVERLORD):
                return
            bot.train(UnitTypeId.OVERLORD)

        # Get 17 drones
        if bot.supply_workers < 17:
            if not bot.can_afford(UnitTypeId.DRONE):
                return
            bot.train(UnitTypeId.DRONE)

        economy.reset_saving()
        # Tech pool first
        if bot.structures(UnitTypeId.SPAWNINGPOOL).amount + bot.already_pending(UnitTypeId.SPAWNINGPOOL) < 1:
            await economy.tech.try_build_tech(bot, UnitTypeId.SPAWNINGPOOL)
            if economy.tech.saving_money:
                return # Save for spawning pool

        # Then hatch
        if bot.townhalls.amount + bot.already_pending(UnitTypeId.HATCHERY) < 2:
            next_expansion = await bot.get_next_expansion()
            if next_expansion is not None:
                if bot.can_afford(UnitTypeId.HATCHERY):
                    # Drone scout
                    if not self.scout_sent:
                        scout = bot.workers.gathering.first
                        scout.move(bot.enemy_start_locations[0])
                        scout.move(base_identifier.enemy_natural, queue=True)
                        scout.hold_position(queue=True)
                        self.scout_sent = True
                    await bot.build(UnitTypeId.HATCHERY, next_expansion)
                else:
                    return # Save for hatchery

        # Then gas
        await economy.get_gas(bot, 1)
        if economy.saving_money:
            return # Save for gas

        # Get 1 queen
        queen_count = bot.all_own_units(UnitTypeId.QUEEN).amount + bot.already_pending(UnitTypeId.QUEEN)
        if queen_count < 1 and bot.structures(UnitTypeId.SPAWNINGPOOL).ready.amount > 0:
            if not bot.can_afford(UnitTypeId.QUEEN):
                return # Save for queen
            idle_townhalls = bot.townhalls.ready.idle
            if idle_townhalls.amount > 0:
                idle_townhalls.first.train(UnitTypeId.QUEEN)

        if bot.supply_used >= 21 and bot.all_own_units(UnitTypeId.ZERGLING).amount + bot.already_pending(UnitTypeId.ZERGLING) == 0:
            bot.train(UnitTypeId.ZERGLING)
            self.is_finished = True

    def prefered_follow_up_strategy(self) -> Strategy:
        return EarlyLingPush()