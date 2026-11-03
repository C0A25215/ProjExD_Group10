# 行動ブロックの定義
# 新しい行動は @register(ラベル, 色) を付けた関数を書くだけで、
# 行動選択画面のパレットに自動で追加される
# 行動関数は引数 game (main.Game) を1つ受け取る
from dataclasses import dataclass
from typing import Callable


@dataclass
class Action:
    label: str
    color: tuple[int, int, int]
    func: Callable


ACTIONS: list[Action] = []  # 登録順にパレットへ並ぶ


def register(label: str, color: tuple[int, int, int]):
    """行動関数をパレットに登録するデコレータ"""
    def deco(func: Callable) -> Callable:
        ACTIONS.append(Action(label, color, func))
        return func
    return deco


@register("↑ 上", (90, 140, 230))
def move_up(game) -> None:
    game.player.move(0, -1, game.maze)


@register("↓ 下", (90, 140, 230))
def move_down(game) -> None:
    game.player.move(0, 1, game.maze)


@register("← 左", (90, 140, 230))
def move_left(game) -> None:
    game.player.move(-1, 0, game.maze)


@register("→ 右", (90, 140, 230))
def move_right(game) -> None:
    game.player.move(1, 0, game.maze)
