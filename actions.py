# 行動ブロックの定義
# 行動は register(ラベル, 色, アクションの種類) を書くと
# 行動選択画面のパレットに自動で追加される
# main.py の match 文にアクションの具体的な処理が書かれているので
# そこにもコードを追加をする必要がある
from dataclasses import dataclass
from typing import Callable
from enum import Enum, auto


class ActionKind(Enum):
    MoveUp = auto()
    MoveDown = auto()
    MoveLeft = auto()
    MoveRight = auto()


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
