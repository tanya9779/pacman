import sys
import pygame
from pygame.locals import *
from math import floor
import random


def init_window():
    pygame.init()
    pygame.display.set_mode((512, 512))
    pygame.display.set_caption('Pacman')


def draw_background(scr, img=None):
    if img:
        scr.blit(img, (0, 0))
    else:
        bg = pygame.Surface(scr.get_size())
        bg.fill((128, 128, 128))
        scr.blit(bg, (0, 0))

# класс Карта хранит все стены, все артефакты за стенами и вкусняшки (белые шарики везде)
# загружать карту из файла. Легенда: X-неразрушаемая O-разрушаемая стена
# 1-9 доп артефакты за разрушаемой стеной или просто на пути
# Класс будет рисовать стены (2-х типов) и др.
# потом на карту методом set ставятся привидения и Пакман

class Map:
        def __init__(self, w, h):
            self.map = [ [list()]*w for i in range(h) ] # каждая ячейка это список объектов
            # загрузим карту из файла
            in_f=open('map.txt','r')
            s=in_f.readline().rstrip()
            i=0
            while len(s)>0:
                for j in range(len(s)):
                    if s[j]=='X': # неразрушаемая стена
                        obj = Wall(i, j, tile_size, map_size)
                        obj.set_solid(True) # неразрушаемая
                        self.map[i][j] = [ obj ]
                    elif s[j]=='O': # разрушаемая стена
                        obj = Wall(i, j, tile_size, map_size)
                        self.map[i][j] = [ obj ]
                    # FIXME в файле цифрами 1-9 обозначены артефакты внутри стен - их реализовать

                # читаем след строку из файла
                s=in_f.readline().rstrip()
                i+=1
            in_f.close()

        # Функция возвращает список обьектов в данной точке карты
        def get(self, x, y):
                return self.map[floor(x)][floor(y)]

        # ф-ция первоначальной установки Пакмана и приведений на карту - на стены и друг на друга не ставить
        def set(self, obj, new_x, new_y):
            n_point = self.map[new_x][new_y]
            # проверим, можно ли сюда поставить
            for obj2 in n_point:
                if isinstance(obj2, Wall): # здесь стена или кто-то еще
                    return False
                # объект поместим в нужную клетку
            n_point.append(obj)
            obj.set_coord(new_x,new_y)
            return True

        # Функция, перемещающая произвольный обьект в новую точку
        # если нельзя поставить в указ точку, возвращает False
        def moveTo(self, obj, new_x, new_y):
                point = self.map[floor(obj.x)][floor(obj.y)]
                if obj in point:
                        n_point = self.map[floor(new_x)][floor(new_y)]
                        # проверим, можно ли сюда поставить
                        for obj2 in n_point:
                            if isinstance(obj2, Wall): # это стена
                                if obj2.is_solid() or isinstance(obj, Ghost):
                                    return False # здесь неразрушаемая стена или ты приведение
                                elif isinstance(obj, Pacman): # Pacman может разрушить
                                    n_point.remove(obj2) # удаляем стену
                                    break
                        point.remove(obj) # вытащим объект из прежней клетки карты и поместим в новую
                        n_point.append(obj)
                        obj.set_coord(new_x,new_y)
                        return True
                return False

        def draw(self,scr):
            for i in range(len(self.map)):
                for j in range(len(self.map[i])):
                    li=self.map[i][j]
                    for obj in li:
                        obj.draw(scr)


class GameObject(pygame.sprite.Sprite):
    def __init__(self, img, x, y, tile_size, map_size):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.image.load(img)
        self.screen_rect = None
        self.x = 0
        self.y = 0
        self.tick = 0
        self.health = 0
        self.tile_size = tile_size
        self.map_size = map_size
        self.set_coord(x, y)

    def getHealth(self):
        return self.health

    def is_alive(self):
        return self.health > 0

    def attack(self, target):
        if self.health < target.getHealth():
            target.attack(self)
        else:
            self.health -= target.health
            target.health = 0


    # особенность - x,y с плавающей точкой
    def set_coord(self, x, y):
        self.x = x
        self.y = y
        self.screen_rect = Rect(floor(x) * self.tile_size, floor(y) * self.tile_size, self.tile_size, self.tile_size )

    def game_tick(self):
        self.tick += 1

    def draw(self, scr):
        scr.blit(self.image, (self.screen_rect.x, self.screen_rect.y))


# класс Привидение.
# это бестолковое привидение - не обладает зрением, бродит произвольным образом,
# натыкаясь на стены, меняет направление. Также меняет направление в случайный момент времени
class Ghost(GameObject):
    def __init__(self, x, y, tile_size, map_size):
        GameObject.__init__(self, './resources/ghost.png', x, y, tile_size, map_size)
        self.health = 1000
        self.direction = 0
        self.velocity = 4.0 / 10.0

    def game_tick(self):
        super(Ghost, self).game_tick()
        new_x = self.x
        new_y = self.y
        if self.tick % random.randint(3,13) == 0 or self.direction == 0:
            self.direction = random.randint(1, 4) # случайным образом меняет направление движения

        while True:
            # если это граница поля, то менять направление
            if self.direction == 1:
                new_x = self.x + self.velocity
                if new_x >= self.map_size-1:
                    new_x = self.map_size-1
                    self.direction = random.randint(1, 4)
            elif self.direction == 2:
                new_y = self.y + self.velocity
                if new_y >= self.map_size-1:
                    new_y = self.map_size-1
                    self.direction = random.randint(1, 4)
            elif self.direction == 3:
                new_x = self.x - self.velocity
                if new_x <= 0:
                    new_x = 0
                    self.direction = random.randint(1, 4)
            elif self.direction == 4:
                new_y = self.y - self.velocity
                if new_y <= 0:
                    new_y = 0
                    self.direction = random.randint(1, 4)

            if floor(self.x)!=floor(new_x) or floor(self.y)!=floor(new_y):
                # если это уже переход в другую клетку
                if map.moveTo(self, new_x, new_y ): # проверка, не мешает ли стена
                    # проверим, нет ли здесь пакмана
                    point = map.get(new_x, new_y)
                    for obj in point: # в клетке могут оказаться разные объекты
                        if isinstance(obj,Pacman):
                            if self.health>=obj.getHealth():
                                self.attack(obj)
                                point.remove(obj) # это конец - приведение сожрало пакмана
                            else:
                                obj.attack(self)
                                point.remove(self) # пакман съел это привидение
                    break # выход из while
                else: # не удалось передвинуться - поменяем направление
                    new_x = self.x
                    new_y = self.y
                    self.direction = random.randint(1,4)
                    # здесь нет выхода их цикла!!!
            else: # маленький шаг в пределах клетки
                self.x = new_x
                self.y = new_y
                break # выход из while

# класс Пакман
class Pacman(GameObject):
    def __init__(self, x, y, tile_size, map_size):
        GameObject.__init__(self, './resources/pacman.png', x, y, tile_size, map_size)
        self.health = 500
        self.direction = 0
        self.velocity = 4.0 / 10.0
        self.energy = 0

    # вызывается с каждым "тактом" игры
    def game_tick(self):
        super(Pacman, self).game_tick()
        new_x = self.x
        new_y = self.y

        if self.direction == 1:
            new_x = self.x + self.velocity
            if new_x >= self.map_size-1:
                new_x = self.map_size-1
        elif self.direction == 2:
            new_y = self.y + self.velocity
            if new_y >= self.map_size-1:
                new_y = self.map_size-1
        elif self.direction == 3:
            new_x = self.x - self.velocity
            if new_x <= 0:
                new_x = 0
        elif self.direction == 4:
            new_y = self.y - self.velocity
            if new_x <= 0:
                new_y = 0

        if floor(self.x)!=floor(new_x) or floor(self.y)!=floor(new_y):
            # шаг дробный, поэтому не каждый раз перемещаемся в другую клетку
            if map.moveTo(self, new_x, new_y ): # если стены не мешают передвинуться
                point = map.get(new_x, new_y)
                ghost = None # сразу удалять объекты нельзя - запомним их
                for obj in point: # в клетке могут оказаться разные объекты
                    if isinstance(obj,Ghost):
                        ghost = obj
                        if self.health>=ghost.getHealth():
                            self.attack(ghost)
                        else:
                            ghost.attack(self) # это конец - приведение сожрало пакмана
                if self.is_alive() and ghost is not None: # если была встреча с привидением
                    point.remove(ghost) # если пакман сожрал привидение, то приведение нужно удалить
        else:
            self.x = new_x
            self.y = new_y

# класс стена
class Wall(GameObject):
    def __init__(self, x, y, tile_size, map_size):
        GameObject.__init__(self, './resources/wall.png', x, y, tile_size, map_size)
        self.direction = 0
        self.velocity = 0
        self.solid = False # True если неразрушаемая

    def set_solid(self, s):
        self.solid = s

    def is_solid(self):
        return self.solid

def process_events(events, packman):
    for event in events:
        if (event.type == QUIT) or (event.type == KEYDOWN and event.key == K_ESCAPE):
            sys.exit(0)
        elif event.type == KEYDOWN:
            if event.key == K_LEFT:
                packman.direction = 3
            elif event.key == K_RIGHT:
                packman.direction = 1
            elif event.key == K_UP:
                packman.direction = 4
            elif event.key == K_DOWN:
                packman.direction = 2
            elif event.key == K_SPACE:
                packman.direction = 0


if __name__ == '__main__':
    init_window()
    tile_size = 32
    map_size = 16
    map = Map(map_size, map_size)
    # создадим приведение
    ghost = Ghost(0, 0, tile_size, map_size)
    while not map.set(ghost,random.randint(0,15),random.randint(0,15)): # поищем место чтобы не в стене
        pass
    # создадим пакмана
    pacman = Pacman(5, 5, tile_size, map_size)
    while not map.set(pacman,random.randint(0,15),random.randint(0,15)):
        pass
    background = None #pygame.image.load("./resources/background.png")
    screen = pygame.display.get_surface()

    while 1: # здесь основной цикл
        process_events(pygame.event.get(), pacman)
        pygame.time.delay(100)
        ghost.game_tick()
        pacman.game_tick()
        draw_background(screen, background)
        map.draw(screen)
        pygame.display.update()

