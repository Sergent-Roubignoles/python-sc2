import random
from typing import List

from Helpers import queen_helper, surrender_logic, scouting, economy
from sc2.bot_ai import BotAI
from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.upgrade_id import UpgradeId
from sc2.position import Point2


class CompetitiveBot(BotAI):

    buildOrderIndex = 0
    first_push_done = False
    panic_mode = False

    def select_target(self) -> Point2:
        if self.enemy_structures:
            return random.choice(self.enemy_structures).position
        return self.enemy_start_locations[0]

    async def on_start(self):
        print("Game started")
        # Do things here before the game starts
        scouting.find_entry_point(self)

    async def on_step(self, iteration):
        # Populate this function with whatever your bot should do!
        await surrender_logic.surrender_if_overwhelming_losses(self)
        if iteration == 0:
            await self.chat_send("glhf")

        if self.panic_mode:
            for unit in self.all_own_units.idle:
                unit.attack(self.enemy_start_locations[0])
            return

        if self.townhalls.amount > 0 and self.workers.amount > 0:
            await self.bo()[self.buildOrderIndex]()
            queen_helper.inject(self, iteration)
            move_scout(self)
            scouting.move_overlord(self)
        else:
            await self.chat_send("Panic mode engaged!!")
            self.panic_mode = True

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
            target_base = scouting.BaseIdentifier.enemy_3rd[random.randint(0, 1)]
            for ling in self.units(UnitTypeId.ZERGLING).idle:
                ling.attack(target_base)
                ling.attack(self.enemy_start_locations[0], queue= True)
                self.first_push_done = True
        else:
            for unit in self.units(UnitTypeId.ZERGLING).idle:
                unit.move(self.townhalls.closest_to(self.enemy_start_locations[0]).position.towards(self.game_info.map_center, 10))

        if self.minerals > 800 and not self.already_pending(UnitTypeId.HATCHERY):
            next_expansion = await self.get_next_expansion()
            if next_expansion is not None:
                if self.can_afford(UnitTypeId.HATCHERY):
                    await self.build(UnitTypeId.HATCHERY, next_expansion)

    async def late_game_lings(self):
        economy.saving_money = False
        await economy.develop_tech(self)
        await economy.expand_eco(self, 60, 5)
        await economy.expand_army(self)

        army = self.units.of_type({UnitTypeId.ZERGLING, UnitTypeId.BANELING, UnitTypeId.CORRUPTOR, UnitTypeId.BROODLORD})
        if self.supply_army > 70:
            default_target = scouting.BaseIdentifier.enemy_3rd[random.randint(0, 1)]
            targets = self.enemy_structures
            if targets.amount > 0:
                for unit in army.idle:
                    unit.attack(targets.closest_to(self.game_info.map_center).position)
            else:
                for unit in army.idle:
                    unit.attack(default_target)
                    unit.attack(self.enemy_start_locations[0], queue= True)
        else:
            staging_point = self.townhalls.closest_to(self.enemy_start_locations[0]).position.towards(self.game_info.map_center, 10)
            for unit in army.idle:
                if unit.distance_to(staging_point) > 10:
                    unit.move(staging_point)

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


async def try_queue_research(bot: BotAI, structure_id: UnitTypeId, upgrade_id: UpgradeId):
    if upgrade_id not in bot.state.upgrades:
        idle_structures = bot.structures(structure_id).idle
        if idle_structures.amount > 0:
            idle_structures.first.research(upgrade_id)

scout_id: int = 0

def move_scout(bot: BotAI):
    global scout_id
    position_to_scout: Point2

    try:
        scout = bot.all_own_units.by_tag(scout_id)
        if scout.is_idle:
            expansions: List[Point2] = bot.expansion_locations_list
            random.shuffle(expansions)
            scout.move(expansions[0].position)
    except KeyError:
        idle_lings = bot.all_own_units(UnitTypeId.ZERGLING).idle
        if idle_lings.amount > 0:
            scout_id = idle_lings.first.tag