import pygame

CELL = 40
CELL_HALF = CELL / 2

MAP1_KD = (
    "###############\n"
    "#S    #       #\n"
    "#K###D# ##### #\n"
    "#   # #     # #\n"
    "### # ##### # #\n"
    "#   #     # # #\n"
    "# ####### # # #\n"
    "#      K# #   #\n"
    "# ##### # #####\n"
    "#     #   D   #\n"
    "##### #######G#\n"
    "###############\n"
)


def _create_key_image():
    key_image = pygame.Surface((CELL, CELL), pygame.SRCALPHA)
    pyrect1 = pygame.Rect((CELL_HALF - 2, CELL_HALF - 2, 18, 3))
    pyrect2 = pygame.Rect((CELL_HALF + 4, CELL_HALF, 2, 7))
    pyrect3 = pygame.Rect((CELL_HALF + 10, CELL_HALF, 3, 4))
    pygame.draw.circle(key_image, (100, 100, 100), (CELL_HALF - 10, CELL_HALF), 10, width=6)
    pygame.draw.rect(key_image, (100, 100, 100), pyrect1.inflate(3, 3))
    pygame.draw.rect(key_image, (100, 100, 100), pyrect2.inflate(3, 3))
    pygame.draw.rect(key_image, (100, 100, 100), pyrect3.inflate(3, 3))
    pygame.draw.circle(key_image, (255, 255, 0), (CELL_HALF - 10, CELL_HALF), 8, width=2)
    pygame.draw.rect(key_image, (255, 255, 0), pyrect1)
    pygame.draw.rect(key_image, (255, 255, 0), pyrect2)
    pygame.draw.rect(key_image, (255, 255, 0), pyrect3)
    return key_image


def _create_door_image():
    door_image = pygame.Surface((CELL, CELL), pygame.SRCALPHA)
    pygame.draw.circle(door_image, (189, 89, 19), (CELL_HALF, CELL_HALF), CELL_HALF - 2)
    pygame.draw.circle(door_image, (89, 42, 9), (CELL_HALF, CELL_HALF), CELL_HALF - 6, width=2)
    pygame.draw.rect(door_image, (189, 89, 19), (2, CELL_HALF, CELL - 4, CELL_HALF - 1))
    pygame.draw.line(door_image, (89, 42, 9), (CELL_HALF - 1, 6), (CELL_HALF - 1, CELL - 2), 2)
    pygame.draw.line(door_image, (89, 42, 9), (5, CELL_HALF), (5, CELL - 2), 2)
    pygame.draw.line(door_image, (89, 42, 9), (CELL - 7, CELL_HALF), (CELL - 7, CELL - 2), 2)
    pygame.draw.circle(door_image, (89, 42, 9), (CELL_HALF - 6, CELL_HALF + 4), 2)
    pygame.draw.circle(door_image, (89, 42, 9), (CELL_HALF + 6, CELL_HALF + 4), 2)
    return door_image


_door_image = _create_door_image()
_key_image = _create_key_image()


class KeysAndDoors:
    """
    マップの鍵とドアを管理するクラス
    """

    @classmethod
    def from_serialized_data(cls, data: str):
        """
        文字列化されたマップデータから鍵とドアの座標を取り出して、それを元にKeysAndDoorsのインスタンスを生成する。  
        マップデータについて: 改行区切り、鍵を`K`、ドアを`D`で表す。  
        引数: 文字列で表されたマップデータ
        """
        keys: list[tuple[int, int]] = []
        doors: list[tuple[int, int]] = []
        for y, l in enumerate(data.splitlines()):
            for x, c in enumerate(l):
                if c == "K":
                    keys.append((x, y))
                elif c == "D":
                    doors.append((x, y))
        return cls(keys, doors)

    def __init__(self, keys: list[tuple[int, int]], doors: list[tuple[int, int]]):
        """
        引数: 鍵の2D座標のリスト、ドアの2D座標のリスト
        """
        self.__current_key_count = 0
        self.__initial_keys = keys
        self.__initial_doors = doors
        self.__keys = keys[:]
        self.__doors = doors[:]

    def reset(self):
        """
        初期状態に戻す
        """
        self.__current_key_count = 0
        self.__keys = self.__initial_keys[:]
        self.__doors = self.__initial_doors[:]

    def is_walkable(self, x: int, y: int) -> bool:
        """
        現在所持している鍵の数や、その座標にドアがあるかをもとに、walkableなマスかどうかを判定する。  
        引数: 座標 x, y  
        戻り値: walkableかどうか
        """
        return self.__current_key_count >= 1 or (x, y) not in self.__doors

    def on_visit(self, x: int, y: int):
        """
        プレイヤーがその座標に移動したことを、KeysAndDoorsインスタンスに知らせるためのメソッド。  
        その座標に鍵があればそれを拾う。鍵を持った状態でドアに移動したなら、ドアを開ける。  
        引数: 座標 x, y
        """
        self.__try_pick_up_key(x, y)
        self.__try_unlock(x, y)

    def draw(self, screen: pygame.Surface):
        """
        `screen: Surface` に鍵とドアを描画する
        """
        for door_x, door_y in self.__doors:
            screen.blit(_door_image, (door_x * CELL, door_y * CELL, CELL, CELL))
        for key_x, key_y in self.__keys:
            screen.blit(_key_image, (key_x * CELL, key_y * CELL, CELL, CELL))

    def __try_unlock(self, x: int, y: int):
        """
        内部用関数。指定された座標のドアを開錠する
        """
        if self.__current_key_count < 1:
            return
        if (x, y) not in self.__doors:
            return
        self.__doors.remove((x, y))
        self.__current_key_count -= 1

    def __try_pick_up_key(self, x: int, y: int):
        """
        内部用関数。指定された座標の鍵を拾う
        """
        if (x, y) not in self.__keys:
            return
        self.__keys.remove((x, y))
        self.__current_key_count += 1

