from __future__ import annotations

from sc2.bot_ai import BotAI


class Strategy:
    is_finished = False

    async def on_step(self, bot: BotAI):
        pass

    def prefered_follow_up_strategy(self) -> Strategy:
        pass
