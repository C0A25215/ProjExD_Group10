from abc import ABC, abstractmethod
import os

from actions import ActionKind
import pygame

os.chdir(os.path.dirname(os.path.abspath(__file__))) # これをここでやらないと pygame.image.load が死ぬ

CELL = 40


class Enemy(ABC):
    """迷路上の敵"""

    @abstractmethod
    def reset(self):
        """
        初期状態に戻す
        """
        pass

    @abstractmethod
    def step(self):
        """
        1ステップ分の行動をする
        """
        pass

    @abstractmethod
    def draw(self, screen: pygame.Surface):
        """
        Surfaceに自身を描画する
        """
        pass

    @property
    @abstractmethod
    def pos(self) -> tuple[int, int]:
        """
        現在の座標(x,y)を返す
        """
        pass


class TraceEnemy(Enemy):
    """
    数ステップ遅れてプレイヤーの動きを真似する敵
    """

    def __init__(self, delay: int):
        self.__image = pygame.transform.smoothscale(pygame.image.load("fig/enemy1.png"), (CELL, CELL))
        self.__initial_pos = None
        self.__actions: list[ActionKind] = []
        self.__delay = delay
        self.__step_index = 0
        self.__x, self.__y = None, None

    def set_initial_pos(self, initial_pos: tuple[int, int]):
        """
        敵の初期値を設定する
        """
        self.__initial_pos = initial_pos
        self.__x, self.__y = initial_pos

    def set_actions(self, actions: list[ActionKind]):
        """
        敵が真似するアクションを設定する
        """
        self.__actions = actions

    def reset(self):
        self.__step_index = 0
        self.__x, self.__y = self.__initial_pos

    def __move(self, dx: int, dy: int):
        self.__x += dx
        self.__y += dy

    def step(self):
        if self.__step_index >= self.__delay and self.__step_index - self.__delay < len(self.__actions):
            match self.__actions[self.__step_index - self.__delay]:
                case ActionKind.MoveUp:
                    self.__move(0, -1)
                case ActionKind.MoveDown:
                    self.__move(0, 1)
                case ActionKind.MoveLeft:
                    self.__move(-1, 0)
                case ActionKind.MoveRight:
                    self.__move(1, 0)
        self.__step_index += 1

    def draw(self, screen: pygame.Surface):
        if self.__step_index >= self.__delay:
            screen.blit(self.__image, (self.__x * CELL, self.__y * CELL))

    @property
    def pos(self) -> tuple[int, int]:
        if self.__step_index < self.__delay:
            return -1, -1
        return self.__x, self.__y


class PatrolEnemy(Enemy):
    """
    ルートを巡回する敵
    """

    def __init__(self, route: list[tuple[int, int]]):
        self.__image = pygame.transform.smoothscale(pygame.image.load("fig/enemy1.png"), (CELL, CELL))
        self.__lapla = pygame.transform.laplacian(self.__image)
        self.__lapla.set_alpha(150)
        self.__route = route
        self.__route_index = 0
        self.__idx_dir = 1 # 1 or -1

    def reset(self):
        self.__route_index = 0
        self.__idx_dir = 1

    def step(self):
        if (self.__idx_dir < 0 and self.__route_index == 0) or (self.__idx_dir > 0 and self.__route_index == len(self.__route) - 1):
            self.__idx_dir *= -1
        self.__route_index += self.__idx_dir

    def draw(self, screen: pygame.Surface):
        for i, (x, y) in enumerate(self.__route):
            if i == self.__route_index:
                screen.blit(self.__image, (x * CELL, y * CELL))
            else:
                screen.blit(self.__lapla, (x * CELL, y * CELL))

    @property
    def pos(self) -> tuple[int, int]:
        return self.__route[self.__route_index]


MAP1_ENEMIES = [
    PatrolEnemy([(1, 7), (2, 7), (3, 7), (4, 7), (5, 7), (6, 7), (7, 7)]),
    PatrolEnemy([(3, 3), (3, 4), (3, 5)]),
    TraceEnemy(5),
]
