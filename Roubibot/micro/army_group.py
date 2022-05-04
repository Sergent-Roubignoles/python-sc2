from helpers.strategy_analyser import allied_unit_dictionary
from sc2.position import Point2
from sc2.unit import Unit


class AttackGroup:
    attacker_tags = [int]
    target: Point2
    temp_target: Point2 = None

    attackers: list[Unit] = []

    def update_attacker_list(self):
        self.attackers = []
        for tag in self.attacker_tags:
            if tag in allied_unit_dictionary:
                unit: Unit = allied_unit_dictionary.get(tag)
                self.attackers.append(unit)
            else:
                self.attacker_tags.remove(tag)

    def attack(self):
        if len(self.attackers) == 0:
            return

        target_to_evaluate = self.target
        if self.temp_target is not None:
            target_to_evaluate = self.temp_target

        closest = self.attackers[0]
        furthest = self.attackers[0]
        for unit in self.attackers:
            if unit.distance_to(target_to_evaluate) < closest.distance_to(target_to_evaluate):
                closest = unit
            elif unit.distance_to(target_to_evaluate) > furthest.distance_to(target_to_evaluate):
                furthest = unit

        if self.temp_target is None:
            if furthest.distance_to(self.target) - closest.distance_to(self.target) > 30:
                # Set new temp target
                self.temp_target = closest.position
            for unit in self.attackers:
                if unit.is_idle:
                    unit.attack(self.temp_target)
        else:
            if furthest.distance_to(self.target) - closest.distance_to(self.target) < 20:
                # Remove temp target
                self.temp_target = None
            for unit in self.attackers:
                if unit.is_idle:
                    unit.attack(self.target)