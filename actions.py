# 行動ブロックの定義
# 新しい行動は @register(ラベル, 色) を付けた関数を書くだけで、
# 行動選択画面のパレットに自動で追加される
# 行動関数は引数 game (main.Game) を1つ受け取る
from dataclasses import dataclass
from typing import Callable
from enum import Enum, auto


class ActionKind(Enum):
    MoveUp = auto()
    MoveDown = auto()
    MoveLeft = auto()
    MoveRight = auto()
    Wait = auto()


@dataclass
class Action:
    label: str
    color: tuple[int, int, int]
    kind: ActionKind


ACTIONS: list[Action] = []  # 登録順にパレットへ並ぶ


def register(label: str, color: tuple[int, int, int], kind: ActionKind):
    ACTIONS.append(Action(label, color, kind))


register("↑ 上", (90, 140, 230), ActionKind.MoveUp)
register("↓ 下", (90, 140, 230), ActionKind.MoveDown)
register("← 左", (90, 140, 230), ActionKind.MoveLeft)
register("→ 右", (90, 140, 230), ActionKind.MoveRight)
