"""Core game logic for Blackjack Item Battle.

This module has no GUI dependencies.  The Tkinter UI imports this class and
only handles rendering and button events.  Keeping the game rules here makes
this project easier to test and extend.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import random
from typing import Literal

Suit = Literal["♥", "♦", "♣", "♠"]
Rank = Literal["2", "3", "4", "5", "6", "7", "8", "9", "10", "A"]
GamePhase = Literal["PLAYER_TURN", "CHOOSE_ONE_MORE", "ROUND_END", "GAME_OVER"]

SUITS: tuple[Suit, ...] = ("♥", "♦", "♣", "♠")
RANKS: tuple[Rank, ...] = ("2", "3", "4", "5", "6", "7", "8", "9", "10", "A")


@dataclass
class RoundResult:
    title: str
    detail: str
    survived_by_ex_life: bool = False


@dataclass
class BlackjackGame:
    """Stateful blackjack-like game with item mechanics."""

    wins: int = 0
    exchange_count: int = 1
    one_more_count: int = 3
    restart_count: int = 1
    ex_life_count: int = 0
    player_cards: list[str] = field(default_factory=list)
    cpu_cards: list[str] = field(default_factory=list)
    deck: list[str] = field(default_factory=list)
    phase: GamePhase = "PLAYER_TURN"
    message: str = "New game started."
    pending_one_more: tuple[str, str] | None = None
    last_result: RoundResult | None = None

    def __post_init__(self) -> None:
        self.start_round(reset_items=False)

    @staticmethod
    def build_deck() -> list[str]:
        deck = [f"{suit}{rank}" for suit in SUITS for rank in RANKS]
        random.shuffle(deck)
        return deck

    @staticmethod
    def card_value(card: str) -> int:
        rank = card[1:]
        if rank == "A":
            return 1
        return min(int(rank), 10)

    @classmethod
    def score_values(cls, cards: list[str]) -> tuple[int, int | None]:
        """Return low score and optional high score using one Ace as 11."""
        low = sum(cls.card_value(card) for card in cards)
        has_ace = any(card.endswith("A") for card in cards)
        high = low + 10 if has_ace and low + 10 <= 21 else None
        return low, high

    @classmethod
    def best_score(cls, cards: list[str]) -> int:
        low, high = cls.score_values(cards)
        return high if high is not None else low

    @classmethod
    def score_label(cls, cards: list[str]) -> str:
        low, high = cls.score_values(cards)
        return f"{low} / {high}" if high is not None and high != low else str(low)

    @classmethod
    def is_bust(cls, cards: list[str]) -> bool:
        return cls.best_score(cards) > 21

    def draw_card(self) -> str:
        if not self.deck:
            self.deck = self.build_deck()
        return self.deck.pop()

    def start_round(self, reset_items: bool = False) -> dict:
        if reset_items:
            self.wins = 0
            self.exchange_count = 1
            self.one_more_count = 3
            self.restart_count = 1
            self.ex_life_count = 0

        self.deck = self.build_deck()
        self.player_cards = [self.draw_card(), self.draw_card()]
        self.cpu_cards = [self.draw_card()]
        self.phase = "PLAYER_TURN"
        self.pending_one_more = None
        self.last_result = None

        if self.best_score(self.player_cards) == 21:
            self.message = "Blackjack! Round won."
            self._finish_round(player_blackjack=True)
        else:
            self.message = "Choose an action."
        return self.get_state()

    def new_game(self) -> dict:
        return self.start_round(reset_items=True)

    def restart_round(self) -> dict:
        if self.phase not in ("PLAYER_TURN", "CHOOSE_ONE_MORE"):
            self.message = "Round already ended. Start next round."
            return self.get_state()
        if self.restart_count <= 0:
            self.message = "Restart item is not available."
            return self.get_state()
        self.restart_count -= 1
        self.start_round(reset_items=False)
        self.message = "Restart used. New hand dealt."
        return self.get_state()

    def hit(self) -> dict:
        if self.phase != "PLAYER_TURN":
            self.message = "Hit is not available now."
            return self.get_state()

        drawn = self.draw_card()
        self.player_cards.append(drawn)
        self.message = f"Player drew {drawn}."

        if self.best_score(self.player_cards) >= 21:
            self._finish_round(player_blackjack=self.best_score(self.player_cards) == 21)
        else:
            self._cpu_auto_action()
        return self.get_state()

    def stand(self) -> dict:
        if self.phase != "PLAYER_TURN":
            self.message = "Stand is not available now."
            return self.get_state()

        while self.best_score(self.cpu_cards) <= self.best_score(self.player_cards):
            self.cpu_cards.append(self.draw_card())
            if self.is_bust(self.cpu_cards):
                break
        self._finish_round()
        return self.get_state()

    def exchange(self) -> dict:
        if self.phase != "PLAYER_TURN":
            self.message = "Exchange is not available now."
            return self.get_state()
        if self.exchange_count <= 0:
            self.message = "Exchange item is not available."
            return self.get_state()

        self.player_cards, self.cpu_cards = self.cpu_cards, self.player_cards
        self.exchange_count -= 1
        self.message = "Exchange used. Hands were swapped."
        if self.best_score(self.player_cards) >= 21:
            self._finish_round(player_blackjack=self.best_score(self.player_cards) == 21)
        return self.get_state()

    def request_one_more(self) -> dict:
        if self.phase != "PLAYER_TURN":
            self.message = "1More is not available now."
            return self.get_state()
        if self.one_more_count <= 0:
            self.message = "1More item is not available."
            return self.get_state()

        card_a = self.draw_card()
        card_b = self.draw_card()
        self.pending_one_more = (card_a, card_b)
        self.phase = "CHOOSE_ONE_MORE"
        self.message = "Choose one of the two cards."
        return self.get_state()

    def choose_one_more(self, choice: Literal["A", "B"]) -> dict:
        if self.phase != "CHOOSE_ONE_MORE" or self.pending_one_more is None:
            self.message = "There is no 1More choice to resolve."
            return self.get_state()

        selected = self.pending_one_more[0] if choice == "A" else self.pending_one_more[1]
        self.player_cards.append(selected)
        self.one_more_count -= 1
        self.pending_one_more = None
        self.phase = "PLAYER_TURN"
        self.message = f"1More selected {selected}."

        if self.best_score(self.player_cards) >= 21:
            self._finish_round(player_blackjack=self.best_score(self.player_cards) == 21)
        else:
            self._cpu_auto_action()
        return self.get_state()

    def next_round(self) -> dict:
        if self.phase not in ("ROUND_END", "GAME_OVER"):
            self.message = "The current round is still active."
            return self.get_state()
        if self.phase == "GAME_OVER":
            self.message = "Game over. Press New Game to restart."
            return self.get_state()
        return self.start_round(reset_items=False)

    def _cpu_auto_action(self) -> None:
        if self.best_score(self.cpu_cards) < 17:
            drawn = self.draw_card()
            self.cpu_cards.append(drawn)
            self.message += f" CPU drew {drawn}."
        else:
            self.message += " CPU stood."
        if self.is_bust(self.player_cards) or self.is_bust(self.cpu_cards):
            self._finish_round()

    def _finish_round(self, player_blackjack: bool = False) -> None:
        player_score = self.best_score(self.player_cards)
        cpu_score = self.best_score(self.cpu_cards)

        player_final = 0 if player_score > 21 else player_score
        cpu_final = 0 if cpu_score > 21 else cpu_score

        if player_final == 0 and cpu_final == 0:
            result = RoundResult("Draw", "Both sides busted.")
            self.phase = "ROUND_END"
        elif player_blackjack or player_final >= cpu_final:
            self.wins += 1
            if player_blackjack:
                result = RoundResult("21!!", "Player reached 21 and won the round.")
            else:
                result = RoundResult("You Win!", "Player score is equal to or higher than CPU score.")
            self._grant_reward(player_blackjack=player_blackjack)
            self.phase = "ROUND_END"
        else:
            if self.ex_life_count > 0:
                self.ex_life_count -= 1
                result = RoundResult("EXlife activated", "Loss was cancelled by EXlife.", survived_by_ex_life=True)
                self.phase = "ROUND_END"
            else:
                result = RoundResult("You Lose", "CPU score was higher. Game over.")
                self.phase = "GAME_OVER"

        self.last_result = result
        self.message = f"{result.title}: {result.detail}"

    def _grant_reward(self, player_blackjack: bool) -> None:
        if self.wins % 5 == 0 and player_blackjack:
            self.ex_life_count += 1
            self.message = "Reward: EXlife"
            return
        if self.wins % 5 == 0 or player_blackjack:
            item = random.randint(1, 100)
            if 1 <= item < 71:
                self.one_more_count += 1
            elif 71 <= item < 85:
                self.exchange_count += 1
            elif 85 <= item < 99:
                self.restart_count += 1
            else:
                self.ex_life_count += 1

    def get_state(self) -> dict:
        return {
            "phase": self.phase,
            "wins": self.wins,
            "player_cards": self.player_cards.copy(),
            "cpu_cards": self.cpu_cards.copy(),
            "player_score": self.score_label(self.player_cards),
            "cpu_score": self.score_label(self.cpu_cards),
            "player_bust": self.is_bust(self.player_cards),
            "cpu_bust": self.is_bust(self.cpu_cards),
            "items": {
                "Exchange": self.exchange_count,
                "1More": self.one_more_count,
                "Restart": self.restart_count,
                "EXlife": self.ex_life_count,
            },
            "pending_one_more": self.pending_one_more,
            "message": self.message,
            "result": None
            if self.last_result is None
            else {
                "title": self.last_result.title,
                "detail": self.last_result.detail,
                "survived_by_ex_life": self.last_result.survived_by_ex_life,
            },
        }
