from sc2.bot_ai import BotAI
from sc2.ids.unit_typeid import UnitTypeId
from strategies import strategy

last_kill_iteration = 0
minerals_lost = 0
gas_lost = 0
minerals_destroyed = 0
gas_destroyed = 0
trade_anounced = True
iterations_before_anouncing_trade = 35
kills_before_anouncing_trade = 10
kills = 0

async def announce_trade(bot: BotAI, iteration):
    global trade_anounced
    global kills
    if not trade_anounced and iteration - last_kill_iteration >= iterations_before_anouncing_trade and kills >= kills_before_anouncing_trade:
        global minerals_destroyed
        global minerals_lost
        global gas_destroyed
        global gas_lost

        mineral_advantage = minerals_destroyed - minerals_lost
        gas_advantage = gas_destroyed - gas_lost
        await bot.chat_send("Trade results: Minerals: {0}, Gas: {1}".format(mineral_advantage, gas_advantage))
        trade_anounced = True

        minerals_destroyed = 0
        minerals_lost = 0
        gas_destroyed = 0
        gas_lost = 0
        kills = 0

async def unit_destroyed(bot: BotAI, unit_tag: int, iteration):
    kill_counted = False
    if unit_tag in strategy.own_units:
        unit_type = strategy.own_units[unit_tag]
        if unit_type == UnitTypeId.EGG:
            return

        # await bot.chat_send("{0} lost".format(unit_type))

        kill_counted = True
        global minerals_lost
        global gas_lost

        try:
            cost = bot.calculate_cost(unit_type)
            minerals_lost += cost.minerals
            gas_lost += cost.vespene
        except AssertionError:
            pass
    else:
        if unit_tag in strategy.enemy_units:
            unit_type = strategy.enemy_units[unit_tag]
            if unit_type == UnitTypeId.EGG:
                return

            # await bot.chat_send("{0} destroyed".format(unit_type))

            kill_counted = True
            global minerals_destroyed
            global gas_destroyed

            try:
                cost = bot.calculate_cost(unit_type)
                minerals_destroyed += cost.minerals
                gas_destroyed += cost.vespene
            except AssertionError:
                pass
        # else:
        #     await bot.chat_send("Unit destroyed; tag not recognized")

    if kill_counted:
        global last_kill_iteration
        global trade_anounced
        global kills

        last_kill_iteration = iteration
        trade_anounced = False
        kills += 1