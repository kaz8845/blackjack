from game import BlackjackGame


def active_game() -> BlackjackGame:
    game = BlackjackGame()
    game.player_cards = ["♠2", "♥3"]
    game.cpu_cards = ["♦4"]
    game.deck = ["♣5", "♣6", "♣7", "♣8"]
    game.phase = "PLAYER_TURN"
    game.last_result = None
    return game


def test_score_label_with_ace_has_two_values():
    assert BlackjackGame.score_label(["♠A", "♥8"]) == "9 / 19"


def test_bust_score_with_ace_counts_as_low_value():
    assert BlackjackGame.best_score(["♠A", "♥9", "♦9"]) == 19


def test_exchange_swaps_cards_and_consumes_item():
    game = active_game()
    player = game.player_cards.copy()
    cpu = game.cpu_cards.copy()
    game.exchange()
    assert game.player_cards == cpu
    assert game.cpu_cards == player
    assert game.exchange_count == 0


def test_one_more_adds_selected_card_and_consumes_item():
    game = active_game()
    initial_len = len(game.player_cards)
    state = game.request_one_more()
    selected = state["pending_one_more"][0]
    game.choose_one_more("A")
    assert selected in game.player_cards
    assert len(game.player_cards) == initial_len + 1
    assert game.one_more_count == 2
