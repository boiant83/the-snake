"""Игра «Змейка» на pygame."""
from random import choice, randint

import pygame as pg

SCREEN_WIDTH, SCREEN_HEIGHT = 640, 480
GRID_SIZE = 20
GRID_WIDTH = SCREEN_WIDTH // GRID_SIZE
GRID_HEIGHT = SCREEN_HEIGHT // GRID_SIZE
UP = (0, -1)
DOWN = (0, 1)
LEFT = (-1, 0)
RIGHT = (1, 0)
BOARD_BACKGROUND_COLOR = (128, 128, 128)
DEFAULT_BODY_COLOR = (255, 255, 255)
BORDER_COLOR = (93, 216, 228)
APPLE_COLOR = (255, 0, 0)
SNAKE_COLOR = (0, 255, 0)
SPEED = 4
SPEED_STEP = 1
SPEED_MIN, SPEED_MAX = 1, 60
CENTER_CELL = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
RECORD_FILE_PATH = 'snake_record.txt'

# Соответствие «клавиша + текущее направление → новое направление».
# Пар с разворотом на 180 градусов в наборе нет — разворот невозможен.
# Одни и те же повороты доступны и стрелками, и клавишами WASD.
KEYS_TO_DIRECTIONS = {
    (UP, pg.K_LEFT): LEFT,
    (DOWN, pg.K_LEFT): LEFT,
    (UP, pg.K_RIGHT): RIGHT,
    (DOWN, pg.K_RIGHT): RIGHT,
    (LEFT, pg.K_UP): UP,
    (RIGHT, pg.K_UP): UP,
    (LEFT, pg.K_DOWN): DOWN,
    (RIGHT, pg.K_DOWN): DOWN,
    (UP, pg.K_a): LEFT,
    (DOWN, pg.K_a): LEFT,
    (UP, pg.K_d): RIGHT,
    (DOWN, pg.K_d): RIGHT,
    (LEFT, pg.K_w): UP,
    (RIGHT, pg.K_w): UP,
    (LEFT, pg.K_s): DOWN,
    (RIGHT, pg.K_s): DOWN,
}

# Все клетки игрового поля:
ALL_CELLS = set(
    (x * GRID_SIZE, y * GRID_SIZE)
    for x in range(GRID_WIDTH)
    for y in range(GRID_HEIGHT)
)

# Настройка игрового окна:
screen = pg.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), 0, 32)

# Заголовок окна игрового поля:
pg.display.set_caption('Змейка')

# Настройка времени:
clock = pg.time.Clock()


def load_record():
    """Загружает сохранённый рекорд длины змейки из файла."""
    try:
        with open(RECORD_FILE_PATH, 'r', encoding='utf-8') as record_file:
            return int(record_file.read())
    except (OSError, ValueError):
        return 1


def save_record(record):
    """Сохраняет рекорд длины змейки в файл."""
    with open(RECORD_FILE_PATH, 'w', encoding='utf-8') as record_file:
        record_file.write(str(record))


class GameObject:
    """Базовый класс для всех игровых объектов."""

    def __init__(self, position=CENTER_CELL, body_color=DEFAULT_BODY_COLOR):
        self.position = position
        self.body_color = body_color

    def draw_cell(self, position, color=None):
        """Рисует одну ячейку поля в координатах position.

        Если color не передан, используется цвет тела объекта.
        Если ячейка заливается цветом фона, рамка не рисуется —
        иначе затёртая клетка оставляла бы «след» на поле.
        """
        fill_color = color or self.body_color
        rect = pg.Rect(position, (GRID_SIZE, GRID_SIZE))
        pg.draw.rect(screen, fill_color, rect)
        if fill_color != BOARD_BACKGROUND_COLOR:
            pg.draw.rect(screen, BORDER_COLOR, rect, 1)

    def draw(self):
        """Отрисовка объекта. Переопределяется в наследниках."""
        raise NotImplementedError(
            f'Метод draw() не определён в классе {type(self).__name__}'
        )


class Apple(GameObject):
    """Яблоко: появляется в случайной свободной клетке игрового поля."""

    def __init__(self, occupied_positions=(), body_color=APPLE_COLOR):
        super().__init__(body_color=body_color)
        self.randomize_position(occupied_positions)

    def randomize_position(self, occupied_positions=()):
        """Выбирает случайную свободную клетку поля и записывает её."""
        free_cells = tuple(ALL_CELLS - set(occupied_positions))
        self.position = choice(free_cells)

    def draw(self):
        """Рисует яблоко квадратом размером в одну клетку."""
        self.draw_cell(self.position)


class Snake(GameObject):
    """Змейка: хранит сегменты, двигается, растёт и сбрасывается."""

    def __init__(self, body_color=SNAKE_COLOR):
        super().__init__(body_color=body_color)
        self.reset()

    def reset(self):
        """Возвращает змейку в начальное состояние после столкновения."""
        self.length = 1
        self.positions = [CENTER_CELL]
        self.direction = choice([UP, DOWN, LEFT, RIGHT])
        self.last = None

    def get_head_position(self):
        """Возвращает координаты головы змейки."""
        return self.positions[0]

    def update_direction(self, new_direction):
        """Задаёт змейке новое направление движения."""
        self.direction = new_direction

    def move(self):
        """Перемещает змейку на одну клетку в текущем направлении."""
        head_x, head_y = self.get_head_position()
        dir_x, dir_y = self.direction
        self.positions.insert(0, (
            (head_x + dir_x * GRID_SIZE) % SCREEN_WIDTH,
            (head_y + dir_y * GRID_SIZE) % SCREEN_HEIGHT,
        ))
        self.last = (
            self.positions.pop()
            if len(self.positions) > self.length
            else None
        )

    def draw(self):
        """Рисует голову змейки и затирает клетку ушедшего хвоста."""
        self.draw_cell(self.get_head_position())
        if self.last:
            self.draw_cell(self.last, BOARD_BACKGROUND_COLOR)


def handle_keys(snake, speed):
    """Обрабатывает нажатия клавиш: выход, поворот, изменение скорости."""
    for event in pg.event.get():
        is_exit = event.type == pg.QUIT or (
            event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE
        )
        if is_exit:
            pg.quit()
            raise SystemExit
        if event.type == pg.KEYDOWN:
            if event.key in (pg.K_EQUALS, pg.K_KP_PLUS):
                speed = min(speed + SPEED_STEP, SPEED_MAX)
            elif event.key in (pg.K_MINUS, pg.K_KP_MINUS):
                speed = max(speed - SPEED_STEP, SPEED_MIN)
            else:
                snake.update_direction(
                    KEYS_TO_DIRECTIONS.get(
                        (snake.direction, event.key),
                        snake.direction,
                    )
                )
    return speed


def main():
    """Основной игровой цикл."""
    pg.init()
    snake = Snake()
    apple = Apple(occupied_positions=snake.positions)
    screen.fill(BOARD_BACKGROUND_COLOR)
    record = load_record()
    speed = SPEED

    while True:
        speed = handle_keys(snake, speed)
        clock.tick(speed)
        snake.move()

        head = snake.get_head_position()
        if head == apple.position:
            snake.length += 1
            if snake.length > record:
                record = snake.length
                save_record(record)
            apple.randomize_position(snake.positions)
        elif head in snake.positions[3:]:
            # Голова может укусить себя, только начиная с 4-го сегмента.
            snake.reset()
            screen.fill(BOARD_BACKGROUND_COLOR)

        apple.draw()
        snake.draw()
        pg.display.set_caption(
            f'Змейка | Выход: ESC | Стрелки/WASD | '
            f'Скорость: {speed} («+»/«-») | Рекорд: {record}'
        )
        pg.display.update()


if __name__ == '__main__':
    main()
