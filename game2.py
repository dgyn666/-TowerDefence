import random
import pygame
import time
import math 

# --- Конфигурация игры ---
WIDTH, HEIGHT = 1280, 720  # Размеры экрана
FPS = 60  # Частота кадров
CASTLE_SIZE = 50  # Размер замка
HERO_SIZE = 8  # Размер героя
HERO_SPEED = 5  # Скорость героя
BULLET_SPEED = 10  # Скорость пуль
SHOOT_DELAY = 200  # Задержка между выстрелами (в миллисекундах)

# --- Инициализация Pygame ---
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))  # Создание окна
pygame.display.set_caption("Tower Defense Game")  # Название игры
clock = pygame.time.Clock()
font = pygame.font.Font(None, 36)  # Шрифт для текста

# --- Классы ---
class Castle:
    def __init__(self, x, y, health):
        self.x = x  # Позиция X
        self.y = y  # Позиция Y
        self.health = health  # Здоровье замка

    def draw(self):
        # Замок становится красным, если здоровье <= 5
        color = (255, 0, 0) if self.health <= 5 else (100, 100, 255)
        pygame.draw.rect(screen, color, (self.x, self.y, CASTLE_SIZE, CASTLE_SIZE))

class Hero:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.color = (0, 255, 0)  # Зеленый цвет героя
        self.last_shot_time = 0  # Время последнего выстрела
        self.shoot_speed = 1500  # Скорость стрельбы
        self.bullet_damage = 1  # Урон от пуль
        self.multi_shot = 1  # Количество пуль за выстрел
        self.move_speed = 5  # Скорость передвижения

    def move(self, keys):
        # Движение героя по клавишам W, A, S, D
        if keys[pygame.K_w] and self.y - self.move_speed > 0:
            self.y -= self.move_speed
        if keys[pygame.K_s] and self.y + self.move_speed + HERO_SIZE < HEIGHT:
            self.y += self.move_speed
        if keys[pygame.K_a] and self.x - self.move_speed > 0:
            self.x -= self.move_speed
        if keys[pygame.K_d] and self.x + self.move_speed + HERO_SIZE < WIDTH:
            self.x += self.move_speed

    def draw(self):
        # Рисуем героя в виде зеленого круга
        pygame.draw.circle(screen, self.color, (self.x, self.y), HERO_SIZE)

    def shoot(self):
        current_time = pygame.time.get_ticks()
        if current_time - self.last_shot_time >= self.shoot_speed:
            self.last_shot_time = current_time
            bullets = []
            
            # Основное направление выстрела (на мышку)
            mouse_x, mouse_y = pygame.mouse.get_pos()
            dx, dy = mouse_x - self.x, mouse_y - self.y
            magnitude = (dx ** 2 + dy ** 2) ** 0.5
            if magnitude != 0:
                dx /= magnitude
                dy /= magnitude

            # Угловое распределение для мультишота
            angle_step = 15  # Шаг между пулями в градусах
            start_angle = -((self.multi_shot - 1) * angle_step / 2)  # Центральная ось выстрела
            for i in range(self.multi_shot):
                angle = start_angle + i * angle_step
                rad_angle = math.radians(angle)

                # Поворот вектора на заданный угол
                bullet_dx = dx * math.cos(rad_angle) - dy * math.sin(rad_angle)
                bullet_dy = dx * math.sin(rad_angle) + dy * math.cos(rad_angle)

                bullets.append(Bullet(self.x, self.y, bullet_dx, bullet_dy, self.bullet_damage))

            return bullets
        return []

class Bullet:
    def __init__(self, x, y, dx, dy, damage=1):
        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy
        self.damage = damage  # Урон пули

    def update(self):
        # Обновление положения пули
        self.x += self.dx * BULLET_SPEED
        self.y += self.dy * BULLET_SPEED

    def draw(self):
        # Рисуем пулю в виде желтого круга
        pygame.draw.circle(screen, (255, 255, 0), (int(self.x), int(self.y)), 5)

    def is_off_screen(self):
        # Проверяем, не вышла ли пуля за экран
        return self.x < 0 or self.x > WIDTH or self.y < 0 or self.y > HEIGHT

    def is_colliding_with_castle(self, castle):
        # Проверяем столкновение с замком
        return (
            castle.x <= self.x <= castle.x + CASTLE_SIZE and
            castle.y <= self.y <= castle.y + CASTLE_SIZE
        )

class Enemy:
    def __init__(self, x, y, health):
        self.x = x
        self.y = y
        self.health = health  # Здоровье врага

    def move_towards(self, target_x, target_y):
        # Движение врага к цели (замку)
        dx, dy = target_x - self.x, target_y - self.y
        magnitude = (dx ** 2 + dy ** 2) ** 0.5
        if magnitude != 0:
            dx /= magnitude
            dy /= magnitude
        self.x += dx * 0.2
        self.y += dy * 0.2

    def draw(self):
        # Рисуем врага в виде красного круга
        pygame.draw.circle(screen, (255, 0, 0), (int(self.x), int(self.y)), 10)

    def is_colliding_with_castle(self, castle):
        # Проверяем столкновение врага с замком
        return (
            castle.x < self.x < castle.x + CASTLE_SIZE and
            castle.y < self.y < castle.y + CASTLE_SIZE
        )

# --- Инициализация объектов ---
castle = Castle(WIDTH // 2 - CASTLE_SIZE // 2, HEIGHT // 2 - CASTLE_SIZE // 2, 10)
hero = Hero(WIDTH // 3, HEIGHT // 3)
bullets = []
enemies = []
waves = 1
wave_ready = True
score = 0
gold = 1000
shop_open = False
is_shooting = False

# --- Функции ---
def spawn_enemies(wave):
    # Создание врагов для новой волны
    enemy_health = 2 + (wave // 5)  # Усиление врагов: +1 к здоровью каждые 5 волн
    for _ in range(5 + (wave - 1) * 2):
        side = random.choice(['top', 'bottom', 'left', 'right'])
        if side == 'top':
            x, y = random.randint(0, WIDTH), 0
        elif side == 'bottom':
            x, y = random.randint(0, WIDTH), HEIGHT
        elif side == 'left':
            x, y = 0, random.randint(0, HEIGHT)
        else:
            x, y = WIDTH, random.randint(0, HEIGHT)
        enemies.append(Enemy(x, y, enemy_health))

def draw_shop():
    global gold, last_purchase_time
    if 'last_purchase_time' not in globals():
        last_purchase_time = 0  # Инициализация времени последней покупки
    
    # Отображение интерфейса магазина
    pygame.draw.rect(screen, (50, 50, 50), (0, 0, WIDTH, HEIGHT))
    pygame.draw.rect(screen, (200, 200, 200), (WIDTH // 4, HEIGHT // 4, WIDTH // 2, HEIGHT // 2))
    shop_text = font.render("Shop: Upgrade your Hero", True, (0, 0, 0))
    screen.blit(shop_text, (WIDTH // 2 - shop_text.get_width() // 2, HEIGHT // 4 + 20))

    upgrades = [
        ("Increase Fire Rate", 10, hero.shoot_speed, lambda: setattr(hero, 'shoot_speed', max(50, hero.shoot_speed - 20))),
        ("Increase Bullet Damage", 20, hero.bullet_damage, lambda: setattr(hero, 'bullet_damage', hero.bullet_damage + 1)),
        ("Increase Multi-shot", 30, hero.multi_shot, lambda: setattr(hero, 'multi_shot', hero.multi_shot + 1)),
        ("Increase Move Speed", 15, hero.move_speed, lambda: setattr(hero, 'move_speed', hero.move_speed + 1)),
    ]

    for i, (text, cost, current, action) in enumerate(upgrades):
        upgrade_text = font.render(f"{text} (Cost: {cost}, Current: {current})", True, (0, 0, 0))
        text_x = WIDTH // 2 - upgrade_text.get_width() // 2
        text_y = HEIGHT // 4 + 60 + i * 40
        screen.blit(upgrade_text, (text_x, text_y))

        if pygame.mouse.get_pressed()[0]:  # ЛКМ нажата
            current_time = pygame.time.get_ticks()
            mouse_x, mouse_y = pygame.mouse.get_pos()
            if current_time - last_purchase_time >= 500:  # Задержка 500 мс между покупками
                if WIDTH // 4 < mouse_x < 3 * WIDTH // 4 and text_y <= mouse_y < text_y + 40:
                    if gold >= cost:
                        gold -= cost
                        action()
                        last_purchase_time = current_time
                    else:
                        print("Not enough gold!")
# --- Игровой цикл ---
running = True
while running:
    screen.fill((0, 0, 0))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            is_shooting = True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            is_shooting = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_TAB:
                shop_open = not shop_open

    keys = pygame.key.get_pressed()
    hero.move(keys)

    if shop_open:
        draw_shop()

    # Отображение информации
    info_text = font.render(f"Score: {score}  Health: {castle.health}  Wave: {waves}", True, (255, 255, 255))
    gold_text = font.render(f"Gold: {gold}", True, (255, 255, 0))
    damage_text = font.render(f"Bullet Damage: {hero.bullet_damage}", True, (255, 255, 255))
    
    screen.blit(damage_text, (10, 90))
    screen.blit(info_text, (10, 10))
    screen.blit(gold_text, (10, 50))

    if not shop_open:
        # Обновление и отрисовка объектов
        castle.draw()
        hero.draw()

        if is_shooting:
            new_bullets = hero.shoot()
            if new_bullets:  # Проверяем, если `new_bullets` не пустой
                bullets.extend(new_bullets)

        bullets_to_remove = []
        for bullet in bullets:
            bullet.update()
            bullet.draw()
            if bullet.is_off_screen() or bullet.is_colliding_with_castle(castle):
                bullets_to_remove.append(bullet)
                
        for bullet in bullets_to_remove:
            bullets.remove(bullet)

        for enemy in enemies[:]:  # Обрабатываем здоровье врага при попаданиях пуль
            enemy.move_towards(castle.x + CASTLE_SIZE // 2, castle.y + CASTLE_SIZE // 2)
            enemy.draw()
            if enemy.is_colliding_with_castle(castle):
                enemy.health -= 1  # Уменьшаем здоровье врага при попадании
                if enemy.health <= 0:  # Удаляем врага, если здоровье достигло 0
                    enemies.remove(enemy)
                castle.health -= 1
            for bullet in bullets[:]:
                for enemy in enemies[:]:
                    if ((enemy.x - bullet.x) ** 2 + (enemy.y - bullet.y) ** 2) ** 0.5 < 15:  # Проверка попадания
                        enemy.health -= bullet.damage  # Уменьшаем здоровье врага на урон пули
                        bullets.remove(bullet)  # Убираем пулю после попадания
                        if enemy.health <= 0:  # Если здоровье врага <= 0, удаляем врага
                            enemies.remove(enemy)
                            score += 1
                            gold += 1
                        break

        if not enemies and wave_ready:
            wave_ready = False
            waves += 1
            time.sleep(0.0)  # Пауза перед началом новой волны
            spawn_enemies(waves)


        if not enemies:
            next_wave_text = font.render("Press 'N' to start next wave", True, (255, 255, 255))
            screen.blit(next_wave_text, (WIDTH // 2 - 200, HEIGHT // 2))
            if keys[pygame.K_n]:
                wave_ready = True

        if castle.health <= 0:
            game_over_text = font.render("Game Over", True, (255, 0, 0))
            screen.blit(game_over_text, (WIDTH // 2 - 100, HEIGHT // 2))
            pygame.display.update()
            pygame.time.wait(3000)
            running = False

    pygame.display.update()
    clock.tick(FPS)

pygame.quit()