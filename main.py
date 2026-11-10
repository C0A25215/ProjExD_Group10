import pygame
import os
import sys

import actions
import maps
from keys_and_doors import KeysAndDoors, MAP3_KD
from enemy import Enemy, TraceEnemy, MAP3_ENEMIES

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

    def __init__(self, grid: list[list[str]], keys_and_doors: KeysAndDoors):
        self.grid = [maps.Tile.from_str(tiles) for tiles in grid]  # 元のマップを書き換えないようにコピー
        self.h = len(self.grid)
        self.w = len(self.grid[0])
        self.keys_and_doors = keys_and_doors

    def find(self, ch: str) -> tuple[int, int]:
        """文字 ch のマスの座標 (x, y) を返す"""
        for y, row in enumerate(self.grid):
            for x, c in enumerate(row):
                if c.sign == ch:
                    return x, y
        raise ValueError(f"マップに {ch!r} がありません")

    # def tile(self, x: int, y: int) -> str:
    #     return self.grid[y][x]

    def is_walkable(self, x: int, y: int) -> bool:
        if not (0 <= x < self.w and 0 <= y < self.h):
            return False
        if not self.keys_and_doors.is_walkable(x, y):
            return False
        return self.grid[y][x].walkable

    def draw(self, screen: pygame.Surface) -> None:
        for y, row in enumerate(self.grid):
            for x, c in enumerate(row):
                rect = pygame.Rect(x * CELL, y * CELL, CELL, CELL)
                pygame.draw.rect(screen, c.color, rect)
                pygame.draw.rect(screen, (200, 200, 190), rect, 1)
        self.keys_and_doors.draw(screen)


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

class AudioPlayer:
    """指定ディレクトリ内の音声ファイルを再生するクラス"""

    def __init__(self, music_dir: str, volume: float = 0.5):
        """AudioPlayerオブジェクトの初期化
            music_dir (str): 音声ファイルが保存されているディレクトリ名
            volume (float): 初期音量(0.0～1.0)
            mp3, wav, ogg以外だと正しく認識しないらしいので注意
        """
        pygame.mixer.init()
        self.music_dir = music_dir
        self.volume = volume

        self.files = [
            os.path.join(music_dir, f)
            for f in os.listdir(music_dir)
            if f.lower().endswith((".mp3", ".wav", ".ogg"))
            ]

        self.index = 0
        pygame.mixer.music.set_volume(self.volume)

    def play(self):
        """選択されている音声ファイルを再生
        音声ファイルが存在しない場合は何もしない
        ループ再生にしてある
        """
        if not self.files:
            return

        pygame.mixer.music.load(self.files[self.index])
        pygame.mixer.music.play(-1)

    def next(self):
        """次の音声ファイルへ切り替える
        最終ファイルの場合は先頭のファイルに
        """
        if not self.files:
            return

        self.index = (self.index + 1) % len(self.files)
        self.play()

    def volume_up(self):
        """音量を0.1(10%)上げる
        音量の上限は1.0(100%)
        """
        self.volume = min(1.0, self.volume + 0.1)
        pygame.mixer.music.set_volume(self.volume)

    def volume_down(self):
        """音量を0.1(10%)下げる
        音量の下限は0.0(100%)
        """
        self.volume = max(0.0, self.volume - 0.1)
        pygame.mixer.music.set_volume(self.volume)

class Game:
    """ゲーム全体の状態をまとめるクラス（行動関数はこれを受け取る）"""

    def __init__(self, grid: list[list[str]], keys_and_doors: KeysAndDoors, enemies: list[Enemy]):
        self.maze = Maze(grid, keys_and_doors)
        self.maze_bk = Maze(grid, keys_and_doors)
        self.start = self.maze.find("S")
        self.goal = self.maze.find("G")
        self.player = Player(self.start)
        self.queue: list[actions.Action] = []  # 行動リスト
        self.running = False  # 実行中か
        self.cleared = False
        self.quit_requested = False
        self.step_index = 0  # 次に実行する行動の番号
        self.timer = 0
        self.message = ""
        for enemy in enemies:
            if isinstance(enemy, TraceEnemy):
                enemy.set_initial_pos(self.start)
                enemy.set_maze(self.maze)
        self.enemies: list[Enemy] = enemies

        self.maze_w = self.maze.w * CELL
        self.width = self.maze_w + PANEL_W
        self.height = max(self.maze.h * CELL, MIN_H)
        self.font = get_font(18)
        self.big_font = get_font(48)
        self.clear_font = get_font(28)
        self.buttons: list[Button] = []
        self.palette_buttons: list[Button] = []
        self.audio = AudioPlayer("music", 0.3)
        self.audio.play()
        self._layout()

        button_w = 220
        button_h = 48

        bx = (self.width - button_w) // 2

        self.clear_retry_button = Button(
            pygame.Rect(bx, 445, button_w, button_h),
            "もう一度遊ぶ",
            (60, 170, 90),
            self.retry,
            self.clear_font
        )

        self.clear_exit_button = Button(
            pygame.Rect(bx, 515, button_w, button_h),
            "終了",
            (200, 75, 75),
            self.exit_game,
            self.clear_font
        )

        self.clear_buttons = [
            self.clear_retry_button,
            self.clear_exit_button
        ]

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
        self.run_button = Button(pygame.Rect(px + BLOCK_W + MARGIN, by, BLOCK_W, BLOCK_H), "実行", (70, 170, 90), self.run, self.font)
        self.buttons = self.palette_buttons + [self.delete_button, self.run_button]

        # 行動リストに並べられる最大数
        self.queue_rows = max(1, (by - MARGIN - self.queue_top) // QUEUE_H)
        self.max_queue = self.queue_rows * QUEUE_COLS


        # 音量調整機能
        volume_y = by - 60

        # 音量ボタンの位置指定
        self.vol_down_button = Button(pygame.Rect(px - 240, volume_y + 60, 70, BLOCK_H), "音量-", (80, 80, 200), self.audio.volume_down, self.font)

        self.vol_up_button = Button(pygame.Rect(px -160, volume_y + 60, 70, BLOCK_H), "音量+", (80, 200, 80), self.audio.volume_up, self.font)

        # 音量ボタンを追加
        self.buttons += [
        self.vol_down_button,
        self.vol_up_button
        ]

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
        for enemy in self.enemies:
            enemy.reset()
            if isinstance(enemy, TraceEnemy):
                enemy.set_actions([act.kind for act in self.queue])
        self.maze.keys_and_doors.reset()
        self.running = True
        self.step_index = 0
        self.timer = 0
        self.message = ""

    def retry(self) -> None:
        self.cleared = False
        self.running = False

        for enemy in self.enemies:
            enemy.reset()
        self.maze.keys_and_doors.reset()

        self.player.reset(self.start)
        self.queue.clear()

        self.step_index = 0
        self.timer = 0
        self.message = ""

    def exit_game(self) -> None:
        self.quit_requested = True

    # ---------- フック（追加機能はここを拡張する） ----------
    def on_enter(self, tile: maps.Tile, x: int, y: int) -> None:
        """プレイヤーが1手動いた後に、今いるマスの文字を受け取って呼ばれる"""
        if tile.sign == "W":
            self.maze.grid[y][x].color = (255, 0, 0) # 落ちた穴のマスを赤に
            self.running = False
            self.message = "穴に落ちてしまった..."

    def on_goal(self) -> None:
        """ゴールに着いたときに呼ばれる"""
        self.maze = self.maze_bk # 迷路を初期化して穴についた色をリセット
        self.running = False
        self.cleared = True
        self.message = "GOAL!"

    def on_finish(self) -> None:
        """ゴールせずに行動リストを最後まで実行したときに呼ばれる"""
        self.running = False
        self.message = "ゴールに届かなかった…"

    def on_killed(self) -> None:
        """敵に捕まったときに呼ばれる"""
        self.running = False
        self.message = "敵に捕まった…"

    # ---------- 毎フレームの処理 ----------
    def handle_event(self, event: pygame.event.Event) -> None:
        if self.cleared:
            for btn in self.clear_buttons:
                btn.handle(event)
            return

        for btn in self.buttons:
            btn.handle(event)
        if event.type == pygame.KEYDOWN and not self.running:#実行されてない場合キーボードが押されてら処理する
            key_actions ={
                pygame.K_UP:"↑ 上",#キーボードの上矢印が浅れた場合actions.pyの↑ 上のブロックを追加する
                pygame.K_DOWN:"↓ 下",#キーボードの下矢印が浅れた場合actions.pyの↓ 下のブロックを追加する
                pygame.K_LEFT:"← 左",#キーボードの左矢印が浅れた場合actions.pyの← 左のブロックを追加する
                pygame.K_RIGHT:"→ 右"#キーボードの右矢印が浅れた場合actions.pyの→ 右のブロックを追加する
            }
            if event.key in key_actions:
                direction = key_actions[event.key]#対応するキーを取得して代入
        
                for act in actions.ACTIONS:
                    if act.label == direction:#行動とキーが一緒なら
                        self.add(act)#行動を追加する
                        break

        if event.type == pygame.KEYDOWN and not self.running:
            if event.key == pygame.K_RETURN:
                self.run()

        if event.type == pygame.KEYDOWN and not self.running:
            if event.key == pygame.K_BACKSPACE:
                self.pop()

    def update(self, dt: int) -> None:
        if self.cleared:
            return
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
        match self.queue[self.step_index].kind:
            case actions.ActionKind.MoveUp:
                self.player.move(0, -1, self.maze)
            case actions.ActionKind.MoveDown:
                self.player.move(0, 1, self.maze)
            case actions.ActionKind.MoveLeft:
                self.player.move(-1, 0, self.maze)
            case actions.ActionKind.MoveRight:
                self.player.move(1, 0, self.maze)
        self.step_index += 1
        self.maze.keys_and_doors.on_visit(self.player.x, self.player.y)
        for enemy in self.enemies:
            enemy.step()
        self.on_enter(self.maze.grid[self.player.y][self.player.x], self.player.x, self.player.y)
        if (self.player.x, self.player.y) == self.goal:
            self.on_goal()
        elif any((self.player.x, self.player.y) == enemy.pos for enemy in self.enemies):
            self.on_killed()
        elif self.step_index >= len(self.queue):
            self.on_finish()

    def draw(self, screen: pygame.Surface) -> None:
        if self.cleared:
            self.draw_clear(screen)
            return

        screen.fill((30, 30, 40))

        self.maze.draw(screen)
        self.player.draw(screen)
        for enemy in self.enemies:
            enemy.draw(screen)

        self._draw_panel(screen)

        if self.message:
            txt = self.big_font.render(
                self.message,
                True,
                (255, 60, 60)
            )

            rect = txt.get_rect(
                center=(
                    self.maze_w // 2,
                    self.maze.h * CELL // 2
                )
            )

            pygame.draw.rect(
                screen,
                (255, 255, 255),
                rect.inflate(30, 16),
                border_radius=10
            )
            screen.blit(txt, rect)

    def draw_clear(self, screen: pygame.Surface) -> None:
        screen.fill((35, 45, 70))

        # 背景の装飾
        for x, y, r in [
            (60, 70, 5),
            (self.width - 70, 90, 6),
            (100, 330, 5),
            (self.width - 100, 350, 5),
            (self.width // 2 - 170, 180, 4),
            (self.width // 2 + 170, 180, 4)
        ]:
            pygame.draw.circle(
                screen, (255, 220, 100),
                (x, y), r
            )

        # クリア画面のタイトル
        title = self.big_font.render(
            "GAME CLEAR!",
            True,
            (255, 220, 70)
        )

        screen.blit(
            title,
            title.get_rect(
                center=(self.width // 2, 85)
            )
        )

        # 赤ずきんのイラストを大きく表示
        character = pygame.transform.smoothscale(
            self.player.image,
            (120, 120)
        )

        screen.blit(
            character,
            character.get_rect(
                center=(self.width // 2, 250)
            )
        )

        # クリアメッセージ
        message = self.clear_font.render(
            "おめでとう！",
            True,
            (255, 255, 255)
        )

        screen.blit(
            message,
            message.get_rect(
                center=(self.width // 2, 350)
            )
        )

        sub_message = self.font.render(
            "迷路をクリアしました！",
            True,
            (230, 230, 230)
        )

        screen.blit(
            sub_message,
            sub_message.get_rect(
                center=(self.width // 2, 390)
            )
        )

        # クリア画面のボタン
        for btn in self.clear_buttons:
            btn.draw(screen)

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
    # game = Game(maps.MAPS[0])の中身の数字を2にするとランダムマップに切り替えられます
    # 0なら通常モード
    seleted_map = maps.MAPS[3]
    game = Game(seleted_map.grid, KeysAndDoors.from_serialized_data(seleted_map.key_door_data), seleted_map.enemies)
    screen = pygame.display.set_mode((game.width, game.height))
    clock = pygame.time.Clock()
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            game.handle_event(event)
        if game.quit_requested:
            return
        game.update(clock.get_time())
        game.draw(screen)
        pygame.display.update()
        clock.tick(FPS)


if __name__ == "__main__":
    pygame.init()
    main()
    pygame.quit()
    sys.exit()
