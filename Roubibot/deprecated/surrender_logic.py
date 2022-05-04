from sc2.bot_ai import BotAI

highest_supply: int = 0
has_surrendered = False


async def surrender_if_overwhelming_losses(bot: BotAI):
    global highest_supply
    global has_surrendered

    if not has_surrendered:
        if bot.workers.amount == 0:
            await surrender(bot)

        current_supply = bot.supply_used
        if current_supply > highest_supply:
            highest_supply = current_supply
        else:
            if current_supply < highest_supply / 5:
                await surrender(bot)

async def surrender(bot: BotAI):
    global has_surrendered
    await bot.chat_send("Supply went from {0} to {1}; surrendering now.".format(highest_supply, bot.supply_used))
    await bot.chat_send("(pineapple)")
    has_surrendered = True