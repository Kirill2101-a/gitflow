import pygame
import sqlite3
import random

pygame.init()

# Настройка экрана
screen = pygame.display.set_mode((400, 400))
pygame.display.set_caption("Space War")
clock = pygame.time.Clock()

# Загрузка изображений
def load_image(filename):
    image = pygame.image.load(filename)
    return image.convert_alpha()

# Загрузка шрифтов
font = pygame.font.Font("data/PIXY.ttf", 16)  # Пиксельный шрифт

# Загрузка изображений
sound_on_img = load_image("data/sound_on.png")
sound_off_img = load_image("data/sound_off.png")
space_ship_img1 = load_image("data/space_ship1.png")
space_ship_img2 = load_image("data/space_ship2.png")
asteroid1 = load_image("data/meteor11.png")  # Маленький
asteroid2 = load_image("data/meteor2.png")  # Средний
asteroid3 = load_image("data/meteor31.png")  # Большой астероид
shell = load_image("data/shell.png")  # Снаряд картинка
good_game = load_image("data/gameover.png")

# Группы спрайтов
all_sprites = pygame.sprite.Group()
meteors = pygame.sprite.Group()
bullets = pygame.sprite.Group()

# Класс корабля
class Ship(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__(all_sprites)
        self.image = space_ship_img1
        self.rect = self.image.get_rect()
        self.rect.center = (200, 350)
        self.speed = 1.5  # Пиксели в кадре
        self.health = 100  # Новое свойство для здоровья

    def update(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] and self.rect.left > 0:
            self.rect.x -= self.speed
        if keys[pygame.K_RIGHT] and self.rect.right < 400:
            self.rect.x += self.speed
        if keys[pygame.K_UP] and self.rect.top > 0:
            self.rect.y -= self.speed
        if keys[pygame.K_DOWN] and self.rect.bottom < 400:
            self.rect.y += self.speed

# Класс пуль
class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__(all_sprites, bullets)
        self.image = shell
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)

    def update(self):
        self.rect.y -= 5  # Двигаться вверх со скоростью 100 пикселей в секунду
        if self.rect.bottom < 0:
            self.kill()

# Класс метеоров
class Meteor(pygame.sprite.Sprite):
    def __init__(self, target_score):
        super().__init__(all_sprites, meteors)
        self.image = asteroid1
        self.rect = self.image.get_rect()
        self.rect.x = random.randint(0, 400)
        self.rect.y = 0
        self.target = target_score

    def update(self):
        if self.target == 100:
            self.rect.y += 2  # Двигаться вниз со скоростью 150 пикселей в секунду
        elif self.target == 50:
            self.rect.y += 1.5  # Двигаться вниз со скоростью 125 пикселей в секунду
        else:
            self.rect.y += 1  # Двигаться вниз со скоростью 100 пикселей в секунду
        if self.rect.top > 400:
            self.kill()

# Игровые переменные
score = 0
game_over = False
paused = False
sound_on = True
ship = Ship()

# Настройка базы данных
con = sqlite3.connect("pygame.sqlite")
cur = con.cursor()
score_list = cur.execute("SELECT num FROM score").fetchall()
best_score = max(score_list)[0]

# Игровой цикл
def game_loop(target_score):
    global score, game_over, paused, all_sprites, bullets, meteors, best_score
    score = 0
    game_over = False
    paused = False
    last_meteor_time = pygame.time.get_ticks()  # Инициализировать время последнего появления метеора

    # Пересоздать группы спрайтов
    all_sprites = pygame.sprite.Group()
    meteors = pygame.sprite.Group()
    bullets = pygame.sprite.Group()
    ship = Ship()
    all_sprites.add(ship)

    while not game_over:
        current_time = pygame.time.get_ticks()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:  # Exit level and return to menu
                    game_over = True
                elif event.key == pygame.K_p:  # Пауза
                    paused = not paused
                elif event.key == pygame.K_SPACE:  # Стрельба
                    Bullet(ship.rect.left + 2, ship.rect.top)
                    Bullet(ship.rect.right - 2, ship.rect.top)

        if ship.health <= 0:
            game_over = True

        if not paused:
            all_sprites.update()
            # Проверка на столкновения
            for bullet in bullets:
                meteor_hit = pygame.sprite.spritecollideany(bullet, meteors)
                if meteor_hit:
                    bullet.kill()
                    meteor_hit.kill()
                    score += 1

            if target_score == 100:
                # Появление 4 метеоров каждую секунду
                if current_time - last_meteor_time >= 250:
                    Meteor(target_score)
                    last_meteor_time = current_time  # Обновить время последнего появления
            if target_score == 50:
                # Появление 2 метеоров каждую секунду
                if current_time - last_meteor_time >= 500:
                    Meteor(target_score)
                    last_meteor_time = current_time  # Обновить время последнего появления
            else:
                # Появление метеоров каждую секунду
                if current_time - last_meteor_time >= 1000:
                    Meteor(target_score)
                    last_meteor_time = current_time  # Обновить время последнего появления


            # Отрисовка всего
            screen.fill((0, 0, 0))
            all_sprites.draw(screen)
            score_text = font.render(f"Счёт: {score}", True, (255, 255, 255))
            screen.blit(score_text, (10, 10))
            health_text = font.render(f"Здоровье: {ship.health}%", True, (255, 255, 255))
            screen.blit(score_text, (10, 10))
            screen.blit(health_text, (10, 30))
            pygame.display.flip()

            if pygame.sprite.spritecollide(ship, meteors, True):
                if target_score <= 20 or target_score == 100000:
                    ship.health -= 25
                elif target_score == 50:
                    ship.health -= 35
                elif target_score == 100:
                    ship.health -= 50
                if ship.health <= 0:
                    game_over = True

            if score > best_score:
                cur.execute(f"INSERT INTO score(num) VALUES ({score})")
                con.commit()
                best_score = score

            if score >= target_score:
                game_over = True
                cur.execute(f"INSERT INTO score(num) VALUES ({score})")
                con.commit()
                meteors = pygame.sprite.Group()
                bullets = pygame.sprite.Group()

        clock.tick(60)  # Поддерживать 60 FPS
    # Анимация Game Over
    end_game = pygame.sprite.Sprite()
    end_game.image = good_game
    end_game.rect = end_game.image.get_rect()
    end_game.rect.left = -end_game.rect.width  # Начать за экраном слева

    # Цикл анимации Game Over
    while end_game.rect.left < 0:
        dt = clock.tick(60) / 1000  # Временной интервал в секундах
        movement = 100 * dt  # 100 пикселей в секунду
        end_game.rect.left += movement

        # Отобразить изображение Game Over
        screen.blit(end_game.image, end_game.rect)
        pygame.display.flip()

    # Отобразить сообщение 'Нажмите пробел, чтобы продолжить'
    press_space = pygame.font.Font("data/PIXY.ttf", 20)
    press_text = press_space.render("Кликните мышкой, чтобы продолжить", True, (255, 255, 255))
    press_rect = press_text.get_rect(center=(200, 350))

    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
            elif event.type == pygame.MOUSEBUTTONDOWN:
                waiting = False

        screen.blit(end_game.image, end_game.rect)
        screen.blit(press_text, press_rect)
        pygame.display.flip()
        clock.tick(60)

# Цикл меню
def draw_menu(best_score, sound_on):
    screen.fill((0, 0, 0))
    level1 = font.render("1 уровень", True, (255, 255, 255))
    level2 = font.render("2 уровень", True, (255, 255, 255))
    level3 = font.render("3 уровень", True, (255, 255, 255))
    screen.blit(level1, (140, 80))
    screen.blit(level2, (140, 180))
    screen.blit(level3, (140, 280))

    arcade = font.render("Аркадный режим", True, (255, 255, 255))
    screen.blit(arcade, (115, 350))

    score_text = font.render(f"Лучший счет: {best_score}", True, (255, 255, 255))
    screen.blit(score_text, (120, 20))

    sound_img = sound_on_img if sound_on else sound_off_img
    screen.blit(sound_img, (330, 10))
    pygame.display.flip()

# Основной цикл
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            x, y = event.pos
            if 140 <= x <= 260 and 80 <= y <= 120:
                game_loop(20)  # Уровень 1
            elif 140 <= x <= 260 and 180 <= y <= 220:
                game_loop(50)  # Уровень 2
            elif 140 <= x <= 260 and 280 <= y <= 320:
                game_loop(100)  # Уровень 3
            elif 115 <= x <= 300 and 350 <= y <= 390:
                game_loop(100000)  # Аркадный режим
            elif 330 <= x <= 400 and 10 <= y <= 50:
                sound_on = not sound_on
                print("Звук включен" if sound_on else "Звук выключен")

    draw_menu(best_score, sound_on)
    pygame.display.flip()
    clock.tick(60)

pygame.quit()