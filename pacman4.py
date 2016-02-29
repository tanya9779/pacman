# coding: utf-8
import sys
import pygame
from pygame.locals import *
from math import floor
import random


def init_window():
    pygame.init()
    pygame.display.set_mode((512, 560))
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
            self.point_count = 0
            self.bonus_count = 0
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
                    elif '123456789'.count(s[j]) > 0: # Бонусный артефакт
                        obj = Bonus(i, j, tile_size, map_size)
                        self.map[i][j] = [ obj ]
                        self.bonus_count+=1
                    else: # на все свободные места насыпем белые шарики
                        obj = Ball(i, j, tile_size, map_size)
                        self.map[i][j] = [ obj ]
                        self.point_count+=1

                # читаем след строку из файла
                s=in_f.readline().rstrip()
                i+=1
            in_f.close()

        # Функция возвращает список обьектов в данной точке карты
        def get(self, x, y):
                return self.map[int(floor(x))][int(floor(y))]

        # ф-ция первоначальной установки Пакмана и приведений на карту - на стены и друг на друга не ставить
        def set(self, obj, new_x, new_y):
            n_point = self.map[new_x][new_y]
            # проверим, можно ли сюда поставить
            for obj2 in n_point:
                if isinstance(obj2, Wall) or isinstance(obj2,Bonus): # здесь стена или кто-то еще
                    return False
                # объект поместим в нужную клетку
            n_point.append(obj)
            obj.set_coord(new_x,new_y)
            return True

        # Функция, перемещающая произвольный обьект в новую точку
        # если нельзя поставить в указ точку, возвращает False
        def moveTo(self, obj, new_x, new_y):
                point = self.map[int(floor(obj.x))][int(floor(obj.y))]
                if obj in point:
                        n_point = self.map[int(floor(new_x))][int(floor(new_y))]
                        # проверим, можно ли сюда поставить
                        for obj2 in n_point:
                            if isinstance(obj2, Wall): # это стена
                                if obj2.is_solid() or isinstance(obj, Ghost) or isinstance(obj, SmartGhost):
                                    return False # здесь неразрушаемая стена или ты приведение
                                elif isinstance(obj, Pacman): # Pacman может разрушить
                                    n_point.remove(obj2) # удаляем стену
                                    break
                        point.remove(obj) # вытащим объект из прежней клетки карты и поместим в новую
                        n_point.append(obj)
                        obj.set_coord(new_x,new_y)
                        return True
                return False

        # рисование карты со свсеми объектами
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
        self.health = 0 # здоровье или энергия
        self.tile_size = tile_size
        self.map_size = map_size
        self.set_coord(x, y)

    def getHealth(self):
        return self.health

    # жив еще или уже сожрали?
    def is_alive(self):
        # если энергии >0, то еще жив
        return self.health > 0

    # атаковать цель
    def attack(self, target):
        if self.health < target.getHealth(): # если у цели энергии больше,
            target.attack(self) # то наоборот она будет атаковать
        else:
            self.health -= target.health # энергии поубавится
            target.health = 0 # мы пожрали цель

    # особенность - x,y с плавающей точкой - это потому что скорость не целое число
    def set_coord(self, x, y):
        self.x = x
        self.y = y
        # прямоугольник, который нужно перерисовать. floor() отбрасывает дробную часть числа
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

            if floor(self.x)!=floor(new_x) or floor(self.y)!=floor(new_y): # если это уже переход в другую клетку
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
                else: # не удалось передвинуться (уперлись в стену?) - поменяем направление и опять в цикл while
                    new_x = self.x
                    new_y = self.y
                    self.direction = random.randint(1,4)
                    # здесь нет выхода их цикла!!!
            else: # это только маленький шаг в пределах клетки
                self.x = new_x
                self.y = new_y
                break # выход из while

class SmartGhost(GameObject):
    def __init__(self, x, y, tile_size, map_size):
        GameObject.__init__(self, './resources/ghost.png', x, y, tile_size, map_size)
        self.health = 1000
        self.direction = 0
        self.velocity = 4.0 / 10.0

    def game_tick(self):
        super(SmartGhost, self).game_tick()
        new_x = self.x
        new_y = self.y

        if floor(self.x) == floor(pacman.x):
            if pacman.y > self.y:
                self.direction =2
            else:
                self.direction = 4
        elif floor(self.y) == floor(pacman.y):
             if pacman.x > self.x:
                 self.direction = 1
             else:
                 self.direction = 3
        else:
             # каждые 10 тиков случайно выбираем направление движение
            if self.tick % 10 ==0 or self.direction == 0:
                self.direction = random.randint(1,4)

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

            if floor(self.x)!=floor(new_x) or floor(self.y)!=floor(new_y): # если это уже переход в другую клетку
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
                else: # не удалось передвинуться (уперлись в стену?) - поменяем направление и опять в цикл while
                    new_x = self.x
                    new_y = self.y
                    self.direction = random.randint(1,4)
                    # здесь нет выхода их цикла!!!
            else: # это только маленький шаг в пределах клетки
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

    # переопределим метод рисования. Пакман должен поворачиваться в сторону движения
    def draw(self, scr):
        # вращаем картинку пакмана по часовой
        scr.blit(pygame.transform.rotate(self.image,90*(1-self.direction)), (self.screen_rect.x, self.screen_rect.y))


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
            if new_y <= 0:
                new_y = 0

        if floor(self.x)!=floor(new_x) or floor(self.y)!=floor(new_y): # вышли в другую клетку
            # шаг дробный, поэтому не каждый раз перемещаемся в другую клетку
            if map.moveTo(self, new_x, new_y ): # если стены не мешают передвинуться
                point = map.get(new_x, new_y) # это спискок
                ball = None # мы перебираем список point
                bonus = None # поэтому изменять список и
                ghost = None # сразу удалять объекты нельзя - запомним их
                for obj in point: # в клетке могут оказаться разные объекты
                    if isinstance(obj,Ball):
                        ball = obj # чуть позже удалим этот с карты
                        self.health+=ball.getHealth() # напитаемся энергией шарика
                    elif isinstance(obj,Bonus):
                        bonus = obj
                        self.health+=bonus.getHealth() # напитаемся энергией шарика
                    elif isinstance(obj,Ghost):
                        ghost = obj
                        if self.health>=ghost.getHealth():
                            self.attack(ghost)
                        else:
                            ghost.attack(self) # это конец - приведение сожрало пакмана
                if ball is not None:
                    point.remove(ball)
                    map.point_count-=1 # счетчик шариков
                if bonus is not None:
                    point.remove(bonus)
                    map.bonus_count-=1 # счетчик артефактов
                if self.is_alive() and ghost is not None: # если была встреча с привидением
                    point.remove(ghost) # если пакман сожрал привидение, то приведение нужно удалить
        else: # это перемещение в пределах клетки - запомним координаты
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

# класс белый шарик
class Ball(GameObject):
    def __init__(self, x, y, tile_size, map_size):
        GameObject.__init__(self, './resources/ball.png', x, y, tile_size, map_size)
        self.health = 100
        self.direction = 0
        self.velocity = 0

# Класс Артефакт
class Bonus(GameObject):
    def __init__(self, x, y, tile_size, map_size):
        GameObject.__init__(self, './resources/bonus.png', x, y, tile_size, map_size)
        self.health = 300
        self.direction = 0
        self.velocity = 0


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

def message_box(screen, message):
    # вывод вообщения в окошке по центру
    fontobject = pygame.font.Font(None,18)
    pygame.draw.rect(screen, (0,255,0),
                   ((screen.get_width() / 2) - 200,
                    (screen.get_height() / 2) - 20,
                    400,40), 0)
    pygame.draw.rect(screen, (255,255,255),
                   ((screen.get_width() / 2) - 202,
                    (screen.get_height() / 2) - 22,
                    404,44), 1)
    if len(message) != 0:
        screen.blit(fontobject.render(message, 1, (255,255,255)),
                ((screen.get_width() / 2) - 100, (screen.get_height() / 2) - 10))

    pygame.display.flip()

if __name__ == '__main__':
    init_window()
    tile_size = 32
    map_size = 16
    RED = (255,0,0) # класный цвет
    BLUE = (0,0,255) # синий
    map = Map(map_size, map_size)
    # создадим приведение
    ghost = Ghost(0, 0, tile_size, map_size)
    while not map.set(ghost,random.randint(0,15),random.randint(0,15)): # поищем место чтобы не в стене
        pass
    # добавим еще приведение
#    ghost2 = Ghost(0, 0, tile_size, map_size)
    ghost2=SmartGhost(0,0,tile_size,map_size)

    # картинка приведения у нас только одна -
    # перекрасим приведение в синий цвет
    pxarr = pygame.PixelArray(ghost2.image) # подсмотрено в интернете
    pxarr.replace(RED, BLUE,0.5) # как перекрашивать
    del pxarr # важно удалять объект PixelArray - иначе не работает дольше

    while not map.set(ghost2,random.randint(0,15),random.randint(0,15)):
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
        ghost2.game_tick()
        pacman.game_tick()
        draw_background(screen, background)
        map.draw(screen)
      
        # статус пакмана выведем
        # рисуем прямоугольник на screen c цветом (кр,зел,син) в коорд (x,y,длина,высота) с закраской
        # цвет и координаты в виде кортежей 
        pygame.draw.rect(screen, (0,0,255), (100,520,400,30), 1)
        fontobject = pygame.font.Font(None,18)
        # выведем надпись - цвет и координаты в виде кортежей
        screen.blit( fontobject.render('energy: ' + str(pacman.health), 1, (0,0,255)),(250,525) )

        pygame.display.update()


        pygame.time.delay(10)
        if not pacman.is_alive(): # pacman'а сожрали
            message_box(screen,'GHOST KILL YOU')
            pygame.time.delay(3000)
            break
        if not ( ghost.is_alive() or ghost2.is_alive() ): # пакман съел привидение
            message_box(screen,'YOU ARE HERO!!!')
            pygame.time.delay(3000)
            break
        if map.point_count==0 and map.bonus_count==0: # собраны все шары и бонусы
            message_box(screen,'Congratulations! All done!')
            pygame.time.delay(3000)
            break

