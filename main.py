import pygame
import random
import os
from pygame import mixer


def path_gen(path):
    return r"\\".join(str(os.path.abspath(__file__)).split("\\")[0:-1]) + r"\\" + path


pygame.init()
mixer.init()

SCREEN_WIDTH = 400
SCREEN_HEIGHT = 600
SCROLL_THRESH = 200
GRAVITY = 1
MAX_PLATFORMS = 10


WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREY = (100, 100, 100)


font_small = pygame.font.SysFont("Lucida Sans", 20)
font_big = pygame.font.SysFont("Lucida Sans", 24)

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Игрулька")
icon = pygame.image.load(path_gen(r"assets\ghost.png"))
pygame.display.set_icon(icon)

pygame.mixer.music.load(path_gen(r"assets\fuyu-biyori bgm.mp3"))
pygame.mixer.music.set_volume(0.9)
pygame.mixer.music.play(-1, 0.0)
jump_fx = pygame.mixer.Sound(path_gen(r"assets\jump.mp3"))
jump_fx.set_volume(1)
death_fx = pygame.mixer.Sound(path_gen(r"assets\death.mp3"))
death_fx.set_volume(1)

jumpy_image = pygame.image.load(path_gen(r"assets\bocchi1.png")).convert_alpha()
bg_image = pygame.image.load(path_gen(r"assets\background2.png")).convert_alpha()
platform_image = pygame.image.load(path_gen(r"assets\wood.png")).convert_alpha()
bird_sheet_img = pygame.image.load(path_gen(r"assets\bird.png")).convert_alpha()


clock = pygame.time.Clock()
FPS = 60


def load_high_score():
    score_path = path_gen(r"score.txt")
    if os.path.exists(score_path):
        with open(score_path, "r") as file:
            try:
                return int(file.read())
            except:
                return 0
    else:
        return 0


def save_high_score(score):
    score_path = path_gen(r"score.txt")
    with open(score_path, "w") as file:
        file.write(str(score))


class Slider:
    def __init__(self, x, y, width, min_val, max_val, initial, label):
        self.rect = pygame.Rect(x, y, width, 20)
        self.min_val = min_val
        self.max_val = max_val
        self.value = initial
        self.handle_pos = x + (initial - min_val) / (max_val - min_val) * width
        self.dragging = False
        self.label = label
        self.font = pygame.font.SysFont("Lucida Sans", 16)

    def draw(self, screen):
        pygame.draw.rect(screen, (200, 200, 200), self.rect)
        handle_rect = pygame.Rect(self.handle_pos - 5, self.rect.y - 5, 10, 30)
        pygame.draw.rect(screen, (100, 100, 100), handle_rect)
        label_surf = self.font.render(
            f"{self.label}: {int(self.value * 100)}%", True, WHITE
        )
        draw_outlined_text(
            label_surf, self.font, BLACK, screen, self.rect.x, self.rect.y - 25
        )

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.dragging = True
        elif event.type == pygame.MOUSEBUTTONUP:
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION:
            if self.dragging:
                mouse_x = event.pos[0]
                self.handle_pos = max(
                    self.rect.x, min(mouse_x, self.rect.x + self.rect.width)
                )
                ratio = (self.handle_pos - self.rect.x) / self.rect.width
                self.value = self.min_val + ratio * (self.max_val - self.min_val)


def draw_outlined_text(text_surf, font, outline_color, screen, x, y, center=False):
    outline_range = [-1, 0, 1]
    for ox in outline_range:
        for oy in outline_range:
            if ox != 0 or oy != 0:
                pos = (x + ox, y + oy)
                if center:
                    screen.blit(text_surf, text_surf.get_rect(center=(x + ox, y + oy)))
                else:
                    screen.blit(text_surf, (x + ox, y + oy))
    if center:
        screen.blit(text_surf, text_surf.get_rect(center=(x, y)))
    else:
        screen.blit(text_surf, (x, y))


def draw_text_with_outline(text, font, color, outline_color, x, y, center=False):
    text_surf = font.render(text, True, color)
    draw_outlined_text(text_surf, font, outline_color, screen, x, y, center)


def draw_panel():
    draw_text_with_outline("SCORE: " + str(score), font_small, WHITE, BLACK, 10, 10)


def draw_bg(scroll):
    screen.blit(bg_image, (0, scroll))
    screen.blit(bg_image, (0, scroll - SCREEN_HEIGHT))


class SpriteSheet:
    def __init__(self, sheet):
        self.sheet = sheet

    def get_image(self, frame, width, height, scale, color):
        image = pygame.Surface((width, height), pygame.SRCALPHA).convert_alpha()
        image.blit(self.sheet, (0, 0), (frame * width, 0, width, height))
        image = pygame.transform.scale(image, (int(width * scale), int(height * scale)))
        image.set_colorkey(color)
        return image


class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, spritesheet, scale, speed=2):
        super().__init__()
        self.spritesheet = SpriteSheet(spritesheet)
        self.images = self.load_images(scale)
        self.current_frame = 0
        self.image = self.images[self.current_frame]
        self.rect = self.image.get_rect(center=(x, y))
        self.speed = speed
        self.animation_time = 0.1
        self.current_time = 0
        self.mask = pygame.mask.from_surface(self.image)

    def load_images(self, scale):
        images = []
        for frame in range(4):
            image = self.spritesheet.get_image(frame, 64, 64, scale, (0, 0, 0))
            images.append(image)
        return images

    def update_animation(self, dt):
        self.current_time += dt
        if self.current_time >= self.animation_time:
            self.current_time = 0
            self.current_frame = (self.current_frame + 1) % len(self.images)
            self.image = self.images[self.current_frame]
            self.mask = pygame.mask.from_surface(self.image)

    def update(self, scroll, screen_width, dt, difficulty):
        self.update_animation(dt)
        self.rect.x -= self.speed * difficulty
        self.rect.y += scroll
        if self.rect.right < 0:
            self.kill()


class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.original_image = pygame.transform.scale(jumpy_image, (45, 45))
        self.image = self.original_image
        self.rect = self.image.get_rect(center=(x, y))
        self.vel_y = 0
        self.flip = False
        self.mask = pygame.mask.from_surface(self.image)

    def move(self, platforms, jump_fx, difficulty):
        scroll = 0
        dx = 0
        dy = 0
        key = pygame.key.get_pressed()
        if key[BINDS["move_left"]]:  # Используем бинды вместо pygame.K_a
            dx = -10 * difficulty
            self.flip = False
        if key[BINDS["move_right"]]:  # Используем бинды вместо pygame.K_d
            dx = 10 * difficulty
            self.flip = True
        self.vel_y += GRAVITY
        dy += self.vel_y
        self.rect.x += dx
        # Экранирование игрока с противоположной стороны
        if self.rect.right < 0:
            self.rect.left = SCREEN_WIDTH
        elif self.rect.left > SCREEN_WIDTH:
            self.rect.right = 0
        for platform in platforms:
            if platform.rect.colliderect(
                self.rect.x, self.rect.y + dy, self.rect.width, self.rect.height
            ):
                if self.vel_y > 0 and self.rect.bottom < platform.rect.centery:
                    self.rect.bottom = platform.rect.top
                    dy = 0
                    self.vel_y = -20
                    jump_fx.play()
        if self.rect.top <= SCROLL_THRESH and self.vel_y < 0:
            scroll = -dy
        self.rect.y += dy + scroll
        self.mask = pygame.mask.from_surface(self.image)
        return scroll

    def update(self):
        if self.flip:
            self.image = pygame.transform.flip(self.original_image, True, False)
        else:
            self.image = self.original_image
        self.mask = pygame.mask.from_surface(self.image)

    def draw(self):
        screen.blit(self.image, self.rect)


class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, width, moving, destroyable=False, player=None):
        super().__init__()
        self.image = pygame.transform.scale(platform_image, (width, 10))
        self.moving = moving
        self.move_counter = random.randint(0, 50)
        self.direction = random.choice([-1, 1])
        self.speed = random.randint(1, 2)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.destroyable = destroyable
        self.player = player
        self.is_stepped_on = False  # Новый атрибут для отслеживания прыжка
        self.original_image = self.image  # Сохраняем оригинальный спрайт
        self.destroyable_image = pygame.image.load(
            path_gen(r"assets\wood2.png")
        ).convert_alpha()  # Загрузка спрайта разрушенной платформы
        self.destroyable_image = pygame.transform.scale(
            self.destroyable_image, (width, 10)
        )

    def update(self, scroll, difficulty, player):
        if self.moving:
            self.move_counter += 1
            self.rect.x += self.direction * self.speed * difficulty
            if (
                self.move_counter >= 100
                or self.rect.left < 0
                or self.rect.right > SCREEN_WIDTH
            ):
                self.direction *= -1
                self.move_counter = 0
        self.rect.y += scroll
        if self.rect.top > SCREEN_HEIGHT:
            self.kill()

        # Проверяем прыжок и устанавливаем платформу как "задействованную"
        if self.destroyable and self.rect.colliderect(player.rect):
            if not self.is_stepped_on:
                self.is_stepped_on = True
                self.image = self.destroyable_image  # Меняем спрайт на `wood2`

        # Разрушаем платформу с 25% шансом, если она уже использована
        if self.is_stepped_on and not self.rect.colliderect(player.rect):
            if random.random() < 0.25:  # 25% шанс
                self.kill()  # Уничтожаем платформу


import json


class GameSettings:
    def __init__(self):
        global BINDS
        self.key_bindings = {
            "move_left": pygame.K_a,
            "move_right": pygame.K_d,
            "pause": pygame.K_p,
            "menu": pygame.K_m,
            "start": pygame.K_RETURN,
            "settings": pygame.K_s,
            "quit": pygame.K_q,
            "back": pygame.K_b,
        }
        BINDS = self.key_bindings  # Инициализация глобальных биндов
        self.forbidden_keys = [
            pygame.K_UP,
            pygame.K_DOWN,
            pygame.K_BACKSPACE,
            pygame.K_r,
        ]  # Запрещенные клавиши
        self.load_key_bindings()

    def load_key_bindings(self):
        global BINDS
        try:
            with open(path_gen(r"key_bindings.json"), "r") as file:
                self.key_bindings = json.load(file)
                BINDS = self.key_bindings  # Обновляем глобальные бинды
        except FileNotFoundError:
            pass

    def save_key_bindings(self):
        with open(path_gen(r"key_bindings.json"), "w") as file:
            json.dump(self.key_bindings, file)

    def rebind_key(self, action, new_key):
        global BINDS  # Указываем, что работаем с глобальной переменной

        # Проверка на запрещенные клавиши
        if new_key in self.forbidden_keys:
            print(f"Клавиша {pygame.key.name(new_key)} запрещена для бинда.")
            return False

        # Проверка, используется ли уже эта клавиша
        if new_key in self.key_bindings.values():
            print(
                f"Клавиша {pygame.key.name(new_key)} уже используется для другого действия."
            )
            return False

        if action in self.key_bindings:
            self.key_bindings[action] = new_key
            self.save_key_bindings()
            BINDS = self.key_bindings  # Обновляем глобальные бинды
            return True
        return False


BINDS = GameSettings().key_bindings


class RebindMenu:
    def __init__(self, game_settings):
        self.game_settings = game_settings
        self.rebind_menu_items = [
            {
                "action": "move_left",
                "key": self.game_settings.key_bindings["move_left"],
                "text": "Движение влево",
            },
            {
                "action": "move_right",
                "key": self.game_settings.key_bindings["move_right"],
                "text": "Движение вправо",
            },
            {
                "action": "pause",
                "key": self.game_settings.key_bindings["pause"],
                "text": "Пауза",
            },
            {
                "action": "menu",
                "key": self.game_settings.key_bindings["menu"],
                "text": "Меню",
            },
            {
                "action": "start",
                "key": self.game_settings.key_bindings["start"],
                "text": "Старт",
            },
            {
                "action": "settings",
                "key": self.game_settings.key_bindings["settings"],
                "text": "Настройки",
            },
            {
                "action": "quit",
                "key": self.game_settings.key_bindings["quit"],
                "text": "Выход",
            },
            {
                "action": "back",
                "key": self.game_settings.key_bindings["back"],
                "text": "Назад",
            },
        ]
        self.selected_item = 0

    def draw(self, screen):
        screen.fill(BLACK)
        draw_text_with_outline(
            "Чтобы выйти - нажмите BACKSPACE",
            font_small,
            WHITE,
            BLACK,
            SCREEN_WIDTH // 2,
            50,
            True,
        )
        draw_text_with_outline(
            "Перемещение по позициям -",
            font_small,
            WHITE,
            BLACK,
            SCREEN_WIDTH // 2,
            100,
            True,
        )
        draw_text_with_outline(
            "стрелка вверх и стрелка вниз",
            font_small,
            WHITE,
            BLACK,
            SCREEN_WIDTH // 2,
            130,
            True,
        )
        for i, item in enumerate(self.rebind_menu_items):
            text = item["text"] + ": " + pygame.key.name(item["key"])
            if i == self.selected_item:
                text = "> " + text
            draw_text_with_outline(
                text, font_small, WHITE, BLACK, SCREEN_WIDTH // 2, 200 + i * 50, True
            )

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.selected_item = (self.selected_item - 1) % len(
                    self.rebind_menu_items
                )
            elif event.key == pygame.K_DOWN:
                self.selected_item = (self.selected_item + 1) % len(
                    self.rebind_menu_items
                )
            elif (
                event.key != pygame.K_UP
                and event.key != pygame.K_DOWN
                and event.key != pygame.K_BACKSPACE
            ):
                action = self.rebind_menu_items[self.selected_item]["action"]
                new_key = event.key
                if self.game_settings.rebind_key(action, new_key):
                    self.rebind_menu_items[self.selected_item]["key"] = new_key
            elif event.key == pygame.K_BACKSPACE:
                self.game_settings.rebind_mode = False
                self.game_settings.rebind_action = None
                self.game_settings.rebind_new_key = None


def main_menu(high_score):
    menu = True
    difficulty = 1.0
    while menu:
        screen.fill(BLACK)
        draw_bg(0)
        draw_text_with_outline(
            "Jumpy Game",
            font_big,
            WHITE,
            BLACK,
            SCREEN_WIDTH // 2,
            SCREEN_HEIGHT // 2 - 100,
            True,
        )
        draw_text_with_outline(
            f'Начать игру ({pygame.key.name(BINDS["start"])})',
            font_small,
            WHITE,
            BLACK,
            SCREEN_WIDTH // 2,
            SCREEN_HEIGHT // 2,
            True,
        )
        draw_text_with_outline(
            f'Настройки ({pygame.key.name(BINDS["settings"])})',
            font_small,
            WHITE,
            BLACK,
            SCREEN_WIDTH // 2,
            SCREEN_HEIGHT // 2 + 30,
            True,
        )
        draw_text_with_outline(
            f"Бинды (r)",
            font_small,
            WHITE,
            BLACK,
            SCREEN_WIDTH // 2,
            SCREEN_HEIGHT // 2 + 90,
            True,
        )
        draw_text_with_outline(
            f'Выход ({pygame.key.name(BINDS["quit"])})',
            font_small,
            WHITE,
            BLACK,
            SCREEN_WIDTH // 2,
            SCREEN_HEIGHT // 2 + 60,
            True,
        )
        draw_text_with_outline(
            f"Рекорд: {high_score}",
            font_small,
            WHITE,
            BLACK,
            SCREEN_WIDTH // 2,
            SCREEN_HEIGHT // 2 + 120,
            True,
        )
        pygame.display.update()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            if event.type == pygame.KEYDOWN:
                if event.key == BINDS["start"]:
                    menu = False
                    main_game(high_score, difficulty)
                if event.key == BINDS["quit"]:
                    pygame.quit()
                    quit()
                if event.key == BINDS["settings"]:
                    difficulty = settings_menu()
                if event.key == pygame.K_r:
                    game_settings = GameSettings()
                    reb = RebindMenu(game_settings)
                    reb_menu = True
                    while reb_menu:
                        reb.draw(screen)
                        for event in pygame.event.get():
                            if event.type == pygame.QUIT:
                                pygame.quit()
                                quit()
                            reb.handle_event(event)
                            if event.type == pygame.KEYDOWN:
                                if event.key == pygame.K_BACKSPACE:
                                    reb_menu = False
                        pygame.display.update()
                    menu = True
                if event.key == pygame.K_i:
                    print(BINDS)


def settings_menu():
    settings = True
    music_volume = pygame.mixer.music.get_volume()
    jump_volume_val = jump_fx.get_volume() if jump_fx else 0
    death_volume_val = death_fx.get_volume() if death_fx else 0
    difficulty = 1.0
    music_slider = Slider(100, 150, 200, 0.0, 1.0, music_volume, "Music Volume")
    jump_slider = Slider(100, 200, 200, 0.0, 1.0, jump_volume_val, "Jump Volume")
    death_slider = Slider(100, 250, 200, 0.0, 1.0, death_volume_val, "Death Volume")
    difficulty_slider = Slider(100, 300, 200, 0.5, 3.0, difficulty, "Difficulty")
    while settings:
        screen.fill(GREY)
        draw_bg(0)
        draw_text_with_outline(
            "Настройки", font_big, WHITE, BLACK, SCREEN_WIDTH // 2, 50, True
        )
        music_slider.draw(screen)
        jump_slider.draw(screen)
        death_slider.draw(screen)
        difficulty_slider.draw(screen)
        draw_text_with_outline(
            f'Назад ({pygame.key.name(BINDS["back"])})',
            font_small,
            WHITE,
            BLACK,
            SCREEN_WIDTH // 2,
            400,
            True,
        )
        pygame.display.update()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            music_slider.handle_event(event)
            jump_slider.handle_event(event)
            death_slider.handle_event(event)
            difficulty_slider.handle_event(event)
            if event.type == pygame.KEYDOWN:
                if event.key == BINDS["back"]:
                    settings = False
    pygame.mixer.music.set_volume(music_slider.value)
    if jump_fx:
        jump_fx.set_volume(jump_slider.value)
    if death_fx:
        death_fx.set_volume(death_slider.value)
    return difficulty_slider.value


def game_over_screen(score, high_score):
    game_over = True
    if score > high_score:
        high_score = score
        save_high_score(high_score)
    while game_over:
        screen.fill(BLACK)
        draw_bg(0)
        draw_text_with_outline(
            "GAME OVER!",
            font_big,
            WHITE,
            BLACK,
            SCREEN_WIDTH // 2,
            SCREEN_HEIGHT // 2 - 50,
            True,
        )
        draw_text_with_outline(
            f"SCORE: {score}",
            font_big,
            WHITE,
            BLACK,
            SCREEN_WIDTH // 2,
            SCREEN_HEIGHT // 2,
            True,
        )
        draw_text_with_outline(
            f'PRESS {pygame.key.name(BINDS["start"])} TO PLAY AGAIN',
            font_big,
            WHITE,
            BLACK,
            SCREEN_WIDTH // 2,
            SCREEN_HEIGHT // 2 + 50,
            True,
        )
        pygame.display.update()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            if event.type == pygame.KEYDOWN:
                if event.key == BINDS["start"]:
                    game_over = False
                    main_game(high_score, 1.0)


def pause_menu():
    paused = True
    while paused:
        screen.fill(GREY)
        draw_bg(0)
        draw_text_with_outline(
            "ПАУЗА",
            font_big,
            WHITE,
            BLACK,
            SCREEN_WIDTH // 2,
            SCREEN_HEIGHT // 2 - 50,
            True,
        )
        draw_text_with_outline(
            f'Продолжить ({pygame.key.name(BINDS["pause"])})',
            font_small,
            WHITE,
            BLACK,
            SCREEN_WIDTH // 2,
            SCREEN_HEIGHT // 2,
            True,
        )
        draw_text_with_outline(
            f'Главное меню ({pygame.key.name(BINDS["menu"])})',
            font_small,
            WHITE,
            BLACK,
            SCREEN_WIDTH // 2,
            SCREEN_HEIGHT // 2 + 30,
            True,
        )
        pygame.display.update()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            if event.type == pygame.KEYDOWN:
                if event.key == BINDS["pause"]:  # Используем бинды вместо pygame.K_p
                    paused = False
                if event.key == BINDS["menu"]:  # Используем бинды вместо pygame.K_m
                    paused = False
                    main_menu(high_score)


def main_game(high_score, difficulty=1.0):
    global score
    player = Player(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 150)
    platform_group = pygame.sprite.Group()
    enemy_group = pygame.sprite.Group()
    initial_platform = Platform(SCREEN_WIDTH // 2 - 50, SCREEN_HEIGHT - 50, 100, False)
    platform_group.add(initial_platform)
    scroll = 0
    bg_scroll = 0
    game_over = False
    score = 0
    fade_counter = 0
    while True:
        dt = clock.tick(FPS) / 1000
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                if score > high_score:
                    high_score = score
                    save_high_score(high_score)
                pygame.quit()
                quit()
            if event.type == pygame.KEYDOWN:
                if event.key == BINDS["pause"] and not game_over:
                    pause_menu()

        if not game_over:
            scroll = player.move(platform_group, jump_fx, difficulty)
            player.update()
            bg_scroll += scroll * difficulty
            if bg_scroll >= SCREEN_HEIGHT:
                bg_scroll = 0
            draw_bg(bg_scroll)
            if len(platform_group) < MAX_PLATFORMS:
                p_w = random.randint(40, 60)
                p_x = random.randint(0, SCREEN_WIDTH - p_w)
                highest_platform = min(platform.rect.y for platform in platform_group)
                p_y = highest_platform - random.randint(30, 80)
                p_type = random.randint(1, 2)
                p_moving = True if p_type == 1 and score > 1000 else False
                p_destroyable = (
                    True if random.random() < 0.25 else False
                )  # 25% шанс сделать платформу разрушаемой
                new_platform = Platform(
                    p_x, p_y, p_w, p_moving, destroyable=p_destroyable, player=player
                )
                platform_group.add(new_platform)
            platform_group.update(scroll * difficulty, difficulty, player)
            if len(enemy_group) == 0 and score > 2000:
                enemy = Enemy(
                    SCREEN_WIDTH,
                    random.randint(100, SCREEN_HEIGHT - 100),
                    bird_sheet_img,
                    1.5,
                    speed=2 * difficulty,
                )
                enemy_group.add(enemy)
            enemy_group.update(scroll * difficulty, SCREEN_WIDTH, dt, difficulty)
            if scroll > 0:
                score += scroll * difficulty
            pygame.draw.line(
                screen,
                WHITE,
                (0, score - high_score + SCROLL_THRESH),
                (SCREEN_WIDTH, score - high_score + SCROLL_THRESH),
                3,
            )
            draw_text_with_outline(
                "HIGH SCORE",
                font_small,
                WHITE,
                BLACK,
                SCREEN_WIDTH - 130,
                score - high_score + SCROLL_THRESH,
                False,
            )
            platform_group.draw(screen)
            enemy_group.draw(screen)
            player.draw()
            draw_panel()
            if player.rect.top > SCREEN_HEIGHT:
                game_over = True
                death_fx.play()
            if pygame.sprite.spritecollide(
                player, enemy_group, False, pygame.sprite.collide_mask
            ):
                game_over = True
                death_fx.play()
        else:
            game_over_screen(score, high_score)
        pygame.display.update()


high_score = load_high_score()
main_menu(high_score)
pygame.quit()
