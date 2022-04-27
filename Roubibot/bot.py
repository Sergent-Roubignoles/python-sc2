import random

from Helpers import queen_helper
from Roubibot.Helpers import surrender_logic
from sc2.bot_ai import BotAI
from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.upgrade_id import UpgradeId
from sc2.position import Point2


class CompetitiveBot(BotAI):

    buildOrderIndex = 0
    first_push_done = False

    def select_target(self) -> Point2:
        if self.enemy_structures:
            return random.choice(self.enemy_structures).position
        return self.enemy_start_locations[0]

    async def on_start(self):
        print("Game started")
        # Do things here before the game starts

    async def on_step(self, iteration):
        # Populate this function with whatever your bot should do!
        await surrender_logic.surrender_if_overwhelming_losses(self)
        if iteration == 0:
            await self.chat_send("glhf")
        await self.bo()[self.buildOrderIndex]()
        queen_helper.inject(self, iteration)

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
        # Increase supply
        if self.supply_left <= 2 and self.already_pending(UnitTypeId.OVERLORD) == 0:
            if not self.can_afford(UnitTypeId.OVERLORD):
                return
            self.train(UnitTypeId.OVERLORD)
        if self.supply_left <= 4 and self.supply_used > 30 and self.already_pending(UnitTypeId.OVERLORD) == 0:
            if not self.can_afford(UnitTypeId.OVERLORD):
                return
            self.train(UnitTypeId.OVERLORD)
        if self.supply_left <= 10 and self.supply_used > 50 and self.already_pending(UnitTypeId.OVERLORD) < 2:
            if not self.can_afford(UnitTypeId.OVERLORD):
                return
            self.train(UnitTypeId.OVERLORD)

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

        if UpgradeId.ZERGLINGMOVEMENTSPEED not in self.state.upgrades:
            self.research(UpgradeId.ZERGLINGMOVEMENTSPEED)
        if not self.first_push_done:
            await self.first_ling_push()
        else:
            await self.late_game_lings()

    async def first_ling_push(self):
        if self.supply_workers < 40:
            self.train(UnitTypeId.DRONE, int(40 - self.supply_workers))
        await self.distribute_workers()

        self.train(UnitTypeId.ZERGLING, int(self.supply_left))

        if self.units(UnitTypeId.ZERGLING).amount > 30:
            for ling in self.units(UnitTypeId.ZERGLING).idle:
                ling.attack(self.enemy_start_locations[0])
                self.first_push_done = True
        else:
            for unit in self.units(UnitTypeId.ZERGLING).idle:
                unit.move(self.townhalls.closest_to(self.enemy_start_locations[0]).position.towards(self.game_info.map_center, 10))

    async def late_game_lings(self):
        await self.tech_banelings()
        await self.tech_hive()
        self.research(UpgradeId.ZERGLINGATTACKSPEED)

        # Expand if out of mineral fields
        available_mineral_fields = []
        for mineral_field in self.mineral_field:
            for hatchery in self.townhalls.ready:
                if mineral_field.distance_to(hatchery) < 10:
                    available_mineral_fields.append(mineral_field)
        if len(available_mineral_fields) < 24 and not self.already_pending(UnitTypeId.HATCHERY):
            next_expansion = await self.get_next_expansion()
            if next_expansion is not None:
                await self.build(UnitTypeId.HATCHERY, next_expansion)

        # Build workers
        if self.supply_workers < 60:
            self.train(UnitTypeId.DRONE, int(60 - self.supply_workers))
        await self.distribute_workers()

        if self.can_afford(UnitTypeId.EXTRACTOR) and len(self.gas_buildings) + self.already_pending(UnitTypeId.EXTRACTOR) < 3:
            geyser = self.vespene_geyser.closest_to(self.townhalls.first)
            self.workers.closest_to(geyser).build_gas(geyser)

        self.train(UnitTypeId.ZERGLING, int(self.supply_left))
        for zergling in self.all_own_units(UnitTypeId.ZERGLING):
            if self.can_afford(UnitTypeId.BANELING):
                zergling(AbilityId.MORPHZERGLINGTOBANELING_BANELING)

        army = self.units.of_type({UnitTypeId.ZERGLING, UnitTypeId.BANELING})
        if army.amount > 80:
            for unit in army.idle:
                unit.attack(self.enemy_start_locations[0])
                self.first_push_done = True
        else:
            for unit in army.idle:
                unit.move(self.townhalls.closest_to(self.enemy_start_locations[0]).position.towards(self.game_info.map_center, 10))

    def current_plus_pending_count(self, unit_id: UnitTypeId):
        return int(self.units.of_type(unit_id).amount + self.already_pending(unit_id))

    async def try_build_tech(self, building_id: UnitTypeId):
        if self.structures(building_id).amount + self.already_pending(building_id) == 0:
            if self.can_afford(building_id):
                await self.build(building_id, near=self.townhalls.closest_to(self.start_location).position.towards(self.game_info.map_center, 5))

    async def try_expand(self, desired_hatcheries: int):
        if self.can_afford(UnitTypeId.HATCHERY) and len(self.townhalls) + self.already_pending(UnitTypeId.HATCHERY) < desired_hatcheries:
            next_expansion = await self.get_next_expansion()
            await self.build(UnitTypeId.HATCHERY, next_expansion)

    async def tech_lair(self):
        if self.structures(UnitTypeId.LAIR).amount > 0:
            return
        if self.structures(UnitTypeId.SPAWNINGPOOL).amount > 0:
            starting_base = self.townhalls.closest_to(self.start_location)
            if starting_base.is_idle and self.can_afford(UnitTypeId.LAIR):
                starting_base.train(UnitTypeId.LAIR)
        else:
            await self.try_build_tech(UnitTypeId.SPAWNINGPOOL)

    async def tech_hive(self):
        if self.structures(UnitTypeId.HIVE).amount > 0:
            return
        lairs = self.structures(UnitTypeId.LAIR)
        if lairs.amount > 0:
            if self.structures(UnitTypeId.INFESTATIONPIT).amount > 0:
                lair = lairs.first
                if lair.is_idle and self.can_afford(UnitTypeId.HIVE):
                    lair.train(UnitTypeId.HIVE)
            else:
                await self.try_build_tech(UnitTypeId.INFESTATIONPIT)
        else:
            await self.tech_lair()

    async def tech_banelings(self):
        if self.structures(UnitTypeId.BANELINGNEST).amount > 0:
            await try_queue_research(self, UnitTypeId.BANELINGNEST, UpgradeId.BANELINGSPEED)
            return

        if self.structures(UnitTypeId.SPAWNINGPOOL).amount > 0:
            await self.try_build_tech(UnitTypeId.BANELINGNEST)
        else:
            await self.try_build_tech(UnitTypeId.SPAWNINGPOOL)


async def try_queue_research(bot: BotAI, structure_id: UnitTypeId, upgrade_id: UpgradeId):
    if upgrade_id not in bot.state.upgrades:
        idle_structures = bot.structures(structure_id).idle
        if idle_structures.amount > 0:
            idle_structures.first.research(upgrade_id)
