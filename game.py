import pygame
import random
import math
import time

WIDTH, HEIGHT = 800, 560
FPS = 60
BG = (30,35,25)


class Zombie:
    SPEED = 1.5
    SIZE = 30
    HP = 3
    COLOR = (60,140,60)

    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, self.SIZE, self.SIZE)
        self.color = self.COLOR
        self.hp = self.HP
        self.wobble = random.uniform(0, 6.28)
        self.frame = 0

    def update(self, player_pos):
        px, py = player_pos
        cx, cy = self.rect.center
        dx, dy = px-cx, py-cy
        dist = (dx**2+dy**2)**0.5

        if dist:
            self.rect.x += int(dx/dist*self.SPEED)
            self.rect.y += int(dy/dist*self.SPEED)

        self.frame += 1

    def hit(self):
        self.hp -= 1
        return self.hp <= 0

    def draw(self, screen):
        wobble_y = int(math.sin(self.frame*0.2)*3)
        draw_rect = self.rect.move(0, wobble_y)

        pygame.draw.rect(
            screen,
            self.color,
            draw_rect,
            border_radius=5
        )

        eye_offset = max(5, self.SIZE // 5)

        for ex in [
            draw_rect.x + eye_offset,
            draw_rect.x + self.SIZE - eye_offset - 4
        ]:
            pygame.draw.circle(
                screen,
                (200,40,40),
                (ex, draw_rect.y + self.SIZE // 3),
                4
            )


class FastZombie(Zombie):
    SPEED = 3.0
    SIZE = 20
    HP = 1
    COLOR = (220,180,40)


class TankZombie(Zombie):
    SPEED = 0.75
    SIZE = 42
    HP = 6
    COLOR = (120,70,160)

class Barrel:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 28, 32)

    def draw(self, screen):
        pygame.draw.rect(
            screen,
            (150, 80, 30),
            self.rect,
            border_radius=4
        )
        pygame.draw.rect(
            screen,
            (220, 180, 60),
            self.rect,
            3,
            border_radius=4
        )
        pygame.draw.line(
            screen,
            (220, 180, 60),
            (self.rect.x + 4, self.rect.centery),
            (self.rect.right - 4, self.rect.centery),
            3
        )

def spawn_zombie(width, height, player_rect, zombie_class=Zombie, margin=120):
    size = zombie_class.SIZE

    while True:
        x = random.randint(0, width-size)
        y = random.randint(0, height-size)

        rect = pygame.Rect(x, y, size, size)

        if not rect.colliderect(player_rect.inflate(margin, margin)):
            return zombie_class(x, y)

def spawn_barrel(width, height, player_rect, existing_barrels):
    while True:
        x = random.randint(0, width - 28)
        y = random.randint(50, height - 32)

        rect = pygame.Rect(x, y, 28, 32)

        if rect.colliderect(player_rect.inflate(100, 100)):
            continue

        if any(rect.colliderect(barrel.rect.inflate(20, 20))
               for barrel in existing_barrels):
            continue

        return Barrel(x, y)
    
SPEED = 4



class Player:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 32, 32)
        self.color = (60,160,220)
        self.bullets = []
        self.shoot_cooldown = 0
        self.ammo = 12
        self.reload_start = None

    def move(self, keys, width, height):
        dx = dy = 0
        if keys[pygame.K_w] or keys[pygame.K_UP]: dy = -SPEED
        if keys[pygame.K_s] or keys[pygame.K_DOWN]: dy = SPEED
        if keys[pygame.K_a] or keys[pygame.K_LEFT]: dx = -SPEED
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]: dx = SPEED
        self.rect.x = max(0, min(width-self.rect.width, self.rect.x+dx))
        self.rect.y = max(0, min(height-self.rect.height, self.rect.y+dy))
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1

    def shoot(self, target_pos):
        if self.shoot_cooldown > 0:
            return
        if self.reload_start is not None:
            return
        if self.ammo <= 0:
            return
        cx, cy = self.rect.center
        tx, ty = target_pos
        dx, dy = tx-cx, ty-cy
        dist = (dx**2+dy**2)**0.5
        if dist == 0: return
        vx, vy = dx/dist*10, dy/dist*10
        self.bullets.append(pygame.Rect(cx-4, cy-4, 8, 8))
        self.bullets.append([cx-4, cy-4, vx, vy])
        self.bullets.pop(-2)
        self.ammo -= 1
        if self.ammo == 0:
            self.reload_start = time.time()
        self.shoot_cooldown = 15
        
    def update_reload(self):
        if self.reload_start is not None:
            if time.time() - self.reload_start >= 2.0:
                self.ammo = 12
                self.reload_start = None

    def update_bullets(self, width, height):
        live = []
        for b in self.bullets:
            b[0] += b[2]; b[1] += b[3]
            if 0 <= b[0] <= width and 0 <= b[1] <= height:
                live.append(b)
        self.bullets = live

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect, border_radius=6)
        for b in self.bullets:
            pygame.draw.circle(screen, (255,220,60), (int(b[0]), int(b[1])), 5)


class GameEngine:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Zombie Escape")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("monospace", 24)
        self.big_font = pygame.font.SysFont("monospace", 44, bold=True)
        self.reset()

    def reset(self):
        self.player = Player(WIDTH//2, HEIGHT//2)
        self.zombies = [
            spawn_zombie(WIDTH, HEIGHT, self.player.rect, Zombie)
            for _ in range(6)
        ]

        self.zombies.append(
            spawn_zombie(WIDTH, HEIGHT, self.player.rect, FastZombie)
        )

        self.zombies.append(
            spawn_zombie(WIDTH, HEIGHT, self.player.rect, TankZombie)
        )

        self.barrels = []
        for _ in range(4):
            self.barrels.append(
                spawn_barrel(WIDTH, HEIGHT, self.player.rect, self.barrels)
            )

        self.hp = 3
        self.invincible_until = 0
        self.score = 0
        self.wave = 1
        self.kills = 0
        self.kills_to_next = 8
        self.game_over = False
        self.start_time = time.time()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT: return False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r: self.reset()
            if event.type == pygame.MOUSEBUTTONDOWN and not self.game_over:
                self.player.shoot(event.pos)
        return True

    def update(self):
        if self.game_over: return
        keys = pygame.key.get_pressed()
        self.player.move(keys, WIDTH, HEIGHT)
        self.player.update_reload()
        self.player.update_bullets(WIDTH, HEIGHT)
        self.score = int(time.time() - self.start_time)

        for z in self.zombies:
            z.update(self.player.rect.center)
            if z.rect.colliderect(self.player.rect):
                current_time = time.time()

                if current_time >= self.invincible_until:
                    self.hp -= 1
                    self.invincible_until = current_time + 1.0

                    if self.hp <= 0:
                        self.game_over = True
        # Check bullet-barrel collisions
        exploded_barrels = []
        explosion_radius = 90

        for barrel in self.barrels:
            for b in self.player.bullets[:]:
                bx, by = int(b[0]), int(b[1])

                if barrel.rect.collidepoint(bx, by):
                    exploded_barrels.append(barrel)

                    if b in self.player.bullets:
                        self.player.bullets.remove(b)

                    barrel_x, barrel_y = barrel.rect.center

                    for z in self.zombies[:]:
                        zombie_x, zombie_y = z.rect.center
                        distance = math.sqrt(
                            (zombie_x - barrel_x) ** 2 +
                            (zombie_y - barrel_y) ** 2
                        )

                        if distance <= explosion_radius:
                            self.zombies.remove(z)
                            self.kills += 1
                            self.score += 10

                    break

        for barrel in exploded_barrels:
            if barrel in self.barrels:
                self.barrels.remove(barrel)
        
        dead = []
        for z in self.zombies:
            for b in self.player.bullets[:]:
                bx, by = int(b[0]), int(b[1])
                if z.rect.collidepoint(bx, by):
                    if z.hit():
                        dead.append(z)
                    if b in self.player.bullets:
                        self.player.bullets.remove(b)
        for z in dead:
            if z in self.zombies:
                self.zombies.remove(z)
                self.kills += 1
                self.score += 10

        if self.kills >= self.kills_to_next:
            self.kills = 0
            self.wave += 1
            self.kills_to_next = 8 + self.wave * 2
            for _ in range(self.wave + 1):
                self.zombies.append(
                    spawn_zombie(WIDTH, HEIGHT, self.player.rect, Zombie)
                )

                self.zombies.append(
                    spawn_zombie(WIDTH, HEIGHT, self.player.rect, FastZombie)
                )

                self.zombies.append(
                    spawn_zombie(WIDTH, HEIGHT, self.player.rect, TankZombie)
                )
    
    def draw(self):
        self.screen.fill(BG)
        for x in range(0, WIDTH, 60):
            pygame.draw.line(self.screen, (40,45,35), (x,0), (x,HEIGHT), 1)
        for y in range(0, HEIGHT, 60):
            pygame.draw.line(self.screen, (40,45,35), (0,y), (WIDTH,y), 1)
        for barrel in self.barrels:
            barrel.draw(self.screen)

        for z in self.zombies:
            z.draw(self.screen)

        self.player.draw(self.screen)
        hud_bg = pygame.Rect(0, 0, WIDTH, 40)
        pygame.draw.rect(self.screen, (15,20,15), hud_bg)
        hud = self.font.render(
            f"HP: {self.hp}  Ammo: {self.player.ammo}/12  Wave: {self.wave}  Score: {self.score}  Kills: {self.kills}/{self.kills_to_next}  |  WASD Move, Click Shoot, R Restart",
            True, (160,220,120))
        self.screen.blit(hud, (8, 8))
        if self.game_over:
            ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            ov.fill((0,0,0,160))
            self.screen.blit(ov, (0,0))
            m = self.big_font.render("DEVOURED!", True, (180,40,40))
            s = self.font.render(f"Wave {self.wave} | Score {self.score} | Press R", True, (200,200,200))
            self.screen.blit(m, (WIDTH//2-m.get_width()//2, HEIGHT//2-40))
            self.screen.blit(s, (WIDTH//2-s.get_width()//2, HEIGHT//2+20))
        pygame.display.flip()

    def run(self):
        running = True
        while running:
            running = self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)
        pygame.quit()


if __name__ == "__main__":
    engine = GameEngine()
    engine.run()
