from helpers import strategy_analyser, base_identifier
from macro import economy
from sc2.bot_ai import BotAI
from sc2.ids.unit_typeid import UnitTypeId


def amount_of_type(bot: BotAI, unit_id: UnitTypeId):
    return bot.all_own_units(unit_id).amount + bot.already_pending(unit_id)

