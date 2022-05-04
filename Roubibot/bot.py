import random
from typing import List

from helpers import strategy_analyser, base_identifier
from micro import queen_micro, base_defense_micro
from sc2.bot_ai import BotAI
from sc2.ids.unit_typeid import UnitTypeId
from sc2.position import Point2
from strategies.open_pool_first import OpenPoolFirst


class CompetitiveBot(BotAI):

    current_strategy = OpenPoolFirst()

    async def on_start(self):
        print("Game started")
        base_identifier.identify_bases(self)

    async def on_step(self, iteration):
        if iteration == 0:
            await self.chat_send("glhf")

        if self.townhalls.amount > 0 and self.workers.amount > 0:
            # Main code
            await strategy_analyser.update_unit_list(self)

            if self.current_strategy.is_finished:
                self.current_strategy = self.current_strategy.prefered_follow_up_strategy()
            await self.current_strategy.on_step(self)

            base_defense_micro.emergency_response(self)
            queen_micro.inject_and_creep_spread(self, iteration)
            move_scout(self)

    def on_end(self, result):
        print("Game ended.")

    async def on_unit_destroyed(self, unit_tag: int):
        strategy_analyser.on_unit_destroyed(unit_tag)

scout_id: int = 0

def move_scout(bot: BotAI):
    global scout_id
    position_to_scout: Point2

    try:
        scout = bot.units.by_tag(scout_id)
        if scout.is_idle:
            expansions: List[Point2] = bot.expansion_locations_list
            random.shuffle(expansions)
            scout.move(expansions[0].position)
    except KeyError:
        idle_lings = bot.units(UnitTypeId.ZERGLING).idle
        if idle_lings.amount > 0:
            scout_id = idle_lings.first.tag