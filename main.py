import pygame
import os
import sys

import actions
import maps

os.chdir(os.path.dirname(os.path.abspath(__file__)))

CELL = 40  # 迷路1マスの大きさ
PANEL_W = 320  # 右側の行動選択画面の幅
MIN_H = 600  # 画面の最小の高さ
STEP_MS = 300  # 実行時の1手の間隔（ミリ秒）
FPS = 60

BLOCK_W = 140  # ブロックの幅
BLOCK_H = 34  # ブロックの高さ
QUEUE_W = 60  # 行動リストに並ぶブロックの幅
QUEUE_H = 20  # 行動リストに並ぶブロックの高さ
QUEUE_COLS = 5  # 行動リストの列数
MARGIN = 2


def get_font(size: int) -> pygame.font.Font:
    """日本語を表示できるフォントを返す"""
    return pygame.font.SysFont("meiryo,yugothic,msgothic", size)


def draw_block(screen: pygame.Surface, rect: pygame.Rect, color: tuple, label: str,
               font: pygame.font.Font, highlight: bool = False) -> None:
    """スクラッチ風のブロックを描く（上端の凸で前のブロックとつながって見える）"""
    tab = pygame.Rect(rect.x + 14, rect.y - 5, 18, 6)
    pygame.draw.rect(screen, color, tab, border_radius=2)
    pygame.draw.rect(screen, color, rect, border_radius=6)
    border = (255, 255, 255) if highlight else (40, 40, 40)
    pygame.draw.rect(screen, border, rect, 3 if highlight else 1, border_radius=6)
    txt = font.render(label, True, (255, 255, 255))
    screen.blit(txt, txt.get_rect(midleft=(rect.x + 10, rect.centery)))


class Maze:
    """迷路（maps.py の2次元リスト）を扱うクラス"""

    def __init__(self, grid: list[list[str]]):
        self.grid = [row[:] for row in grid]  # 元のマップを書き換えないようにコピー
        self.h = len(self.grid)
        self.w = len(self.grid[0])

    def find(self, ch: str) -> tuple[int, int]:
        """文字 ch のマスの座標 (x, y) を返す"""
        for y, row in enumerate(self.grid):
            for x, c in enumerate(row):
                if c == ch:
                    return x, y
        raise ValueError(f"マップに {ch!r} がありません")

    def tile(self, x: int, y: int) -> str:
        return self.grid[y][x]

    def is_walkable(self, x: int, y: int) -> bool:
        if not (0 <= x < self.w and 0 <= y < self.h):
            return False
        return maps.TILES[self.tile(x, y)]["walkable"]

    def draw(self, screen: pygame.Surface) -> None:
        for y, row in enumerate(self.grid):
            for x, c in enumerate(row):
                rect = pygame.Rect(x * CELL, y * CELL, CELL, CELL)
                pygame.draw.rect(screen, maps.TILES[c]["color"], rect)
                pygame.draw.rect(screen, (200, 200, 190), rect, 1)


class Player:
    """迷路を進む主人公"""

    def __init__(self, pos: tuple[int, int]):
        self.image = pygame.transform.smoothscale(pygame.image.load("fig/kouka_zukin.png"), (CELL, CELL))
        self.reset(pos)

    def reset(self, pos: tuple[int, int]) -> None:
        self.x, self.y = pos

    def move(self, dx: int, dy: int, maze: Maze) -> bool:
        """移動先が通れれば1マス動く。動けたら True"""
        nx, ny = self.x + dx, self.y + dy
        if not maze.is_walkable(nx, ny):
            return False
        self.x, self.y = nx, ny
        return True

    def draw(self, screen: pygame.Surface) -> None:
        screen.blit(self.image, (self.x * CELL, self.y * CELL))


class Button:
    """クリックで on_click を呼ぶボタン（パレットのブロック・削除・実行に使う）"""

    def __init__(self, rect: pygame.Rect, label: str, color: tuple, on_click, font: pygame.font.Font):
        self.rect = rect
        self.label = label
        self.color = color
        self.on_click = on_click
        self.font = font
        self.enabled = True

    def handle(self, event: pygame.event.Event) -> None:
        if (self.enabled and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1
                and self.rect.collidepoint(event.pos)):
            self.on_click()

    def draw(self, screen: pygame.Surface) -> None:
        color = self.color if self.enabled else (150, 150, 150)
        draw_block(screen, self.rect, color, self.label, self.font)


class Game:
    """ゲーム全体の状態をまとめるクラス（行動関数はこれを受け取る）"""

    def __init__(self, grid: list[list[str]]):
        self.maze = Maze(grid)
        self.start = self.maze.find("S")
        self.goal = self.maze.find("G")
        self.player = Player(self.start)
        self.queue: list[actions.Action] = []  # 行動リスト
        self.running = False  # 実行中か
        self.step_index = 0  # 次に実行する行動の番号
        self.timer = 0
        self.message = ""

        self.maze_w = self.maze.w * CELL
        self.width = self.maze_w + PANEL_W
        self.height = max(self.maze.h * CELL, MIN_H)
        self.font = get_font(18)
        self.big_font = get_font(48)
        self.buttons: list[Button] = []
        self.palette_buttons: list[Button] = []
        self._layout()

    # ---------- 画面の配置 ----------
    def _layout(self) -> None:
        px = self.maze_w + MARGIN
        y = 40
        # パレット: actions.ACTIONS から自動で並べる（2列）
        for i, act in enumerate(actions.ACTIONS):
            col, row = i % 2, i // 2
            rect = pygame.Rect(px + col * (BLOCK_W + MARGIN), y + row * (BLOCK_H + MARGIN), BLOCK_W, BLOCK_H)
            btn = Button(rect, act.label, act.color, lambda a=act: self.add(a), self.font)
            self.palette_buttons.append(btn)
        rows = (len(actions.ACTIONS) + 1) // 2
        self.queue_top = y + rows * (BLOCK_H + MARGIN) + 40

        # 削除・実行ボタン（画面下）
        by = self.height - BLOCK_H - MARGIN
        self.delete_button = Button(pygame.Rect(px, by, BLOCK_W, BLOCK_H), "削除",
                                    (210, 80, 80), self.pop, self.font)
        self.run_button = Button(pygame.Rect(px + BLOCK_W + MARGIN, by, BLOCK_W, BLOCK_H), "実行",
                                 (70, 170, 90), self.run, self.font)
        self.buttons = self.palette_buttons + [self.delete_button, self.run_button]

        # 行動リストに並べられる最大数
        self.queue_rows = max(1, (by - MARGIN - self.queue_top) // QUEUE_H)
        self.max_queue = self.queue_rows * QUEUE_COLS

    def queue_rect(self, i: int) -> pygame.Rect:
        """行動リストの i 番目のブロックの位置（縦につなげ、あふれたら次の列へ）"""
        col, row = divmod(i, self.queue_rows)
        x = self.maze_w + MARGIN + col * (QUEUE_W + MARGIN)
        return pygame.Rect(x, self.queue_top + row * QUEUE_H, QUEUE_W, QUEUE_H)

    # ---------- 行動リストの操作 ----------
    def add(self, action: actions.Action) -> None:
        if len(self.queue) < self.max_queue:
            self.queue.append(action)

    def pop(self) -> None:
        if self.queue:
            self.queue.pop()

    def run(self) -> None:
        """スタートに戻して行動リストを先頭から実行する"""
        if not self.queue:
            return
        self.player.reset(self.start)
        self.running = True
        self.step_index = 0
        self.timer = 0
        self.message = ""

    # ---------- フック（追加機能はここを拡張する） ----------
    def on_enter(self, tile: str) -> None:
        """プレイヤーが1手動いた後に、今いるマスの文字を受け取って呼ばれる"""
        pass

    def on_goal(self) -> None:
        """ゴールに着いたときに呼ばれる"""
        self.running = False
        self.message = "GOAL!"

    def on_finish(self) -> None:
        """ゴールせずに行動リストを最後まで実行したときに呼ばれる"""
        self.running = False
        self.message = "ゴールに届かなかった…"

    # ---------- 毎フレームの処理 ----------
    def handle_event(self, event: pygame.event.Event) -> None:
        for btn in self.buttons:
            btn.handle(event)

    def update(self, dt: int) -> None:
        for btn in self.palette_buttons:
            btn.enabled = not self.running
        self.delete_button.enabled = not self.running
        self.run_button.enabled = not self.running and bool(self.queue)

        if not self.running:
            return
        self.timer += dt
        if self.timer < STEP_MS:
            return
        self.timer = 0
        self.queue[self.step_index].func(self)
        self.step_index += 1
        self.on_enter(self.maze.tile(self.player.x, self.player.y))
        if (self.player.x, self.player.y) == self.goal:
            self.on_goal()
        elif self.step_index >= len(self.queue):
            self.on_finish()

    def draw(self, screen: pygame.Surface) -> None:
        screen.fill((30, 30, 40))
        self.maze.draw(screen)
        self.player.draw(screen)
        self._draw_panel(screen)
        if self.message:
            txt = self.big_font.render(self.message, True, (255, 60, 60))
            rect = txt.get_rect(center=(self.maze_w // 2, self.maze.h * CELL // 2))
            pygame.draw.rect(screen, (255, 255, 255), rect.inflate(30, 16), border_radius=10)
            screen.blit(txt, rect)

    def _draw_panel(self, screen: pygame.Surface) -> None:
        panel = pygame.Rect(self.maze_w, 0, PANEL_W, self.height)
        pygame.draw.rect(screen, (245, 245, 250), panel)
        px = self.maze_w + MARGIN
        screen.blit(self.font.render("ブロックを選ぶ", True, (40, 40, 40)), (px, 10))
        screen.blit(self.font.render(f"行動リスト ({len(self.queue)}/{self.max_queue})", True,
                                     (40, 40, 40)), (px, self.queue_top - 32))
        for i, act in enumerate(self.queue):
            current = self.running and i == self.step_index
            draw_block(screen, self.queue_rect(i), act.color, act.label, self.font, highlight=current)
        for btn in self.buttons:
            btn.draw(screen)


def main():
    pygame.display.set_caption("こうか頭巾")
    # game = Game(maps.MAPS[1])の中身の数字を1にするとランダムマップに切り替えられます
    # 0なら通常モード
    game = Game(maps.MAPS[1])
    screen = pygame.display.set_mode((game.width, game.height))
    clock = pygame.time.Clock()
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            game.handle_event(event)
        game.update(clock.get_time())
        game.draw(screen)
        pygame.display.update()
        clock.tick(FPS)


if __name__ == "__main__":
    pygame.init()
    main()
    pygame.quit()
    sys.exit()
