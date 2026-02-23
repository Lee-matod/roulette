# -*- coding: utf-8 -*-


class RouletteException(Exception):
    pass


class NotEnoughFunds(RouletteException):
    def __init__(self, funds: int, bet: int) -> None:
        self.funds: int = funds
        self.bet: int = bet
        super().__init__(f"Insufficient funds (${funds:,}) to place ${bet:,} bet")


class InvalidBet(RouletteException):
    pass
