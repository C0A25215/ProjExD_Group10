import random

# 迷路の定義
# 各マップは2次元リスト（要素は1文字の文字列）
#   "S": スタート  "G": ゴール  " ": 道  "#": 壁

# マスの種類ごとの性質（新しいマスを作るときはここに追加する）
TILES = {
    "#": {"color": (60, 60, 70), "walkable": False},
    " ": {"color": (235, 235, 225), "walkable": True},
    "S": {"color": (130, 200, 255), "walkable": True},
    "G": {"color": (255, 210, 80), "walkable": True},
}

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

class MazeGenerator:
    """12×15のランダム迷路を穴掘り法で生成するクラス"""

    def __init__(self):
        """迷路生成を初期化"""
        self.width = 15
        self.height = 12

    def generate(self):
        """ランダム迷路を生成
        Returns:
            list[list[str]]: 生成した迷路
        """

        self.maze = [
            ["#" for _ in range(self.width)]
            for _ in range(self.height)
        ]

        self._dig(1, 1)

        # スタートとゴールを配置
        self.maze[1][1] = "S"
        self.maze[10][13] = "G"

        # 必ず到達可能にする
        self.maze[2][1] = " "
        self.maze[10][12] = " "

        return self.maze

    def _dig(self, x, y):
        """再帰的に通路を掘る

        Args:
            x (int): 現在のx座標
            y (int): 現在のy座標
        """

        self.maze[y][x] = " "

        directions = [
            (0, -2),
            (0, 2),
            (-2, 0),
            (2, 0)
        ]

        random.shuffle(directions)

        for dx, dy in directions:

            nx = x + dx
            ny = y + dy

            if (
                0 < nx < self.width - 1
                and
                0 < ny < self.height - 1
                and
                self.maze[ny][nx] == "#"
            ):

                self.maze[y + dy // 2][x + dx // 2] = " "
                self._dig(nx, ny)

    def print_map(self, name="MAP2"):
        """maps.pyに貼り付け可能な形式で出力する"""

        print(f"{name} = [")

        for row in self.maze:
            print(f'list("{"".join(row)}"),')
        print("]")

generator = MazeGenerator()

MAP2 = generator.generate()

generator.print_map()

# 使用するマップの一覧（新しいマップはここに追加する）
MAPS = [MAP1, MAP2]
