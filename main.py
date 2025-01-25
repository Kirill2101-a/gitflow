import pygame
import sqlite3
import random

pygame.init()
pygame.mixer.init()

# Настройка экрана
screen = pygame.display.set_mode((400, 400))
pygame.display.set_caption("Space War")
clock = pygame.time.Clock()
screen_rect = screen.get_rect()
GRAVITY = 0
stop_time = 0


# Загрузка изображений
def load_image(filename):
    image = pygame.image.load(filename)
    return image.convert_alpha()


# Загрузка фоновой музыки
pygame.mixer.music.load("data/music.mp3")
pygame.mixer.music.set_volume(0.2)
pygame.mixer.music.play(-1)

# Загрузка шрифтов
font = pygame.font.Font("data/PIXY.ttf", 16)  # Пиксельный шрифт
big_font = pygame.font.Font("data/PIXY.ttf", 32)  # Большой шрифт для "Новый рекорд"

# Загрузка изображений
space_ship_img1 = load_image("data/space_ship1.png")
space_ship_img2 = load_image("data/space_ship2.png")
asteroid1 = load_image("data/meteor11.png")  # Маленький астероид
shell = load_image("data/shell.png")  # Снаряд
good_game = load_image("data/gameover.png")
star_img = load_image("data/m4.jpg")  # Частица
power_up_img = load_image("data/power_up.png")  # Изображение для power-up
power_up_img_1 = load_image("data/power_up_health.png")  # Изображение для power-up

# Группы спрайтов
all_sprites = pygame.sprite.Group()
meteors = pygame.sprite.Group()
bullets = pygame.sprite.Group()
power_ups = pygame.sprite.Group()


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
        self.speed = 2.25  # Скорость движения в пикселях за кадр
        self.health = 100  # Здоровье корабля
        self.is_shooting = False
        self.shoot_start_time = 0  # Время начала выстрела
        self.invincible = False  # Флаг для неуязвимости
        self.invincible_start_time = 0  # Время начала неуязвимости
        self.invincible_duration = 5000  # Длительность неуязвимости в миллисекундах
        self.paused_duration = 0  # Время, проведенное в паузе

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
            if current_time - self.shoot_start_time >= 100:  # 100 мс = 0.1 секунды
                self.is_shooting = False
                self.image = space_ship_img1
            else:
                self.image = space_ship_img2

        # Обработка неуязвимости
        if self.invincible:
            current_time = pygame.time.get_ticks()
            if current_time - self.invincible_start_time - self.paused_duration >= self.invincible_duration:
                self.invincible = False


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
        self.rect.x = random.randint(0, 380)
        self.rect.y = 0
        self.target = target_score
        self.speed = random.uniform(1, 3)  # Случайная скорость от 1 до 3

    def update(self):
        global combo, new_record_shown
        self.rect.y += self.speed  # Движение вниз с постоянной скоростью
        if self.rect.top > 400:
            if combo > 0:  # Если комбо больше 0, записываем его в таблицу combo
                cur.execute("INSERT INTO combo(num) VALUES (?)", (combo,))
                con.commit()
            combo = 0  # Обнуляем комбо
            new_record_shown = False
            self.kill()


# Класс power-up для неуязвимости
class PowerUp(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__(all_sprites, power_ups)
        self.image = power_up_img
        self.rect = self.image.get_rect()
        self.rect.x = random.randint(0, 400 - self.rect.width)
        self.rect.y = 0

    def update(self):
        self.rect.y += 2  # Движение вниз с постоянной скоростью
        if self.rect.top > 400:
            self.kill()


# Класс power-up для регенерации
class HealthPowerUp(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__(all_sprites, power_ups)
        self.image = power_up_img_1
        self.rect = self.image.get_rect()
        self.rect.x = random.randint(0, 400 - self.rect.width)
        self.rect.y = 0

    def update(self):
        self.rect.y += 2  # Движение вниз с постоянной скоростью
        if self.rect.top > 400:
            self.kill()


# Игровые переменные
score = 0
last_score = 0  # Переменная для хранения последнего результата
game_over = False
paused = False
sound_enabled = True
ship = Ship()
combo = 0
max_combo = 0
show_new_record = False  # Флаг для отображения сообщения о новом рекорде комбо
new_record_shown = False
level_passed = False  # Флаг для отслеживания прохождения уровня
level_passed_start_time = 0  # Время начала отображения сообщения о прохождении уровня
level_passed_message_shown = False  # Флаг для отслеживания, было ли сообщение показано

# Настройка базы данных
con = sqlite3.connect("pygame.sqlite")  # Подключаемся к базе данных pygame0
cur = con.cursor()

# Получение лучшего и последнего результата из базы данных
score_list = cur.execute("SELECT num FROM score").fetchall()
combo_list = cur.execute("SELECT num FROM combo").fetchall()
if score_list:
    best_score = max(score_list)[0]
    last_score = score_list[-1][0]  # Последний результат
else:
    best_score = 0
    last_score = 0

if combo_list:
    max_combo = max(combo_list)[0]
else:
    max_combo = 0


# Игровой цикл
def game_loop(target_score):
    global score, game_over, paused, last_score, combo
    initialize_game()

    while not game_over:
        handle_events()
        if target_score != 100:
            if score >= target_score:
                game_over = True

        if not paused:
            update_game_objects(target_score)

        render_screen()
        clock.tick(60)

    # Запись текущего счета в таблицу score
    cur.execute("INSERT INTO score(num) VALUES (?)", (score,))
    con.commit()

    # Запись текущего комбо в таблицу combo, если комбо больше 0
    if combo > 0:
        cur.execute("INSERT INTO combo(num) VALUES (?)", (combo,))
        con.commit()

    last_score = score # Обновление последнего результата

    reset_game_state()  # Сброс состояния игры после завершения


def initialize_game():
    global score, paused, all_sprites, meteors, bullets, ship, last_meteor_time, combo, show_new_record
    global new_record_shown, power_ups, level_passed, level_passed_start_time, level_passed_message_shown
    score = 0
    combo = 0
    paused = False
    show_new_record = False  # Сброс флага при инициализации игры
    new_record_shown = False  # Сброс флага, чтобы сообщение могло появиться в новой игре
    level_passed = False  # Сброс флага прохождения уровня
    level_passed_start_time = 0  # Сброс времени отображения сообщения
    level_passed_message_shown = False  # Сброс флага показа сообщения
    all_sprites = pygame.sprite.Group()
    meteors = pygame.sprite.Group()
    bullets = pygame.sprite.Group()
    power_ups = pygame.sprite.Group()
    ship = Ship()
    all_sprites.add(ship)
    last_meteor_time = pygame.time.get_ticks()


def handle_events():
    global game_over, paused, ship, sound_enabled
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            quit()
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_s:
                sound_enabled = not sound_enabled
                if sound_enabled:
                    pygame.mixer.music.set_volume(0.5)
                    pygame.mixer.music.unpause()
                else:
                    pygame.mixer.music.set_volume(0)
                    pygame.mixer.music.pause()
            elif event.key == pygame.K_ESCAPE:
                game_over = True
            elif event.key == pygame.K_p:
                paused = not paused
                if paused:
                    ship.paused_duration += pygame.time.get_ticks() - ship.invincible_start_time
                else:
                    ship.invincible_start_time = pygame.time.get_ticks() - ship.paused_duration
            elif event.key == pygame.K_SPACE and not paused:
                if sound_enabled:
                    sound1 = pygame.mixer.Sound('data/music2.mp3')
                    sound1.set_volume(0.2)
                    sound1.play()
                Bullet(ship.rect.left + 2, ship.rect.top)
                Bullet(ship.rect.right - 2, ship.rect.top)
                ship.is_shooting = True
                ship.shoot_start_time = pygame.time.get_ticks()  # Запуск таймера выстрела


def update_game_objects(target_score):
    global score, best_score, last_meteor_time, game_over, ship, combo, max_combo, show_new_record
    global new_record_shown, level_passed, level_passed_start_time, level_passed_message_shown
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
            combo += 1

    # Проверка, вылетел ли метеорит за пределы экрана
    for meteor in meteors:
        if meteor.rect.top > 400:
            if combo > 0:  # Если комбо больше 0, записываем его в таблицу combo
                cur.execute("INSERT INTO combo(num) VALUES (?)", (combo,))
                con.commit()
            combo = 0  # Обнуляем комбо
            show_new_record = False  # Сброс флага при обнулении комбо

    # Проверка столкновений корабля с метеорами
    meteor_collisions = pygame.sprite.spritecollide(ship, meteors, True)
    for meteor in meteor_collisions:
        if not ship.invincible:
            ship.health -= health_damage(target_score)
            if ship.health <= 0:
                game_over = True
        if sound_enabled:
            sound2 = pygame.mixer.Sound('data/music3.mp3')
            sound2.play()
        # Метеор уничтожается в любом случае
        create_particles(meteor.rect.center)

    # Проверка сбора power-up
    power_up_collisions = pygame.sprite.spritecollide(ship, power_ups, True)
    for power_up in power_up_collisions:
        if isinstance(power_up, PowerUp):
            ship.invincible = True
            ship.invincible_start_time = pygame.time.get_ticks()
            ship.paused_duration = 0
        elif isinstance(power_up, HealthPowerUp):
            ship.health = 100  # Восстановление здоровья до максимума
            if ship.health > 100:  # Защита от превышения
                ship.health = 100

    # Создание метеоров в зависимости от целевого счета
    interval = meteor_spawn_interval(target_score)
    if interval == 250:
        interval -= int(score / 2)
        if interval < 100:
            interval = 100
    if current_time - last_meteor_time >= interval:
        Meteor(target_score)
        last_meteor_time = current_time

    # Создание power-up случайно
    if random.random() < 0.001:  # 0,1% шанс каждую итерацию
        # 50% шанс на обычный power-up, 50% на восстановление здоровья
        if random.choice([True, False]):
            PowerUp()
        else:
            HealthPowerUp()

    # Обновление лучшего счета в базе данных
    if score > best_score:
        update_best_score(score)
        best_score = score

    # Проверка достижения 100 очков на 3-м уровне
    if target_score == 100 and score >= 100 and not level_passed:
        level_passed = True  # Устанавливаем флаг, что уровень пройден
        level_passed_start_time = pygame.time.get_ticks()  # Запоминаем время начала отображения сообщения

    # Проверка на новый рекорд комбо
    if combo > max_combo:
        max_combo = combo
        if not show_new_record and not new_record_shown:  # Если флаг не установлен и сообщение еще не показывалось
            show_new_record = True
            new_record_shown = True  # Устанавливаем флаг, что сообщение было показано
            draw_new_combo_record()  # Вызываем функцию для отображения сообщения


def render_screen():
    global stop_time, level_passed_start_time, level_passed, level_passed_message_shown
    screen.fill((0, 0, 0))
    all_sprites.draw(screen)
    draw_score()
    draw_health()
    draw_combo()

    # Отображение сообщения о новом рекорде комбо
    if show_new_record:
        draw_new_combo_record()

    # Отображение сообщения о прохождении 3-го уровня
    if level_passed and not level_passed_message_shown:
        current_time = pygame.time.get_ticks()
        if level_passed_start_time == 0:
            level_passed_start_time = current_time  # Запоминаем время начала отображения

        # Если прошло меньше 5 секунд, отображаем сообщение
        if current_time - level_passed_start_time < 5000:  # 5000 мс = 5 секунд
            level_passed_text = big_font.render("Вы прошли 3-й уровень!", True, (255, 255, 0))  # Желтый цвет
            screen.blit(level_passed_text, (20, 10))  # Позиция в верхней части экрана
        else:
            level_passed_message_shown = True  # Сообщение было показано, больше не отображаем

    # Отображение плашки power-up в верхнем левом углу
    if ship.invincible:
        power_up_indicator = pygame.transform.scale(power_up_img, (30, 30))
        screen.blit(power_up_indicator, (350, 30))  # Позиция в верхнем правом углу

    pygame.display.flip()


def reset_game_state():
    global game_over, all_sprites, meteors, bullets, power_ups, sound_enabled
    game_over = False
    all_sprites.empty()
    meteors.empty()
    bullets.empty()
    power_ups.empty()
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
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_s:
                    sound_enabled = not sound_enabled
                    if sound_enabled:
                        pygame.mixer.music.set_volume(0.5)
                        pygame.mixer.music.unpause()
                    else:
                        pygame.mixer.music.set_volume(0)
                        pygame.mixer.music.pause()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                waiting = False
        screen.blit(end_game.image, end_game.rect)
        screen.blit(press_text, press_rect)
        pygame.display.flip()
        clock.tick(60)


def meteor_spawn_interval(target_score):
    if target_score == 100:
        return 250
    elif target_score == 50:
        return 400
    else:
        return 600


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


def draw_score():
    score_text = font.render(f"Счёт: {score}", True, (255, 255, 255))
    screen.blit(score_text, (10, 10))


def draw_health():
    if ship.health < 0:
        ship.health = 0
    health_text = font.render(f"Здоровье: {ship.health}%", True, (255, 255, 255))
    screen.blit(health_text, (10, 30))


def draw_combo():
    combo_text = font.render(f"Комбо: {combo}", True, (255, 255, 255))
    screen.blit(combo_text, (10, 50))


# Добавляем переменную для отслеживания времени отображения сообщения
new_record_start_time = 0


def draw_new_combo_record():
    global new_record_start_time, show_new_record
    current_time = pygame.time.get_ticks()

    # Если сообщение только что появилось, запоминаем время
    if show_new_record and new_record_start_time == 0:
        new_record_start_time = current_time

    # Если прошло больше 1 секунды, скрываем сообщение
    if current_time - new_record_start_time > 1000:
        show_new_record = False
        new_record_start_time = 0
        return

    # Рисуем сообщение желтым цветом
    new_record_text = big_font.render("Новый рекорд", True, (255, 255, 0))  # Желтый цвет
    combo_record_text = font.render(f"Комбо: {combo}", True, (255, 255, 0))  # Желтый цвет
    screen.blit(new_record_text, (100, 150))
    screen.blit(combo_record_text, (150, 200))


# Цикл меню
def draw_menu(best_score, last_score, max_combo):
    screen.fill((0, 0, 0))
    level1 = font.render("1 уровень", True, (255, 255, 255))
    level2 = font.render("2 уровень", True, (255, 255, 255))
    level3 = font.render("3 уровень", True, (255, 255, 255))
    screen.blit(level1, (140, 90))
    screen.blit(level2, (140, 160))
    screen.blit(level3, (140, 230))

    arcade = font.render("Аркадный режим", True, (255, 255, 255))
    screen.blit(arcade, (120, 290))

    score_text = font.render(f"Лучший счет: {best_score}", True, (255, 255, 255))
    screen.blit(score_text, (120, 20))

    last_score_text = font.render(f"Последний результат: {last_score}", True, (255, 255, 255))
    screen.blit(last_score_text, (95, 40))  # Отображение последнего результата

    max_combo_text = font.render(f"Максимальное комбо: {max_combo}", True, (255, 255, 255))
    screen.blit(max_combo_text, (95, 60))  # Отображение максимального комбо

    sound_status = "Вкл" if sound_enabled else "Выкл"
    sound_text = font.render(f"Звук: {sound_status} (S)", True, (255, 255, 255))
    screen.blit(sound_text, (140, 350))  # Позиция под аркадным режимом

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
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_s:
                sound_enabled = not sound_enabled
                if sound_enabled:
                    pygame.mixer.music.set_volume(0.5)
                    pygame.mixer.music.unpause()
                else:
                    pygame.mixer.music.set_volume(0)
                    pygame.mixer.music.pause()
        elif event.type == pygame.MOUSEBUTTONDOWN:
            x, y = event.pos
            if 140 <= x <= 260 and 90 <= y <= 130:
                game_loop(20)  # Уровень 1
            elif 140 <= x <= 260 and 160 <= y <= 210:
                game_loop(50)  # Уровень 2
            elif 140 <= x <= 260 and 230 <= y <= 280:
                game_loop(100)  # Уровень 3
            elif 120 <= x <= 300 and 290 <= y <= 340:
                game_loop(100000)  # Аркадный режим

    draw_menu(best_score, last_score, max_combo)  # Передаем max_combo в draw_menu
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
