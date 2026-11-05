
import pygame
import random
import math
import time

from enemy import Goblin, Orc, Demon
from character import Archer, Healer, Adventurer, Scout


# ==========================================
# GAME INITIALIZATION
# ==========================================

pygame.init()
pygame.font.init()

WIDTH = 1100
HEIGHT = 700

SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Character Defense")

CLOCK = pygame.time.Clock()

WHITE = (255, 255, 255)
BLACK = (20, 20, 20)
GREEN = (80, 150, 75)
DARK_GREEN = (45, 105, 50)
BROWN = (135, 95, 55)
YELLOW = (255, 215, 0)
RED = (220, 50, 50)
BLUE = (60, 130, 230)
PURPLE = (150, 80, 200)

FONT = pygame.font.SysFont("arial", 24, bold=True)
BIG_FONT = pygame.font.SysFont("arial", 55, bold=True)


# ==========================================
# ENEMY PATH
# ==========================================

PATH = [
    (-30, 180),
    (200, 180),
    (200, 400),
    (450, 400),
    (450, 200),
    (700, 200),
    (700, 500),
    (1050, 500)
]


# ==========================================
# MAIN LOOP CLASS
# ==========================================

class MainLoop:

    def __init__(self):

        self.running = True
        self.in_start = True

        self.money = 1000
        self.lives = 30
        self.wave = 1

        self.enemies = []
        self.towers = []
        self.projectiles = []

        self.moving_tower = None
        self.selected_tower = None

        self.paused = True
        self.game_over = False
        self.win = False

        self.spawn_timer = time.time()
        self.spawn_delay = 1.5
        self.enemies_to_spawn = 5

        # Character shop
        self.tower_types = {
            "Archer": {
                "cost": 100,
                "color": (50, 150, 50)
            },
            "Healer": {
                "cost": 200,
                "color": (255, 100, 150)
            },
            "Adventurer": {
                "cost": 300,
                "color": (70, 100, 200)
            },
            "Scout": {
                "cost": 150,
                "color": (255, 180, 50)
            }
        }

        # Shop buttons
        self.shop_buttons = {
            "Archer": pygame.Rect(850, 150, 220, 60),
            "Healer": pygame.Rect(850, 225, 220, 60),
            "Adventurer": pygame.Rect(850, 300, 220, 60),
            "Scout": pygame.Rect(850, 375, 220, 60)
        }

        self.start_button = pygame.Rect(400, 350, 300, 80)
        self.play_button = pygame.Rect(850, 470, 220, 55)

    # ======================================
    # START SCREEN
    # ======================================

    def start_screen(self):

        while self.running and self.in_start:

            for event in pygame.event.get():

                if event.type == pygame.QUIT:
                    self.running = False

                if event.type == pygame.MOUSEBUTTONDOWN:

                    if self.start_button.collidepoint(event.pos):
                        self.in_start = False
                        self.paused = False

            SCREEN.fill((30, 45, 65))

            title = BIG_FONT.render(
                "CHARACTER DEFENSE",
                True,
                WHITE
            )

            SCREEN.blit(
                title,
                (
                    WIDTH // 2 - title.get_width() // 2,
                    180
                )
            )

            pygame.draw.rect(
                SCREEN,
                GREEN,
                self.start_button,
                border_radius=12
            )

            start_text = FONT.render(
                "START GAME",
                True,
                WHITE
            )

            SCREEN.blit(
                start_text,
                (
                    self.start_button.centerx -
                    start_text.get_width() // 2,
                    self.start_button.centery -
                    start_text.get_height() // 2
                )
            )

            pygame.display.update()
            CLOCK.tick(60)

        if self.running:
            self.main()

    # ======================================
    # ADD CHARACTER / TOWER
    # ======================================

    def add_tower(self, tower_name):

        if tower_name not in self.tower_types:
            return

        cost = self.tower_types[tower_name]["cost"]

        if self.money < cost:
            print("[ACTION] Not enough coins!")
            return

        if tower_name == "Archer":
            tower = Archer(0, 0)

        elif tower_name == "Healer":
            tower = Healer(0, 0)

        elif tower_name == "Adventurer":
            tower = Adventurer(0, 0)

        elif tower_name == "Scout":
            tower = Scout(0, 0)

        else:
            return

        self.money -= cost
        self.moving_tower = tower

        print(f"[ACTION] Selected {tower_name}.")

    # ======================================
    # CHECK TOWER PLACEMENT
    # ======================================

    def point_to_line(self, tower):

        tower_rect = pygame.Rect(
            tower.x - 25,
            tower.y - 25,
            50,
            50
        )

        # Keep towers inside the map.
        if tower.x < 30 or tower.x > 820:
            return False

        if tower.y < 30 or tower.y > HEIGHT - 30:
            return False

        # Prevent towers from being placed on the road.
        for index in range(len(PATH) - 1):

            start = PATH[index]
            end = PATH[index + 1]

            path_rect = pygame.Rect(
                min(start[0], end[0]) - 25,
                min(start[1], end[1]) - 25,
                abs(end[0] - start[0]) + 50,
                abs(end[1] - start[1]) + 50
            )

            if tower_rect.colliderect(path_rect):
                return False

        # Prevent tower overlapping.
        for existing_tower in self.towers:

            distance = math.hypot(
                tower.x - existing_tower.x,
                tower.y - existing_tower.y
            )

            if distance < 55:
                return False

        return True

    # ======================================
    # SPAWN ENEMIES
    # ======================================

    def spawn_enemy(self):

        if self.enemies_to_spawn <= 0:
            return

        if self.wave <= 5:
            enemy = Goblin(self.wave)

        elif self.wave <= 10:
            enemy = Orc(self.wave)

        else:
            enemy = Demon(self.wave)

        enemy.x = PATH[0][0]
        enemy.y = PATH[0][1]
        enemy.path_index = 1

        self.enemies.append(enemy)
        self.enemies_to_spawn -= 1

        print(f"[ENEMY] Enemy spawned in Wave {self.wave}.")

    # ======================================
    # MOVE ENEMIES
    # ======================================

    def move_enemy(self, enemy):

        if not hasattr(enemy, "path_index"):
            enemy.path_index = 1

        if enemy.path_index >= len(PATH):
            return True

        target_x, target_y = PATH[enemy.path_index]

        dx = target_x - enemy.x
        dy = target_y - enemy.y

        distance = math.hypot(dx, dy)

        speed = getattr(enemy, "speed", 1)

        if distance <= speed:

            enemy.x = target_x
            enemy.y = target_y
            enemy.path_index += 1

        elif distance > 0:

            enemy.x += (dx / distance) * speed
            enemy.y += (dy / distance) * speed

        return enemy.path_index >= len(PATH)

    # ======================================
    # CHARACTER ATTACK
    # ======================================

    def tower_attack(self):

        for tower in self.towers:

            # Healer supports other characters instead of attacking.
            if tower.__class__.__name__ == "Healer":
                continue

            if not self.enemies:
                continue

            attack_range = getattr(
                tower,
                "attack_range",
                150
            )

            damage = getattr(
                tower,
                "damage",
                10
            )

            cooldown = getattr(
                tower,
                "cooldown",
                1
            )

            if not hasattr(tower, "last_attack"):
                tower.last_attack = 0

            if time.time() - tower.last_attack < cooldown:
                continue

            for enemy in self.enemies:

                distance = math.hypot(
                    tower.x - enemy.x,
                    tower.y - enemy.y
                )

                if distance <= attack_range:

                    enemy.take_damage(damage)

                    tower.last_attack = time.time()

                    self.projectiles.append({
                        "x": tower.x,
                        "y": tower.y,
                        "target": enemy,
                        "color": getattr(
                            tower,
                            "color",
                            YELLOW
                        ),
                        "timer": 10
                    })

                    if enemy.get_health() <= 0:

                        reward = getattr(
                            enemy,
                            "reward",
                            20
                        )

                        self.money += reward

                        self.enemies.remove(enemy)

                        print(
                            f"[ACTION] Enemy defeated! "
                            f"+{reward} coins."
                        )

                    break

    # ======================================
    # HEALER SUPPORT
    # ======================================

    def healer_support(self):

        for healer in self.towers:

            if healer.__class__.__name__ != "Healer":
                continue

            if not hasattr(healer, "last_heal"):
                healer.last_heal = 0

            cooldown = getattr(
                healer,
                "cooldown",
                3
            )

            if time.time() - healer.last_heal < cooldown:
                continue

            healer_range = getattr(
                healer,
                "attack_range",
                150
            )

            for tower in self.towers:

                if tower is healer:
                    continue

                distance = math.hypot(
                    healer.x - tower.x,
                    healer.y - tower.y
                )

                if distance <= healer_range:

                    healer.last_heal = time.time()

                    # Visual indicator for healing.
                    self.projectiles.append({
                        "x": healer.x,
                        "y": healer.y,
                        "target": tower,
                        "color": (100, 255, 150),
                        "timer": 10
                    })

                    break

    # ======================================
    # UPDATE PROJECTILES
    # ======================================

    def update_projectiles(self):

        for projectile in self.projectiles[:]:

            projectile["timer"] -= 1

            if projectile["timer"] <= 0:
                self.projectiles.remove(projectile)

    # ======================================
    # DRAW MAP
    # ======================================

    def draw_map(self):

        SCREEN.fill(GREEN)

        # Grass details.
        for x in range(20, 830, 80):

            for y in range(20, HEIGHT, 80):

                pygame.draw.circle(
                    SCREEN,
                    DARK_GREEN,
                    (x, y),
                    2
                )

        # Enemy road.
        pygame.draw.lines(
            SCREEN,
            BROWN,
            False,
            PATH,
            55
        )

        pygame.draw.lines(
            SCREEN,
            (190, 150, 100),
            False,
            PATH,
            5
        )

        # Enemy entrance.
        pygame.draw.circle(
            SCREEN,
            RED,
            PATH[0],
            18
        )

        # Base.
        pygame.draw.circle(
            SCREEN,
            BLUE,
            PATH[-1],
            25
        )

    # ======================================
    # DRAW CHARACTERS
    # ======================================

    def draw_towers(self):

        for tower in self.towers:
            tower.draw(SCREEN)

        if self.moving_tower:

            mouse_x, mouse_y = pygame.mouse.get_pos()

            self.moving_tower.x = mouse_x
            self.moving_tower.y = mouse_y

            self.moving_tower.draw(SCREEN)

            attack_range = getattr(
                self.moving_tower,
                "attack_range",
                150
            )

            pygame.draw.circle(
                SCREEN,
                WHITE,
                (mouse_x, mouse_y),
                attack_range,
                1
            )

    # ======================================
    # DRAW ENEMIES
    # ======================================

    def draw_enemies(self):

        for enemy in self.enemies:
            enemy.draw(SCREEN)

    # ======================================
    # DRAW PROJECTILES
    # ======================================

    def draw_projectiles(self):

        for projectile in self.projectiles:

            target = projectile["target"]

            if target not in self.enemies and target not in self.towers:
                continue

            pygame.draw.line(
                SCREEN,
                projectile["color"],
                (int(projectile["x"]), int(projectile["y"])),
                (int(target.x), int(target.y)),
                4
            )

    # ======================================
    # DRAW SHOP
    # ======================================

    def draw_shop(self):

        pygame.draw.rect(
            SCREEN,
            (35, 35, 45),
            (840, 0, 260, HEIGHT)
        )

        title = FONT.render(
            "CHARACTER SHOP",
            True,
            WHITE
        )

        SCREEN.blit(title, (855, 90))

        for name, button in self.shop_buttons.items():

            color = self.tower_types[name]["color"]

            pygame.draw.rect(
                SCREEN,
                color,
                button,
                border_radius=8
            )

            cost = self.tower_types[name]["cost"]

            text = FONT.render(
                f"{name} - {cost}",
                True,
                WHITE
            )

            SCREEN.blit(
                text,
                (
                    button.centerx - text.get_width() // 2,
                    button.centery - text.get_height() // 2
                )
            )

        # Pause button.
        pygame.draw.rect(
            SCREEN,
            (70, 70, 80),
            self.play_button,
            border_radius=8
        )

        pause_text = FONT.render(
            "RESUME" if self.paused else "PAUSE",
            True,
            WHITE
        )

        SCREEN.blit(
            pause_text,
            (
                self.play_button.centerx -
                pause_text.get_width() // 2,
                self.play_button.centery -
                pause_text.get_height() // 2
            )
        )

    # ======================================
    # DRAW GAME INFORMATION
    # ======================================

    def draw_information(self):

        money_text = FONT.render(
            f"Coins: {self.money}",
            True,
            YELLOW
        )

        lives_text = FONT.render(
            f"Lives: {self.lives}",
            True,
            WHITE
        )

        wave_text = FONT.render(
            f"Wave: {self.wave}/15",
            True,
            WHITE
        )

        SCREEN.blit(money_text, (20, 20))
        SCREEN.blit(lives_text, (200, 20))
        SCREEN.blit(wave_text, (350, 20))

    # ======================================
    # REDRAW GAME WINDOW
    # ======================================

    def redraw_game_window(self):

        self.draw_map()
        self.draw_towers()
        self.draw_enemies()
        self.draw_projectiles()
        self.draw_shop()
        self.draw_information()

        pygame.display.update()

    # ======================================
    # HANDLE MOUSE CLICK
    # ======================================

    def handle_click(self, position):

        # Place selected character.
        if self.moving_tower:

            if self.point_to_line(self.moving_tower):

                self.towers.append(self.moving_tower)

                print("[ACTION] Character successfully placed!")

            else:

                tower_name = self.moving_tower.__class__.__name__

                self.money += self.tower_types[tower_name]["cost"]

                print("[ACTION] Invalid placement. Coins refunded.")

            self.moving_tower = None
            return

        # Check shop buttons.
        for name, button in self.shop_buttons.items():

            if button.collidepoint(position):

                self.add_tower(name)
                return

        # Pause and resume.
        if self.play_button.collidepoint(position):

            self.paused = not self.paused

            if self.paused:
                print("[ACTION] Game paused.")
            else:
                print("[ACTION] Game resumed.")

    # ======================================
    # GAME OVER SCREEN
    # ======================================

    def lose_screen(self):

        waiting = True

        while waiting and self.running:

            for event in pygame.event.get():

                if event.type == pygame.QUIT:
                    self.running = False
                    waiting = False

                if event.type == pygame.KEYDOWN:
                    self.running = False
                    waiting = False

                if event.type == pygame.MOUSEBUTTONDOWN:
                    self.running = False
                    waiting = False

            SCREEN.fill((35, 25, 35))

            title = BIG_FONT.render(
                "GAME OVER",
                True,
                RED
            )

            wave_text = FONT.render(
                f"You reached Wave {self.wave}",
                True,
                WHITE
            )

            SCREEN.blit(
                title,
                (
                    WIDTH // 2 - title.get_width() // 2,
                    250
                )
            )

            SCREEN.blit(
                wave_text,
                (
                    WIDTH // 2 - wave_text.get_width() // 2,
                    340
                )
            )

            info = FONT.render(
                "Press any key or click to exit",
                True,
                WHITE
            )

            SCREEN.blit(
                info,
                (
                    WIDTH // 2 - info.get_width() // 2,
                    420
                )
            )

            pygame.display.update()
            CLOCK.tick(30)

    # ======================================
    # VICTORY SCREEN
    # ======================================

    def win_screen(self):

        waiting = True

        while waiting and self.running:

            for event in pygame.event.get():

                if event.type == pygame.QUIT:
                    self.running = False
                    waiting = False

                if event.type == pygame.KEYDOWN:
                    self.running = False
                    waiting = False

                if event.type == pygame.MOUSEBUTTONDOWN:
                    self.running = False
                    waiting = False

            SCREEN.fill((25, 50, 75))

            title = BIG_FONT.render(
                "YOU WIN!",
                True,
                YELLOW
            )

            message = FONT.render(
                "Congratulations! You completed all 15 waves!",
                True,
                WHITE
            )

            SCREEN.blit(
                title,
                (
                    WIDTH // 2 - title.get_width() // 2,
                    250
                )
            )

            SCREEN.blit(
                message,
                (
                    WIDTH // 2 - message.get_width() // 2,
                    350
                )
            )

            info = FONT.render(
                "Press any key or click to exit",
                True,
                WHITE
            )

            SCREEN.blit(
                info,
                (
                    WIDTH // 2 - info.get_width() // 2,
                    420
                )
            )

            pygame.display.update()
            CLOCK.tick(30)

    # ======================================
    # MAIN GAME LOOP
    # ======================================

    def main(self):

        while self.running:

            CLOCK.tick(60)

            # Event handling.
            for event in pygame.event.get():

                if event.type == pygame.QUIT:
                    self.running = False

                if event.type == pygame.MOUSEBUTTONDOWN:

                    if event.button == 1:
                        self.handle_click(event.pos)

                if event.type == pygame.KEYDOWN:

                    if event.key == pygame.K_ESCAPE:
                        self.paused = not self.paused

            # Game updates.
            if not self.paused:

                # Spawn enemies.
                if (
                    self.enemies_to_spawn > 0
                    and time.time() - self.spawn_timer >= self.spawn_delay
                ):

                    self.spawn_enemy()
                    self.spawn_timer = time.time()

                # Move enemies.
                for enemy in self.enemies[:]:

                    reached_base = self.move_enemy(enemy)

                    if reached_base:

                        self.enemies.remove(enemy)
                        self.lives -= 1

                        print("[ACTION] An enemy reached your base!")

                # Character attacks.
                self.tower_attack()

                # Healer support.
                self.healer_support()

                # Update projectiles.
                self.update_projectiles()

                # Check wave completion.
                if (
                    self.enemies_to_spawn == 0
                    and len(self.enemies) == 0
                ):

                    if self.wave == 15:

                        self.win = True
                        self.running = False

                        print("[END] You completed all 15 waves!")

                    else:

                        self.wave += 1

                        # Increase enemy count for each wave.
                        self.enemies_to_spawn = 5 + (self.wave * 2)

                        self.spawn_timer = time.time()

                        print(
                            f"[WAVE] Starting Wave {self.wave}!"
                        )

                # Check player lives.
                if self.lives <= 0:

                    self.game_over = True
                    self.running = False

                    print("[END] Game Over! No more lives.")

            # Draw game.
            self.redraw_game_window()

        # Show final screen.
        if self.game_over:
            self.lose_screen()

        elif self.win:
            self.win_screen()

        pygame.quit()
