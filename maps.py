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

# 使用するマップの一覧（新しいマップはここに追加する）
MAPS = [MAP1, MAP_WHOLE]