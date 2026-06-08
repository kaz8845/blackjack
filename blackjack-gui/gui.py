"""Tkinter user interface for Blackjack Item Battle."""
from __future__ import annotations

import tkinter as tk
from tkinter import messagebox
from typing import Callable

from game import BlackjackGame


class BlackjackApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Blackjack Item Battle")
        self.geometry("820x900")
        self.minsize(780, 820)
        self.configure(bg="#1f2933")
        self.game = BlackjackGame()
        self.card_labels: dict[str, list[tk.Label]] = {"cpu": [], "player": []}
        self.item_vars = {
            "Exchange": tk.StringVar(),
            "1More": tk.StringVar(),
            "Restart": tk.StringVar(),
            "EXlife": tk.StringVar(),
        }
        self.wins_var = tk.StringVar()
        self.cpu_score_var = tk.StringVar()
        self.player_score_var = tk.StringVar()
        self.message_var = tk.StringVar()

        self._build_layout()
        self.refresh()

    def _build_layout(self) -> None:
        title = tk.Label(
            self,
            text="Blackjack Item Battle",
            font=("Helvetica", 26, "bold"),
            fg="white",
            bg="#1f2933",
        )
        title.pack(pady=(18, 4))

        subtitle = tk.Label(
            self,
            textvariable=self.wins_var,
            font=("Helvetica", 14),
            fg="#d9e2ec",
            bg="#1f2933",
        )
        subtitle.pack(pady=(0, 14))

        table = tk.Frame(self, bg="#323f4b", padx=18, pady=18)
        table.pack(fill="both", expand=True, padx=28, pady=8)

        self.cpu_frame = self._create_hand_frame(table, "CPU", self.cpu_score_var)
        self.cpu_frame.pack(fill="x", pady=(0, 14))

        self.player_frame = self._create_hand_frame(table, "Player", self.player_score_var)
        self.player_frame.pack(fill="x", pady=(0, 14))

        items_frame = tk.LabelFrame(
            table,
            text="Items",
            font=("Helvetica", 12, "bold"),
            fg="white",
            bg="#323f4b",
            bd=2,
            relief="groove",
            labelanchor="n",
            padx=12,
            pady=8,
        )
        items_frame.pack(fill="x", pady=(0, 14))
        for index, (name, var) in enumerate(self.item_vars.items()):
            label = tk.Label(
                items_frame,
                textvariable=var,
                font=("Helvetica", 12),
                fg="#f0f4f8",
                bg="#323f4b",
                width=16,
                anchor="w",
            )
            label.grid(row=0, column=index, padx=8, pady=4, sticky="w")

        button_frame = tk.Frame(table, bg="#323f4b")
        button_frame.pack(fill="x", pady=(8, 16))

        self.buttons: dict[str, tk.Button] = {}
        specs: list[tuple[str, str, Callable[[], None]]] = [
            ("hit", "Hit", self.on_hit),
            ("stand", "Stand", self.on_stand),
            ("exchange", "Exchange", self.on_exchange),
            ("one_more", "1More", self.on_one_more),
            ("restart", "Restart", self.on_restart),
            ("next", "Next Round", self.on_next_round),
            ("new", "New Game", self.on_new_game),
        ]
        for index, (key, text, command) in enumerate(specs):
            button = tk.Button(
                button_frame,
                text=text,
                command=command,
                font=("Helvetica", 11, "bold italic"),
                width=14,
                height=2,
                fg="#111111",
                bg="#f5f7fa",
                activeforeground="#111111",
                activebackground="#d9e2ec",
                disabledforeground="#7b8794",
                relief="raised",
                bd=2,
            )
            button.grid(row=index // 4, column=index % 4, padx=6, pady=6, sticky="ew")
            self.buttons[key] = button

            for col in range(4):
                button_frame.grid_columnconfigure(col, weight=1)

        message = tk.Label(
            table,
            textvariable=self.message_var,
            wraplength=650,
            justify="left",
            font=("Helvetica", 12),
            fg="#f0f4f8",
            bg="#52606d",
            padx=12,
            pady=10,
        )
        message.pack(fill="x")

        rules_frame = tk.LabelFrame(
            table,
            text="Rules",
            font=("Helvetica", 12, "bold italic"),
            fg="white",
            bg="#323f4b",
            bd=2,
            relief="groove",
            labelanchor="n",
            padx=12,
            pady=10,
        )
        rules_frame.pack(fill="both", expand=True, pady=(14, 0))

        rules_text = (
             "・Hit：カードを1枚引きます．\n"
            "・Stand：自分のターンを終了し，CPUがカードを引きます．\n"
            "・Exchange：自分とCPUの手札を交換します．\n"
            "・1More：2枚のカードから1枚を選んで手札に加えます．\n"
            "・Restart：現在のラウンドを最初からやり直します．\n"
            "・Next Round：勝利または引き分け後，次のバトルへ進みます．\n"
            "・New Game：勝利数とアイテム数をリセットします．\n\n"
            "目標：21を超えない範囲で，CPUより高い点数を目指します．\n"
            "Aは1または11として扱われます．"
        )

        rules_label = tk.Label(
            rules_frame,
            text=rules_text,
            justify="left",
            anchor="nw",
            font=("Helvetica", 11),
            fg="#f0f4f8",
            bg="#323f4b",
        )
        rules_label.pack(fill="both", expand=True)

    def _create_hand_frame(self, parent: tk.Widget, title: str, score_var: tk.StringVar) -> tk.LabelFrame:
        frame = tk.LabelFrame(
            parent,
            text=title,
            font=("Helvetica", 13, "bold"),
            fg="white",
            bg="#323f4b",
            bd=2,
            relief="groove",
            labelanchor="n",
            padx=12,
            pady=10,
            )
        card_area = tk.Frame(frame, bg="#323f4b")
        card_area.pack(fill="x", pady=(0, 8))
        setattr(self, f"{title.lower()}_card_area", card_area)

        score = tk.Label(
            frame,
            textvariable=score_var,
            font=("Helvetica", 13),
            fg="#d9e2ec",
            bg="#323f4b",
            anchor="w",
        )
        score.pack(fill="x")
        return frame

    def _render_cards(self, area: tk.Frame, cards: list[str]) -> None:
        for child in area.winfo_children():
            child.destroy()
        for card in cards:
            suit = card[0]
            fg = "#d64545" if suit in ("♥", "♦") else "#111111"
            label = tk.Label(
                area,
                text=card,
                font=("Helvetica", 20, "bold"),
                fg=fg,
                bg="#f5f7fa",
                width=5,
                height=2,
                relief="raised",
                bd=3,
            )
            label.pack(side="left", padx=6, pady=4)

    def refresh(self) -> None:
        state = self.game.get_state()
        self.wins_var.set(f"Wins: {state['wins']}")
        self.cpu_score_var.set(f"Score: {state['cpu_score']}" + ("  BUST" if state["cpu_bust"] else ""))
        self.player_score_var.set(
            f"Score: {state['player_score']}" + ("  BUST" if state["player_bust"] else "")
        )
        self.message_var.set(state["message"])

        for item_name, count in state["items"].items():
            self.item_vars[item_name].set(f"{item_name}: {count}")

        self._render_cards(self.cpu_card_area, state["cpu_cards"])
        self._render_cards(self.player_card_area, state["player_cards"])
        self._update_buttons(state)

    def _update_buttons(self, state: dict) -> None:
        phase = state["phase"]
        player_turn = phase == "PLAYER_TURN"
        round_end = phase == "ROUND_END"
        game_over = phase == "GAME_OVER"

        self.buttons["hit"].config(state="normal" if player_turn else "disabled")
        self.buttons["stand"].config(state="normal" if player_turn else "disabled")
        self.buttons["exchange"].config(
            state="normal" if player_turn and state["items"]["Exchange"] > 0 else "disabled"
        )
        self.buttons["one_more"].config(
            state="normal" if player_turn and state["items"]["1More"] > 0 else "disabled"
        )
        self.buttons["restart"].config(
            state="normal" if player_turn and state["items"]["Restart"] > 0 else "disabled"
        )
        self.buttons["next"].config(state="normal" if round_end else "disabled")
        self.buttons["new"].config(state="normal" if game_over or round_end else "normal")

    def on_hit(self) -> None:
        self.game.hit()
        self.refresh()
        self._notify_result_if_needed()

    def on_stand(self) -> None:
        self.game.stand()
        self.refresh()
        self._notify_result_if_needed()

    def on_exchange(self) -> None:
        self.game.exchange()
        self.refresh()
        self._notify_result_if_needed()

    def on_one_more(self) -> None:
        state = self.game.request_one_more()
        pending = state.get("pending_one_more")
        if not pending:
            self.refresh()
            return
        choice = messagebox.askyesno(
            "1More",
            f"Choose a card.\n\nYes: {pending[0]}\nNo: {pending[1]}",
        )
        self.game.choose_one_more("A" if choice else "B")
        self.refresh()
        self._notify_result_if_needed()

    def on_restart(self) -> None:
        self.game.restart_round()
        self.refresh()
        self._notify_result_if_needed()

    def on_next_round(self) -> None:
        self.game.next_round()
        self.refresh()

    def on_new_game(self) -> None:
        if messagebox.askyesno("New Game", "Reset wins and items?"):
            self.game.new_game()
            self.refresh()

    def _notify_result_if_needed(self) -> None:
        state = self.game.get_state()
        if state["phase"] in ("ROUND_END", "GAME_OVER") and state["result"]:
            result = state["result"]
            messagebox.showinfo(result["title"], result["detail"])


def run() -> None:
    app = BlackjackApp()
    app.mainloop()
