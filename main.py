import pygame
import sqlite3
import random

pygame.init()

# Настройка экрана
screen = pygame.display.set_mode((400, 400))
pygame.display.set_caption("Space War")
clock = pygame.time.Clock()
screen_rect = screen.get_rect()
GRAVITY = 0  # Set gravity to 0 for space environment

# Загрузка изображений
def load_image(filename):
    image = pygame.image.load(filename)
    return image.convert_alpha()

# Загрузка шрифтов
font = pygame.font.Font("data/PIXY.ttf", 16)  # Пиксельный шрифт
big_font = pygame.font.Font("data/PIXY.ttf", 32)  # Большой шрифт для "Новый рекорд"

# Загрузка изображений
sound_on_img = load_image("data/sound_on.png")
sound_off_img = load_image("data/sound_off.png")
space_ship_img1 = load_image("data/space_ship1.png")
space_ship_img2 = load_image("data/space_ship2.png")
asteroid1 = load_image("data/meteor11.png")  # Маленький астероид
shell = load_image("data/shell.png")  # Снаряд
good_game = load_image("data/gameover.png")
star_img = load_image("data/m4.jpg")  # Частица

# Группы спрайтов
all_sprites = pygame.sprite.Group()
meteors = pygame.sprite.Group()
bullets = pygame.sprite.Group()

# Класс частиц
class Particle(pygame.sprite.Sprite):
    def __init__(self, pos, dx, dy):
        super().__init__(all_sprites)
        size = random.randint(5, 15)
        self.image = pygame.transform.scale(star_img, (size, size))
        self.rect = self.image.get_rect()
        self.velocity = [dx, dy]
        self.rect.x, self.rect.y = pos
        self.birth_time = pygame.time.get_ticks()
        self.lifetime = random.randint(500, 1000)  # Время существования

    def update(self):
        self.velocity[1] += GRAVITY
        self.rect.x += self.velocity[0]
        self.rect.y += self.velocity[1]
        if not self.rect.colliderect(screen_rect) or pygame.time.get_ticks() - self.birth_time > self.lifetime:
            self.kill()

# Функция создания частиц
def create_particles(position):
    particle_count = 20
    numbers = range(-5, 6)
    for _ in range(particle_count):
        dx = random.choice(numbers)
        dy = random.choice(numbers)
        Particle(position, dx, dy)

# Класс корабля
class Ship(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__(all_sprites)
        self.image = space_ship_img1
        self.rect = self.image.get_rect()
        self.rect.center = (200, 350)
        self.speed = 1.5  # Скорость движения в пикселях за кадр
        self.health = 100  # Здоровье корабля
        self.is_shooting = False
        self.shoot_start_time = 0  # Время начала выстрела

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

        # Обработка анимации выстрела
        if self.is_shooting:
            current_time = pygame.time.get_ticks()
            if current_time - self.shoot_start_time >= 100:  # 500 мс = 0.5 секунды
                self.is_shooting = False
                self.image = space_ship_img1
            else:
                self.image = space_ship_img2

# Класс пуль
class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__(all_sprites, bullets)
        self.image = shell
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)

    def update(self):
        self.rect.y -= 5  # Движение вверх со скоростью 5 пикселей за кадр
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
        self.speed = random.uniform(1, 3)  # Случайная скорость от 1 до 3

    def update(self):
        self.rect.y += self.speed  # Движение вниз с постоянной скоростью
        if self.rect.top > 400:
            self.kill()

# Игровые переменные
score = 0
last_score = 0  # Переменная для хранения последнего результата
game_over = False
paused = False
sound_on = True
ship = Ship()
current_combo = 0  # Текущее комбо
max_game_kombo = 0  # Максимальное комбо за игру

# Настройка базы данных
con = sqlite3.connect("pygame.sqlite")  # Подключаемся к базе данных pygame0
cur = con.cursor()

con.commit()

# Получение лучшего и последнего результата из базы данных
score_list = cur.execute("SELECT num FROM score").fetchall()
if score_list:
    best_score = max(score_list)[0]
    last_score = score_list[-1][0]  # Последний результат
else:
    best_score = 0
    last_score = 0

# Получение максимального комбо из таблицы kombo
combo_list = cur.execute("SELECT num FROM kombo").fetchall()
if combo_list:
    max_combo = max(combo_list)[0]  # Максимальное комбо
else:
    max_combo = 0  # Если таблица пуста, устанавливаем комбо в 0

# Игровой цикл
def game_loop(target_score):
    global score, game_over, paused, best_score, ship, last_score, max_game_kombo, current_combo
    initialize_game(target_score)

    while not game_over:
        handle_events()

        if not paused:
            update_game_objects(target_score)

        render_screen()
        clock.tick(60)

    # Запись текущего счета в таблицу score
    cur.execute("INSERT INTO score(num) VALUES (?)", (score,))
    con.commit()

    # Запись максимального комбо в таблицу kombo
    if max_game_kombo > 0:
        cur.execute("INSERT INTO kombo(num) VALUES (?)", (max_game_kombo,))
        con.commit()

    handle_game_over()
    reset_game_state()  # Сброс состояния игры после завершения

def initialize_game(target_score):
    global score, paused, all_sprites, meteors, bullets, ship, last_meteor_time, current_combo, max_game_kombo
    score = 0
    paused = False
    game_over = False
    all_sprites = pygame.sprite.Group()
    meteors = pygame.sprite.Group()
    bullets = pygame.sprite.Group()
    ship = Ship()
    all_sprites.add(ship)
    last_meteor_time = pygame.time.get_ticks()
    current_combo = 0  # Сбрасываем текущее комбо
    max_game_kombo = 0  # Сбрасываем максимальное комбо за игру

def handle_events():
    global game_over, paused
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            quit()
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                game_over = True
            elif event.key == pygame.K_p:
                paused = not paused
            elif event.key == pygame.K_SPACE:
                Bullet(ship.rect.left + 2, ship.rect.top)
                Bullet(ship.rect.right - 2, ship.rect.top)
                ship.is_shooting = True
                ship.shoot_start_time = pygame.time.get_ticks()  # Запуск таймера выстрела

def update_game_objects(target_score):
    global score, best_score, last_meteor_time, game_over, ship, current_combo, max_game_kombo
    current_time = pygame.time.get_ticks()
    all_sprites.update()

    # Проверка столкновений пуль и метеоров
    for bullet in bullets:
        meteor_hit = pygame.sprite.spritecollideany(bullet, meteors)
        if meteor_hit:
            create_particles(meteor_hit.rect.center)  # Создаем частицы при уничтожении метеора
            bullet.kill()
            meteor_hit.kill()
            score += 1
            current_combo += 1  # Увеличиваем текущее комбо
            if current_combo > max_game_kombo:
                max_game_kombo = current_combo  # Обновляем максимальное комбо за игру

    # Проверка, улетел ли метеорит за пределы экрана
    for meteor in meteors:
        if meteor.rect.top > 400:
            if current_combo > max_game_kombo:
                max_game_kombo = current_combo  # Обновляем максимальное комбо за игру
            current_combo = 0  # Сбрасываем текущее комбо

    # Создание метеоров в зависимости от целевого счета
    if current_time - last_meteor_time >= meteor_spawn_interval(target_score):
        Meteor(target_score)
        last_meteor_time = current_time

    # Проверка столкновений корабля с метеорами
    if pygame.sprite.spritecollide(ship, meteors, True):
        ship.health -= health_damage(target_score)
        if ship.health <= 0:
            game_over = True

    # Обновление лучшего счета в базе данных
    if score > best_score:
        update_best_score(score)
        best_score = score

    # Проверка достижения целевого счета
    if score >= target_score:
        game_over = True
        update_best_score(score)

def render_screen():
    screen.fill((0, 0, 0))
    all_sprites.draw(screen)
    draw_score()
    draw_health()

    # Отображение "Новый рекорд" и текущего комбо, если текущее комбо больше max_game_kombo
    if current_combo > max_game_kombo:
        # Надпись "Новый рекорд" большими буквами
        record_text = big_font.render("Новый рекорд!", True, (255, 215, 0))  # Золотой цвет
        record_rect = record_text.get_rect(center=(200, 150))  # Центр экрана по вертикали
        screen.blit(record_text, record_rect)

        # Надпись "Комбо: [текущее комбо]" меньшими буквами
        combo_text = font.render(f"Комбо: {current_combo}", True, (255, 255, 255))  # Белый цвет
        combo_rect = combo_text.get_rect(center=(200, 200))  # Чуть ниже "Новый рекорд"
        screen.blit(combo_text, combo_rect)

    pygame.display.flip()

def handle_game_over():
    # Анимация завершения игры
    end_game = pygame.sprite.Sprite()
    end_game.image = good_game
    end_game.rect = end_game.image.get_rect()
    end_game.rect.left = -end_game.rect.width

    while end_game.rect.left < 0:
        dt = clock.tick(60) / 1000
        movement = 100 * dt
        end_game.rect.left += movement
        screen.blit(end_game.image, end_game.rect)
        pygame.display.flip()

    # Ожидание клика мыши для продолжения
    press_space = pygame.font.Font("data/PIXY.ttf", 20)
    press_text = press_space.render("Кликните мышкой, чтобы продолжить", True, (255, 255, 255))
    press_rect = press_text.get_rect(center=(200, 350))

    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                waiting = False
        screen.blit(end_game.image, end_game.rect)
        screen.blit(press_text, press_rect)
        pygame.display.flip()
        clock.tick(60)

def reset_game_state():
    global game_over, all_sprites, meteors, bullets
    game_over = False
    all_sprites.empty()
    meteors.empty()
    bullets.empty()

def meteor_spawn_interval(target_score):
    if target_score == 100:
        return 250
    elif target_score == 50:
        return 500
    else:
        return 1000

def health_damage(target_score):
    if target_score <= 20 or target_score == 100000:
        return 25
    elif target_score == 50:
        return 35
    elif target_score == 100:
        return 50

def update_best_score(new_score):
    cur.execute("INSERT INTO score(num) VALUES (?)", (new_score,))
    con.commit()

def update_last_score(new_score):
    cur.execute("INSERT INTO score(num) VALUES (?)", (new_score,))
    con.commit()

def draw_score():
    score_text = font.render(f"Счёт: {score}", True, (255, 255, 255))
    screen.blit(score_text, (10, 10))

def draw_health():
    health_text = font.render(f"Здоровье: {ship.health}%", True, (255, 255, 255))
    screen.blit(health_text, (10, 30))

# Цикл меню
def draw_menu(best_score, sound_on, last_score, max_combo):
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

    last_score_text = font.render(f"Последний результат: {last_score}", True, (255, 255, 255))
    screen.blit(last_score_text, (95, 40))  # Отображение последнего результата

    # Добавляем отображение максимального комбо
    combo_text = font.render(f"Максимальное комбо: {max_combo}", True, (255, 255, 255))
    screen.blit(combo_text, (95, 60))  # Позиция под последним результатом

    sound_img = sound_on_img if sound_on else sound_off_img
    screen.blit(sound_img, (330, 10))

    # Добавляем подсказки по управлению
    controls_text = font.render("Пауза: P, Стрельба: Пробел, Выход: ESC", True, (255, 255, 255))
    controls_rect = controls_text.get_rect(center=(200, 380))  # Позиция внизу экрана
    screen.blit(controls_text, controls_rect)

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

    draw_menu(best_score, sound_on, last_score, max_combo)  # Передаем last_score в draw_menu
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
