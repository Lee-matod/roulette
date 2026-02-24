# -*- coding: utf-8 -*-

import random
from enum import Enum
from typing import Final, List, Tuple

from roulette.error import InvalidBet, NotEnoughFunds


class SplitBetType(Enum):
    RIGHT = 0
    DOWN = 1


class Bet:
    """Represents a bet made on a roulette table.

    Parameters
    ----------
    amount: :class:`int`
        The amount of funds that were used for this particular bet.
    multiplier: :class:`int`
        The payout multiplier, in case this bet is won.
    covered: Tuple[:class:`int`, ...]
        The numbers covered by this bet.

    Attributes
    ----------
    amount: :class:`int`
        The amount of funds that were used for this particular bet. Read-only.
    covered: Tuple[:class:`int`, ...]
        The numbers covered by this bet. Read-only.
    """

    def __init__(self, amount: int, multiplier: int, covered: Tuple[int, ...]) -> None:
        self.amount: Final[int] = amount
        self.covered: Final[Tuple[int, ...]] = covered
        self._mult: Final[int] = multiplier

    @property
    def payout(self) -> int:
        """:class:`int`: Returns the amount of rewarded funds after applying the multiplier."""
        return self.amount * self._mult

    def has_won(self, winner: int) -> bool:
        """Determines whether this bet can be considered won.

        Parameters
        ----------
        winner: :class:`int`
            The winning number.

        Returns
        -------
        :class:`bool`
            Whether this bet covered the winning number or not.
        """
        return winner in self.covered


class Roulette:
    """Represents a casino roulette table.

    Numbers are ordered in lowest-to-highest, bottom-to-top, left-to-right style:

      | 3 6 9 12 | 15 18 21 24 | 27 30 33 36 | 3rd col
    0 | 2 5 8 11 | 14 17 20 23 | 26 29 32 35 | 2nd col
      | 1 4 7 10 | 13 16 19 22 | 25 28 31 34 | 1st col
      +----------+-------------+-------------+
      | 1st doz  |   2nd doz   |   3rd doz   |

    Parameters
    ----------
    initial: :class:`int`
        Any initial funds to start with. Defaults to 0.

    Attributes
    ----------
    funds: :class:`int`
        The amount of funds available to use for a bet.
    bets: List[~:class:`Bet`]
        Bets made for the next spin.
    """

    # TODO: optionally include double-zero

    def __init__(self, initial: int = 0, /) -> None:
        self.funds: int = initial
        self.bets: List[Bet] = []

    def spin(self) -> Tuple[int, int]:
        """Randomly generates a winning number and pays bets out.

        :attr:`funds` is automatically increased for any bets won.

        Returns
        -------
        Tuple[:class:`int`, :class:`int`]
            The winning number and the amount of funds cashed out, respectively.
        """
        winner = random.randint(0, 36)
        cashout = 0
        for bet in self.bets:
            if bet.has_won(winner):
                self.funds += bet.payout
                cashout += bet.payout
        self.bets.clear()
        return (winner, cashout)

    # Inside bets

    def bet_single(self, number: int, /, amount: int = 1) -> int:
        """Make a bet on a single number of the table.

        Payout is 35:1.

        Parameters
        ----------
        number: :class:`int`
            The number to bet on.
        amount: :class:`int`
            The amount of funds to use for this particular bet.
            Defaults to 1.

        Raises
        ------
        InvalidBet
            The bet made is invalid.
        NotEnoughFunds
            The provided amount is greater than the available funds.

        Returns
        -------
        :class:`int`
            The number that was bet on.
        """
        self._add_bet((number,), amount, 35)
        return number

    def bet_split(self, first: int, location: SplitBetType, /, amount: int = 1) -> Tuple[int, int]:
        """Make a bet on any 2 numbers adjecent to eachother on the table.

        Payout is 17:1.

        Parameters
        ----------
        first: :class:`int`
            The reference number to use for the second one.
        location: SplitBetType
            Where the first number is located with respect to the second one.
        amount: :class:`int`
            The amount of funds to use for this particular bet.
            Defaults to 1.

        Raises
        ------
        InvalidBet
            The bet made is invalid.
        NotEnoughFunds
            The provided amount is greater than the available funds.

        Returns
        -------
        Tuple[:class:`int`, :class:`int`]
            The numbers that were bet on.
        """
        numbers: Tuple[int, int]
        if first <= 0 or first > 36:
            raise InvalidBet(f"Invalid first split number {first}")
        if location is SplitBetType.DOWN:
            if first % 3 == 0:
                raise InvalidBet(f"No number above {first}")
            numbers = (first, first + 1)
        elif location is SplitBetType.RIGHT:
            numbers = (first, max(first - 3, 0))
        else:
            raise InvalidBet("Invalid split location")
        self._add_bet(numbers, amount, 17)
        return numbers

    def bet_street(self, street: int, /, amount: int = 1) -> Tuple[int, int, int]:
        """Make a bet on any 3 consecutive numbers in a row.

        Payout is 11:1.

        Parameters
        ----------
        street: :class:`int`
            The first of the 3 consecutive numbers.
            Only 1st column numbers are allowed.
        amount: :class:`int`
            The amount of funds to use for this particular bet.
            Defaults to 1.

        Raises
        ------
        InvalidBet
            The bet made is invalid.
        NotEnoughFunds
            The provided amount is greater than the available funds.

        Returns
        -------
        Tuple[:class:`int`, :class:`int`, :class:`int`]
            The numbers that were bet on.
        """
        if (street - 1) % 3 != 0:
            raise InvalidBet("Invalid street number")
        numbers = (street, street + 1, street + 2)
        self._add_bet(numbers, amount, 11)
        return numbers

    def bet_corner(self, bottom_left: int, /, amount: int = 1) -> Tuple[int, int, int, int]:
        """Make a bet on any 4 numbers on a square.

        Payout is 8:1.

        Parameters
        ----------
        bottom_left: :class:`int`
            The bottom-left-most number of the 4-square numbers on the table.
            3rd column numbers are not allowed.
        amount: :class:`int`
            The amount of funds to use for this particular bet.
            Defaults to 1.

        Raises
        ------
        InvalidBet
            The bet made is invalid.
        NotEnoughFunds
            The provided amount is greater than the available funds.

        Returns
        -------
        Tuple[:class:`int`, :class:`int`, :class:`int`, :class:`int`]
            The numbers that were bet on.
        """
        # TODO: allow for left-most corners (include 0)
        if bottom_left % 3 == 0:
            raise InvalidBet("Invalid bottom-left corner number")
        numbers = (bottom_left, bottom_left + 1, bottom_left + 3, bottom_left + 4)
        self._add_bet(numbers, amount, 8)
        return numbers

    # TODO: allow for 5-number bet with double-zero

    def bet_sixline(self, bottom_left: int, /, amount: int = 1) -> Tuple[int, int, int, int, int, int]:
        """Make a bet for 6 consecutive numbers in a row.

        Payout is 5:1.

        Parameters
        ----------
        bottom_left: :class:`int`
            The first of the 6 consecutive numbers (bottom-left-most number on the table).
            Only 1st column numbers (except number 34) are allowed.
        amount: :class:`int`
            The amount of funds to use for this particular bet.
            Defaults to 1.

        Raises
        ------
        InvalidBet
            The bet made is invalid.
        NotEnoughFunds
            The provided amount is greater than the available funds.

        Returns
        -------
        Tuple[:class:`int`, :class:`int`, :class:`int`, :class:`int`, :class:`int`, :class:`int`]
            The numbers that were bet on.
        """
        if (bottom_left - 1) % 3 != 0:
            raise InvalidBet("Invalid bottom-left six line number")
        numbers = tuple(range(bottom_left, bottom_left + 6))
        self._add_bet(numbers, amount, 5)
        return numbers  # type: ignore

    # Outside bets

    def bet_column(self, colnum: int, /, amount: int = 1) -> Tuple[int, ...]:
        """Make a bet for any of the 3 columns on the table.

        1st column is all n numbers where (n - 1) mod 3 == 0.
        2nd column is all n numbers where (n - 2) mod 3 == 0.
        3rd column is all n numbers where n mod 3 == 0.

        Payout is 2:1.

        Parameters
        ----------
        colnum: :class:`int`
            The lowest (left-most) number of the column to bet on.
        amount: :class:`int`
            The amount of funds to use for this particular bet.
            Defaults to 1.

        Raises
        ------
        InvalidBet
            The bet made is invalid.
        NotEnoughFunds
            The provided amount is greater than the available funds.

        Returns
        -------
        Tuple[:class:`int`, ...]
            The numbers that were bet on.
        """
        if colnum not in range(1, 4):
            raise InvalidBet("Invalid column number")
        numbers = tuple((colnum + i * 3) for i in range(0, 12))
        self._add_bet(numbers, amount, 2)
        return numbers

    def bet_even(self, /, amount: int = 1) -> Tuple[int, ...]:
        """Make a bet for any even number.

        Payout is 1:1.

        Parameters
        ----------
        amount: :class:`int`
            The amount of funds to use for this particular bet.
            Defaults to 1.

        Raises
        ------
        InvalidBet
            The bet made is invalid.
        NotEnoughFunds
            The provided amount is greater than the available funds.

        Returns
        -------
        Tuple[:class:`int`, ...]
            The numbers that were bet on.
        """
        numbers = tuple(i for i in range(0, 37) if i % 2 == 0)
        self._add_bet(numbers, amount, 1)
        return numbers

    def bet_odd(self, /, amount: int = 1) -> Tuple[int, ...]:
        """Make a bet for any odd number.

        Payout is 1:1.

        Parameters
        ----------
        amount: :class:`int`
            The amount of funds to use for this particular bet.
            Defaults to 1.

        Raises
        ------
        InvalidBet
            The bet made is invalid.
        NotEnoughFunds
            The provided amount is greater than the available funds.

        Returns
        -------
        Tuple[:class:`int`, ...]
            The numbers that were bet on.
        """
        numbers = tuple(i for i in range(0, 37) if i % 2 != 0)
        self._add_bet(numbers, amount, 1)
        return numbers

    def bet_low(self, /, amount: int = 1) -> Tuple[int, ...]:
        """Make a bet for any low number: 1 to 18.

        Payout is 1:1.

        Parameters
        ----------
        amount: :class:`int`
            The amount of funds to use for this particular bet.
            Defaults to 1.

        Raises
        ------
        InvalidBet
            The bet made is invalid.
        NotEnoughFunds
            The provided amount is greater than the available funds.

        Returns
        -------
        Tuple[:class:`int`, ...]
            The numbers that were bet on.
        """
        numbers = tuple(i for i in range(1, 19))
        self._add_bet(numbers, amount, 1)
        return numbers

    def bet_high(self, /, amount: int = 1) -> Tuple[int, ...]:
        """Make a bet for any high number: 19 to 36.

        Payout is 1:1.

        Parameters
        ----------
        amount: :class:`int`
            The amount of funds to use for this particular bet.
            Defaults to 1.

        Raises
        ------
        InvalidBet
            The bet made is invalid.
        NotEnoughFunds
            The provided amount is greater than the available funds.

        Returns
        -------
        Tuple[:class:`int`, ...]
            The numbers that were bet on.
        """
        numbers = tuple(i for i in range(19, 37))
        self._add_bet(numbers, amount, 1)
        return numbers

    def bet_dozen(self, dozen: int, /, amount: int = 1) -> Tuple[int, ...]:
        """Make a bet for any of the 3 dozens on the table.

        1st dozen is 1-12.
        2nd dozen is 13-24.
        3rd dozen is 25-36.

        Payout is 2:1.

        Parameters
        ----------
        dozen: :class:`int`
            The dozen number to bet on. See above for valid numbers.
        amount: :class:`int`
            The amount of funds to use for this particular bet.
            Defaults to 1.

        Raises
        ------
        InvalidBet
            The bet made is invalid.
        NotEnoughFunds
            The provided amount is greater than the available funds.

        Returns
        -------
        Tuple[:class:`int`, ...]
            The numbers that were bet on.
        """
        if dozen not in range(1, 4):
            raise InvalidBet("Invalid dozen number")
        numbers = tuple(i for i in range(12 * (dozen - 1) + 1, 12 * dozen))
        self._add_bet(numbers, amount, 2)
        return numbers

    def bet_red(self, /, amount: int = 1) -> Tuple[int, ...]:
        """Make a bet for all red numbers on the table.

        Payout is 1:1.

        Parameters
        ----------
        amount: :class:`int`
            The amount of funds to use for this particular bet.
            Defaults to 1.

        Raises
        ------
        InvalidBet
            The bet made is invalid.
        NotEnoughFunds
            The provided amount is greater than the available funds.

        Returns
        -------
        Tuple[:class:`int`, ...]
            The numbers that were bet on.
        """
        numbers = (1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36)
        self._add_bet(numbers, amount, 1)
        return numbers

    def bet_black(self, /, amount: int = 1) -> Tuple[int, ...]:
        """Make a bet for all black numbers on the table.

        Payout is 1:1.

        Parameters
        ----------
        amount: :class:`int`
            The amount of funds to use for this particular bet.
            Defaults to 1.

        Raises
        ------
        InvalidBet
            The bet made is invalid.
        NotEnoughFunds
            The provided amount is greater than the available funds.

        Returns
        -------
        Tuple[:class:`int`, ...]
            The numbers that were bet on.
        """
        numbers = (2, 4, 6, 8, 10, 11, 13, 15, 17, 20, 22, 24, 26, 28, 29, 31, 33, 35)
        self._add_bet(numbers, amount, 1)
        return numbers

    def _add_bet(self, numbers: Tuple[int, ...], bet: int, win_mult: int) -> None:
        if any(n < 0 or n > 36 for n in numbers):
            raise InvalidBet("Bet has number outside of range 0..36")
        if bet > self.funds:
            raise NotEnoughFunds(self.funds, bet)
        self.funds -= bet
        obj = Bet(bet, win_mult, numbers)
        self.bets.append(obj)
