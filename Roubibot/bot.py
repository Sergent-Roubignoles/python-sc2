import Helpers.queen_helper
from sc2.position import Point2
from sc2.bot_ai import BotAI
import os
import sys
import random
from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.upgrade_id import UpgradeId

# sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))


class CompetitiveBot(BotAI):

    buildOrderIndex = 0

    def select_target(self) -> Point2:
        if self.enemy_structures:
            return random.choice(self.enemy_structures).position
        return self.enemy_start_locations[0]

    async def on_start(self):
        print("Game started")
        # Do things here before the game starts

    async def on_step(self, iteration):
        # Populate this function with whatever your bot should do!
        if iteration == 0:
            await self.chat_send("glhf")
        await self.bo()[self.buildOrderIndex]()
        Helpers.queen_helper.inject(self, iteration)

    def on_end(self, result):
        print("Game ended.")
        # Do things here after the game ends

    def bo(self):
        return [self.s16pool_hatch_gas, self.bo_over]

    async def s16pool_hatch_gas(self):
        if self.supply_left <= 1 and self.already_pending(UnitTypeId.OVERLORD) == 0:
            self.train(UnitTypeId.OVERLORD)
            return
        if self.supply_workers < 16:
            self.train(UnitTypeId.DRONE)
        else:
            await self.try_build_tech(UnitTypeId.SPAWNINGPOOL)
            await self.try_expand(2)
        await self.distribute_workers()

        if len(self.townhalls) + self.already_pending(UnitTypeId.HATCHERY) >= 2:
            if self.can_afford(UnitTypeId.EXTRACTOR) and len(self.gas_buildings) + self.already_pending(UnitTypeId.EXTRACTOR) < 1:
                geyser = self.vespene_geyser.closest_to(self.townhalls.first)
                self.workers.closest_to(geyser).build_gas(geyser)
                self.buildOrderIndex += 1
                # await self.chat_send("BO is over; going to 40 workers")

    async def bo_over(self):
        if self.supply_left <= 2 and self.already_pending(UnitTypeId.OVERLORD) == 0:
            if not self.can_afford(UnitTypeId.OVERLORD):
                return
            self.train(UnitTypeId.OVERLORD)
        if self.supply_left <= 4 and self.supply_used > 30 and self.already_pending(UnitTypeId.OVERLORD) == 0:
            if not self.can_afford(UnitTypeId.OVERLORD):
                return
            self.train(UnitTypeId.OVERLORD)

        await self.tech_up()

        # Build Queens
        queen_count = self.current_plus_pending_count(UnitTypeId.QUEEN)
        desired_queens = self.townhalls.amount * 2
        if queen_count < desired_queens:
            if not self.can_afford(UnitTypeId.QUEEN) or self.structures(UnitTypeId.SPAWNINGPOOL).ready.amount == 0:
                return
            idle_townhalls = self.townhalls.ready.idle
            if idle_townhalls.amount > 0:
                idle_townhalls.random.train(UnitTypeId.QUEEN)
                # await self.chat_send("Queens: {0} Desired: {1}".format(queen_count, desired_queens))

        self.research(UpgradeId.ZERGLINGMOVEMENTSPEED)
        if self.supply_workers < 40:
            self.train(UnitTypeId.DRONE, int(40 - self.supply_workers))
        await self.distribute_workers()

        self.train(UnitTypeId.ZERGLING, int(self.supply_left))

        # inject
        # for queen in self.units(UnitTypeId.QUEEN).idle:
            # queen(AbilityId.EFFECT_INJECTLARVA, self.townhalls.closest_to(queen))

        if self.units(UnitTypeId.ZERGLING).amount > 30:
            for ling in self.units(UnitTypeId.ZERGLING).idle:
                ling.attack(self.enemy_start_locations[0])
        else:
            for unit in self.units(UnitTypeId.ZERGLING).idle:
                unit.move(self.townhalls.closest_to(self.enemy_start_locations[0]).position.towards(self.game_info.map_center, 10))

        if self.minerals > 500 and self.already_pending(UnitTypeId.HATCHERY) == 0:
            next_expansion = await self.get_next_expansion()
            await self.build(UnitTypeId.HATCHERY, next_expansion)

    def current_plus_pending_count(self, unit_id: UnitTypeId):
        return int(self.units.of_type(unit_id).amount + self.already_pending(unit_id))

    async def try_build_tech(self, building_id: UnitTypeId):
        if self.structures(building_id).amount + self.already_pending(building_id) == 0:
            if self.can_afford(building_id):
                await self.build(building_id, near=self.townhalls.first.position.towards(self.game_info.map_center, 5))

    async def try_expand(self, desired_hatcheries: int):
        if self.can_afford(UnitTypeId.HATCHERY) and len(self.townhalls) + self.already_pending(UnitTypeId.HATCHERY) < desired_hatcheries:
            next_expansion = await self.get_next_expansion()
            await self.build(UnitTypeId.HATCHERY, next_expansion)

    async def tech_up(self):
        if self.structures(UnitTypeId.SPAWNINGPOOL).amount > 0:
            await self.tech_lair()
        else:
            await self.try_build_tech(UnitTypeId.SPAWNINGPOOL)

    async def tech_lair(self):
        if self.structures(UnitTypeId.LAIR).amount > 0:
            await self.tech_infestation_pit()
        else:
            starting_base = self.townhalls.closest_to(self.start_location)
            if starting_base.is_idle and self.can_afford(UnitTypeId.LAIR):
                starting_base.train(UnitTypeId.LAIR)

    async def tech_infestation_pit(self):
        if self.structures(UnitTypeId.INFESTATIONPIT).amount > 0:
            await self.tech_hive()
        else:
            await self.try_build_tech(UnitTypeId.INFESTATIONPIT)

    async def tech_hive(self):
        if self.structures(UnitTypeId.HIVE).amount > 0:
            return
        else:
            lair = self.structures(UnitTypeId.LAIR).first
            if lair.is_idle and self.can_afford(UnitTypeId.HIVE):
                lair.train(UnitTypeId.HIVE)
