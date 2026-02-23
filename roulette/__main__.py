# -*- coding: utf-8 -*-

from typing import Callable, Optional

from roulette.error import RouletteException
from roulette.roulette import Roulette, SplitBetType

COMMAND_LIST = """\033[0mhelp: \033[3mdisplay a list of commands.\033[0m
spin: \033[3mspins the roulette wheel and gives out any winning bets.\033[0m
funds: \033[3mview your current funds.\033[0m
list: \033[3mview a list of current bets.\033[0m
remove: \033[3mremove a bet by its index.\033[0m
increase: \033[3madd an amount of funds to your session.\033[0m
bet: \033[3mmake a new bet.\033[0m
exit: \033[3mexit the roulette model.\033[0m"""

STARTUP = f"""\033[1;4mWelcome to Roulette!\033[0m

\033[1mTo get started, type any of the following commands:
{COMMAND_LIST}
"""

EXTRA_ARGS = ("single", "split", "street", "corner", "sixline", "column", "dozen")
NO_ARGS = ("black", "red", "high", "low", "odd", "even")
BET_TYPE = EXTRA_ARGS + NO_ARGS

CLEAR_LINES = lambda amount=1: print("\033[F\033[K" * amount, end="")


def wait_for[T](msg: str, func: Callable[[str], T] = str, *, default: Optional[T] = None) -> T:
    while True:
        try:
            inp = input(msg).strip()
            if not inp and default is not None:
                return default
            val = func(inp)
        except Exception:
            CLEAR_LINES(msg.count("\n") + 1)
            print("\033[31mInvalid input. Please try again.")
            continue
        if val is False:
            continue
        break
    return val


def entrypoint():
    print(STARTUP)
    roulette = Roulette()
    while True:
        cmd = input("\033[32m>>>\033[0m ").strip()

        if not cmd:
            continue
        elif cmd == "help":
            print(COMMAND_LIST)

        elif cmd == "spin":
            winner, cashout = roulette.spin()
            print(f"\033[33mLucky number: {winner}")
            print(f"\033[34mFunds cashed out: +${cashout:,}")

        elif cmd == "funds":
            print(f"\033[36m${roulette.funds:,}")

        elif cmd == "list":
            if not roulette.bets:
                print("\033[31mNo bets have been made yet.")
                continue
            print(
                "\n".join(
                    f"\033[33m[{i}] \033[32m${b.amount:,} \033[30m(payout: ${b.payout:,})\033[37m: "
                    + ", ".join(map(str, b.covered))
                    for i, b in enumerate(roulette.bets, start=1)
                )
            )

        elif cmd == "remove":
            if not roulette.bets:
                print("\033[31mNo bets have been made yet.")
                continue
            bet_num = wait_for(
                f"\033[35mSelect bet index (1-{len(roulette.bets)}): ",
                lambda s: (int(s) < 0 or int(s) > len(roulette.bets)) and int(s),
            )
            if bet_num > len(roulette.bets):
                print(f"\033[31mInvalid index {bet_num}.")
                continue
            CLEAR_LINES()
            roulette.bets.pop(bet_num - 1)
            print(f"\033[36mRemoved bet at index {bet_num}.")

        elif cmd == "increase":
            amount = wait_for("\033[35mInput amount: $", int)
            CLEAR_LINES()
            roulette.funds += amount
            print(f"\033[36mAdded ${amount:,} funds to your session (${roulette.funds:,})")

        elif cmd == "bet":
            print("\033[36mSelect the type of bet to make:\n\033[30m" + ", ".join(BET_TYPE))
            bet_type = wait_for("\033[35mBet type: ", lambda s: s in BET_TYPE and s)
            CLEAR_LINES(3)
            print(f"\033[36mBet type: {bet_type}")
            amount = wait_for("\033[35mInput bet amount (default: $1): $", lambda s: int(s) > 0 and int(s), default=1)
            CLEAR_LINES()
            print(f"\033[36mInput bet amount (default: $1): ${amount}")
            func = getattr(roulette, f"bet_{bet_type}")
            if bet_type in NO_ARGS:
                try:
                    nums = func(amount)
                except RouletteException as e:
                    print(f"\033[31mError: {e}")
                else:
                    print(
                        f"\033[36mSuccessfully placed bet of ${amount:,} on numbers:\n\033[30m",
                        ", ".join(map(str, nums)),
                    )
                continue
            if bet_type == "split":
                args = wait_for(
                    "\033[35mInput number location and reference point (0: RIGHT, 1: DOWN): ",
                    lambda s: (a := s.split())
                    and int(a[0].strip())
                    and int(a[1].strip()) in range(0, 2)
                    and (int(a[0].strip()), SplitBetType(int(a[1].strip()))),
                )
            else:
                args = (wait_for("\033[35mInput number location: ", int),)
            CLEAR_LINES()
            try:
                nums = func(*args)  # type: ignore
            except RouletteException as e:
                print(f"\033[31mError: {e}")
            else:
                if isinstance(nums, int):
                    nums = (nums,)
                print(
                    f"\033[36mSuccessfully placed bet of ${amount:,} on numbers:\n\033[30m" + ", ".join(map(str, nums))
                )

        elif cmd == "exit":
            break

        else:
            print("\033[31mInvalid command. Type 'help' for a list of commands.")


if __name__ == "__main__":
    try:
        entrypoint()
    except KeyboardInterrupt:
        pass
