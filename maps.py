import random
from dataclasses import dataclass

from enemy import Enemy, MAP3_ENEMIES
from keys_and_doors import MAP3_KD

# 迷路の定義
# 各マップは2次元リスト（要素は1文字の文字列）
#   "S": スタート  "G": ゴール  " ": 道  "#": 壁 "W": 落とし穴

# マスの種類ごとの性質（新しいマスを作るときはここに追加する）
from typing import Self

TILES = {
    "#": {"color": (60, 60, 70), "walkable": False},
    " ": {"color": (235, 235, 225), "walkable": True},
    "S": {"color": (130, 200, 255), "walkable": True},
    "G": {"color": (255, 210, 80), "walkable": True},
    "W": {"color": (235, 234, 225), "walkable": True}
}

class Tile:
    """迷路のマスに関するクラス"""
    def __init__(self, sign: str, color: tuple[int], walkable: bool):
        self.sign = sign
        self.color = color
        self.walkable = walkable

    @staticmethod
    def from_str(tile_str: list[str]) -> list[Self]:
        """
        文字列のリストからTileインスタンスのリストに変換する関数
        引数1: 迷路の文字列のリスト
        """
        tiles = []
        for tile in tile_str:
            tiles.append(Tile(tile, TILES[tile]["color"], TILES[tile]["walkable"]))

        return tiles


MAP1 = [
    list("###############"),
    list("#S    #       #"),
    list("# ### # ##### #"),
    list("#   # #     # #"),
    list("### # ##### # #"),
    list("#   #     # # #"),
    list("# ####### # # #"),
    list("#       # #   #"),
    list("# ##### # #####"),
    list("#     #       #"),
    list("##### #######G#"),
    list("###############"),
]

# 上・中・下の3ルート。上と中は序盤に穴(W)があり、下だけが安全
MAP_WHOLE = [
    list("###############"),
    list("#  W          #"),
    list("# ########### #"),
    list("# ########### #"),
    list("# ########### #"),
    list("#S W         G#"),
    list("# ########### #"),
    list("# ########### #"),
    list("# ########### #"),
    list("#             #"),
    list("###############"),
]

class MazeGenerator:
    """15×15のランダム迷路を穴掘り法で生成するクラス"""

    def __init__(self):
        """迷路生成サイズを設定"""
        self.width = 15
        self.height = 15

    def generate(self):
        """ランダム迷路を生成して返す"""
        # 一度すべて壁で埋める
        self.maze = [
            ["#" for _ in range(self.width)]
            for _ in range(self.height)
        ]
        #x1, y1(スタート)地点を掘る
        self._dig(1, 1)

        # スタート地点を配置
        self.maze[1][1] = "S"
        # ゴール地点の設置
        self.maze[13][13] = "G"

        # 必ず到達可能にする
        # マップサイズ変更により廃止
        # self.maze[10][13] = " "

        return self.maze

    def _dig(self, x, y):
        """指定座標から再帰的に通路を掘る"""

        # 現在地点を通路にする
        self.maze[y][x] = " "

        # 上下左右2マス先を探索候補とする
        directions = [
            (0, -2),
            (0, 2),
            (-2, 0),
            (2, 0)
        ]

        # 掘る方向をランダムに並べ替える
        random.shuffle(directions)

        for dx, dy in directions:

            nx = x + dx
            ny = y + dy

            # 範囲内かつ未探索の壁なら掘り進める
            if (
                0 < nx < self.width - 1
                and
                0 < ny < self.height - 1
                and
                self.maze[ny][nx] == "#"
            ):

                # 現在地と次の地点の間を通路にする
                self.maze[y + dy // 2][x + dx // 2] = " "
                # 再帰的に掘り進める
                self._dig(nx, ny)

    def print_map(self, name="MAP2"):
        """生成したマップをMAP形式で出力する"""
        print(f"{name} = [")

        for row in self.maze:
            print(f'list("{"".join(row)}"),')
        print("]")
# ランダム迷路生成器を作成
generator = MazeGenerator()
# ランダムマップをMAPに2に挿入
MAP2 = generator.generate()
# 生成された迷路をターミナルへ出力
generator.print_map()

@dataclass
class MapData:
    grid: list[list[str]]
    key_door_data: str
    enemies: list[Enemy]

# 使用するマップの一覧（新しいマップはここに追加する）
MAPS = [
    MapData(MAP1, "", []),
    MapData(MAP_WHOLE, "", []),
    MapData(MAP2, "", []),
    MapData(MAP1, MAP3_KD, MAP3_ENEMIES),
]
