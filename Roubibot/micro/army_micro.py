from helpers.strategy_analyser import known_enemy_unit_dictionary
from sc2.bot_ai import BotAI
from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId
from sc2.position import Point2
from sc2.unit import Unit

can_burrow = False
can_burrow_move_roaches = False

async def micro_unit(bot: BotAI, unit: Unit, target: Point2, retreat_point: Point2):
    if unit.type_id == UnitTypeId.ROACH:
        if not unit.is_burrowed:
            if unit.health_percentage < 0.33:
                # Burrow
                if can_burrow and can_burrow_move_roaches:
                    if not unit.is_burrowed:
                            unit(AbilityId.BURROWDOWN)
            else:
                # Attack or move forward
                if unit.weapon_ready:
                    enemies_in_range = get_enemies_in_range(unit, ignore_air= True)
                    if len(enemies_in_range) > 0:
                        # Attack weakest enemy
                        weakest_enemy = enemies_in_range[0]
                        for enemy in enemies_in_range:
                            if enemy.health + enemy.shield < weakest_enemy.health + weakest_enemy.shield:
                                weakest_enemy = enemy
                        unit.attack(weakest_enemy)
                    else:
                        # Move forward
                        enemies_in_sight = get_enemies_in_sight(unit, ignore_air= True)
                        if len(enemies_in_sight) > 0:
                            # Move to closest enemy
                            closest_enemy = enemies_in_sight[0]
                            for enemy in enemies_in_sight:
                                if unit.distance_to(enemy) < unit.distance_to(closest_enemy):
                                    closest_enemy = enemy
                            unit.move(closest_enemy)
                        else:
                            # Move towards original target
                            unit.move(target)
        else:
            if unit.health_percentage < 0.95:
                # Retreat
                closest_enemy = known_enemy_unit_dictionary.closest_to(unit)
                if closest_enemy.distance_to(unit) < 10:
                    unit.move(retreat_point)
            else:
                # Unburrow
                unit(AbilityId.BURROWUP)

def get_enemies_in_range(unit: Unit, ignore_ground = False, ignore_air = False):
    enemies_in_range: list[Unit] = []
    for enemy in known_enemy_unit_dictionary:
        if ignore_ground and not enemy.is_flying:
            continue
        if ignore_air and enemy.is_flying:
            continue

        if unit.target_in_range(enemy):
            enemies_in_range.append(unit)
    return enemies_in_range

def get_enemies_in_sight(unit: Unit, ignore_ground = False, ignore_air = False):
    enemies_in_sight: list[Unit] = []
    for enemy in known_enemy_unit_dictionary:
        if ignore_ground and not enemy.is_flying:
            continue
        if ignore_air and enemy.is_flying:
            continue

        if unit.distance_to(enemy) < unit.sight_range:
            enemies_in_sight.append(unit)
    return enemies_in_sight


async def retreat():
    pass