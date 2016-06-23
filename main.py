import kivy

kivy.require('1.0.6')
from kivy.config import Config

from kivy.uix.widget import Widget
from kivy.uix.label import Label

Config.set('graphics', 'width', '400')
Config.set('graphics', 'height', '717')

from kivy.app import App
from kivy.properties import NumericProperty, ListProperty, BooleanProperty, StringProperty
from kivy.clock import Clock
from kivy.graphics import Ellipse
from kivy.core.window import Window
from random import randint
from kivy.uix.image import Image
from math import radians, cos, sin, sqrt
from kivy.uix.screenmanager import ScreenManager, Screen, NoTransition
from kivy.core.audio import SoundLoader
from kivy.storage.jsonstore import JsonStore
from os.path import join

data_dir = App().user_data_dir

store = JsonStore(join(data_dir, 'store.json'))
try:
    store.get('highscore')
except KeyError:
    store.put('highscore', best=0)

circle_path = 'images/circle.png'
white_circle_path = 'images/white_circle.png'
grey_circle_path = 'images/grey_circle.png'
big_grey_circle_path = 'images/big_grey_circle.png'
big_orange_circle_path = 'images/orange_big_circle.png'

music_sound = SoundLoader.load('sounds/360music.wav')
win_sound = SoundLoader.load('sounds/360winsound.wav')
lose_sound = SoundLoader.load('sounds/360losesound.wav')
click_sound = SoundLoader.load('sounds/360clicksound.wav')
highscore_sound = SoundLoader.load('sounds/360highscoresound.wav')

size = Window.size
window_x = (size[0])
window_y = (size[1])

fps = 70
enemy_fps = 60
speed_time = 0
direction_time = 0
score = 0

sm = ScreenManager(transition=NoTransition())


class BackgroundTemplate(Widget):
    pass


class CircleButton(Widget):
    font_size = NumericProperty(20)

    def __init__(self, path, screen, radius, midpoint, font_size, word, **kwargs):
        super(CircleButton, self).__init__(**kwargs)
        self.texture = Image(source=path, mipmap=True).texture
        self.font_size = font_size
        self.radius = radius
        self.screen = screen
        self.midpoint = midpoint
        self.x = self.midpoint[0]
        self.y = self.midpoint[1]
        self.corner_pos = (self.x - self.radius, self.y - self.radius)
        self.word = word
        self.label = Label(center_x=self.x, center_y=self.y, font_size=self.font_size, text=self.word)

        with self.canvas:
            Ellipse(texture=self.texture, pos=self.corner_pos, size=(self.radius * 2, self.radius * 2))
        self.add_widget(self.label)

    def on_touch_down(self, touch):
        if self.corner_pos[0] < touch.x < self.x + self.radius and self.corner_pos[1] < touch.y < self.y + self.radius:
            sm.current = self.screen


class TinyButton(Widget):
    font_size = NumericProperty(20)

    def __init__(self, path, screen, radius, midpoint, font_size, word, **kwargs):
        super(TinyButton, self).__init__(**kwargs)
        self.texture = Image(source=path, mipmap=True).texture
        self.font_size = font_size
        self.radius = radius
        self.screen = screen
        self.midpoint = midpoint
        self.x = self.midpoint[0]
        self.y = self.midpoint[1]
        self.corner_pos = (self.x - self.radius, self.y - self.radius)
        self.word = word
        self.label = Label(x=self.midpoint[0], center_y=self.midpoint[1], font_size=self.font_size, text=self.word)
        self.label.bind(size=self.label.setter('text_size'))

        with self.canvas:
            Ellipse(texture=self.texture, pos=self.corner_pos, size=(self.radius * 2, self.radius * 2))
        self.add_widget(self.label)

    def on_touch_down(self, touch):
        global click_sound
        click_sound.play()
        if self.corner_pos[1] < touch.y < self.y + self.radius:
            sm.current = self.screen


class Circle(Widget):
    was_position = ListProperty()
    font_size = NumericProperty(20)
    text = StringProperty('0')

    def __init__(self, radius, midpoint, font_size, name='', **kwargs):
        super(Circle, self).__init__(**kwargs)
        self.texture = Image(source=circle_path, mipmap=True).texture

        self.font_size = font_size
        self.radius = radius
        self.midpoint = midpoint
        self.x = self.midpoint[0]
        self.y = self.midpoint[1]
        self.corner_pos = (self.x - self.radius, self.y - self.radius)

        self.position_list = []
        self.name = name
        self.is_full = False

        for position in range(0, 360):
            self.fi = radians(position)
            x = int(self.x - (self.radius + 30) * cos(self.fi)) - 11
            y = int(self.y + (self.radius + 30) * sin(self.fi)) - 11
            self.position_list.append((x, y))

        with self.canvas:
            self.ellipse = Ellipse(texture=self.texture, pos=self.corner_pos,
                                   size=(self.radius * 2, self.radius * 2))
            self.label = Label(text=self.text, pos=(self.x - 50, self.y - 50), font_size=self.font_size,
                               font_name='Montserrat-SemiBold.ttf', markup=True)
        self.bind(text=self.update)

    def update(self):
        if self.is_full:
            self.label.text = str(len(self.was_position) * 2) + '[color=f16a4c]*[/color]'
        else:
            self.label.text = str(len(self.was_position) * 2)


middle_circle = Circle(70, [window_x // 2, window_y // 2], name='middle', font_size=23)
down_circle = Circle(50, [window_x // 2, window_y // 2 - 180], name='down', font_size=18)
up_circle = Circle(50, [window_x // 2, window_y // 2 + 180], name='up', font_size=18)
menu_circle = Circle(70, [window_x // 2, window_y // 2], name='menu', font_size=25)


class Player(Widget):
    texture = Image(source=white_circle_path).texture
    diameter = 22
    radius = diameter // 2

    kill = BooleanProperty(True)

    def __init__(self, actual_circle, enemies_circle_list, main_circle=middle_circle, second_circle=up_circle,
                 third_circle=down_circle, **kwargs):

        super(Player, self).__init__(**kwargs)
        self.main_circle = main_circle
        self.second_circle = second_circle
        self.third_circle = third_circle
        self.actual_circle = actual_circle
        self.new_actual_circle = actual_circle
        self.position_list = self.actual_circle.position_list
        self.change_direction = True

        self.position = 180
        self.pos = self.position_list[self.position]

        self.speed = 2
        self.enemies_circle_list = enemies_circle_list
        self.x = self.pos[0] + self.radius
        self.y = self.pos[1] + self.radius

    def set_position(self):
        if self.change_direction:
            if self.position < len(self.position_list) - self.speed:
                self.position += self.speed
            else:
                self.position = 0
        else:
            if self.position > 0:
                self.position -= self.speed
            else:
                self.position = len(self.position_list) - self.speed
        self.pos = self.position_list[self.position]

    def set_circle(self):
        if self.x > self.actual_circle.x - self.actual_circle.radius * 0.4 and self.x < self.actual_circle.x + self.actual_circle.radius * 0.4:
            if self.actual_circle == self.main_circle:
                if self.y < self.actual_circle.y:
                    self.new_actual_circle = self.third_circle
                elif self.y > self.actual_circle.y:
                    self.new_actual_circle = self.second_circle
            elif self.actual_circle == self.third_circle:
                if self.y > self.actual_circle.y:
                    self.new_actual_circle = self.main_circle
            elif self.actual_circle == self.second_circle:
                if self.y < self.actual_circle.y:
                    self.new_actual_circle = self.main_circle
        if self.new_actual_circle != self.actual_circle:
            self.actual_circle = self.new_actual_circle
            if self.change_direction is False:
                self.change_direction = True
            else:
                self.change_direction = False
            if self.actual_circle == self.main_circle:
                if self.y < self.actual_circle.y:
                    self.position = int(abs(self.position - len(self.position_list)))

                elif self.y > self.actual_circle.y:
                    self.position = int(abs(self.position - len(self.position_list)))

            elif self.actual_circle == self.second_circle:
                if self.y < self.actual_circle.y:
                    self.position = int(abs(self.position - len(self.position_list)))

            elif self.actual_circle == self.third_circle:
                if self.y > self.actual_circle.y:
                    self.position = int(abs(self.position - len(self.position_list)))

        self.position_list = self.actual_circle.position_list

    def do_kill(self):

        global score, lose_sound
        for i in self.enemies_circle_list:
            distance = sqrt((i.x - self.x) ** 2 + (i.y - self.y) ** 2)
            if distance <= self.radius + i.radius:
                self.actual_circle = middle_circle
                self.position_list = middle_circle.position_list
                self.x, self.y = middle_circle.position_list[self.position]
                for i in self.enemies_circle_list:
                    i.speed = 0
                    self.position = 0

                self.speed = 0
                self.position = 180

                lose_sound.play()
                sm.current = 'game_over_screen'
                return True


class Enemy(Widget):
    texture = Image(source=grey_circle_path).texture
    diameter = 22
    radius = diameter // 2
    change_direction = BooleanProperty(True)
    position = NumericProperty(0)

    def __init__(self, circle, **kwargs):
        super(Enemy, self).__init__(**kwargs)
        self.actual_circle = circle
        self.new_actual_circle = circle
        self.position_list = self.actual_circle.position_list
        self.local_speed_time = 0
        self.local_direction_time = 0
        self.pos = self.position_list[self.position]
        self.speed = 1
        self.min_speed = 1
        self.max_speed = 1

        self.x = self.pos[0] + self.diameter // 2
        self.y = self.pos[1] + self.diameter // 2

    def set_position(self):
        if self.change_direction == True:
            if self.position < len(self.position_list) - self.speed:
                self.position += self.speed
            else:
                self.position = 0
        else:
            if self.position > 0:
                self.position -= self.speed
            else:
                self.position = len(self.position_list) - self.speed
        self.pos = self.position_list[self.position]

    def change_speed(self):

        if self.min_speed != self.max_speed:
            self.speed = randint(self.min_speed, self.max_speed)



    def update(self):
        global speed_time, direction_time
        self.set_position()
        if speed_time > self.local_speed_time and self.local_speed_time != 0:
            if randint(0, 1):
                self.change_speed()
                speed_time = 0

        if direction_time > self.local_direction_time and self.local_direction_time != 0:
            if randint(0, 1):
                self.change_direction = not self.change_direction
                direction_time = 0


class GameScreen(Screen):
    global score, direction_time, middle_circle, up_circle, down_circle

    game_score = StringProperty(str(score))

    def __init__(self, **kwargs):
        super(GameScreen, self).__init__(**kwargs)

        self.middle_enemy = Enemy(middle_circle)
        self.up_enemy = Enemy(up_circle)
        self.down_enemy = Enemy(down_circle)
        self.enemies_circle_list = [self.middle_enemy, self.down_enemy, self.up_enemy]
        self.circle_list = [middle_circle, up_circle, down_circle]
        self.player_circle = Player(middle_circle, self.enemies_circle_list, middle_circle, up_circle, down_circle)


    def raise_level(self, dt):
        global score, fps, direction_time, enemy_fps

        if score > 5:
            fps = 75
            enemy_fps = 68
            for i in self.enemies_circle_list:
                i.local_direction_time = 300

        if score > 11:

            fps = 82
            enemy_fps = 72
            for i in self.enemies_circle_list:
                i.local_direction_time = 250
                i.local_speed_time = 250
                i.max_speed = 2

        if score > 23:
            fps = 90
            enemy_fps = 82
            for i in self.enemies_circle_list:
                i.local_direction_time = 200
                i.local_speed_time = 225

        if score > 35:
            fps = 99
            enemy_fps = 90
            for i in self.enemies_circle_list:
                i.local_direction_time = 150
                i.local_speed_time = 200


        if score > 47:
            fps = 110
            enemy_fps = 100
            for i in self.enemies_circle_list:
                i.local_direction_time = 125
                i.local_speed_time = 125

        if score > 59:
            fps = 120
            enemy_fps = 110
            for i in self.enemies_circle_list:
                i.local_direction_time = 100
                i.local_speed_time = 100
                i.max_speed = 2

        if score > 71:
            for i in self.enemies_circle_list:
                i.local_direction_time = 90
                i.local_speed_time = 125

        if score > 83:
            for i in self.enemies_circle_list:
                i.local_direction_time = 125
                i.local_speed_time = 125
                i.max_speed = 3

        if score > 95:
            for i in self.enemies_circle_list:
                i.local_direction_time = 125

    def is360(self, player, main_circle, all=True):

        global score, win_sound, middle_circle, down_circle, up_circle
        if player.position not in player.actual_circle.was_position:
            player.actual_circle.was_position.append(player.position)
            if (len(player.actual_circle.was_position)) == len(player.actual_circle.position_list) / 2:
                player.actual_circle.is_full = True

                score += 1
                win_sound.play()
        if all == True:
            if middle_circle.is_full and up_circle.is_full and down_circle.is_full:
                score += 3
                for i in self.circle_list:
                    i.was_position = []
                    i.is_full = False

        else:
            if main_circle.is_full:
                main_circle.was_position = []
                main_circle.is_full = False

    def restart(self):
        global speed_time, direction_time, score, time, enemies_circle_list, fps, enemy_fps
        self.player_circle.kill = False

        fps = 70
        enemy_fps = 60
        speed_time = 0
        direction_time = 0


        self.player_circle.actual_circle, self.player_circle.new_actual_circle = middle_circle, middle_circle
        self.player_circle.x, self.player_circle.y = self.player_circle.position_list[self.player_circle.position]
        self.player_circle.speed = 2
        self.player_circle.position = 180
        for i in self.enemies_circle_list:
            i.position = 0
            i.speed = 1
            i.max_speed = 1
            i.local_direction_time = 0

        for i in self.circle_list:
            i.was_position = []
            i.is_full = False

    def update(self, dt):

        global score, direction_time, sm, speed_time
        self.game_score = str(score)
        self.player_circle.set_position()
        self.is360(self.player_circle, self.player_circle.actual_circle, all=True)
        self.raise_level(dt)
        direction_time += 1
        speed_time += 1

        for circle in self.circle_list:
            circle.update()

        if self.player_circle.do_kill():
            sm.current = 'game_over_screen'
            self.restart()


    def enemy_update(self, dt):

        for circle in self.enemies_circle_list:
            circle.update()




    def on_touch_down(self, touch):
        if touch.pos[0] > 200:
            if self.player_circle.change_direction == False:
                self.player_circle.change_direction = True
            else:
                self.player_circle.change_direction = False
        elif touch.pos[0] < 200:
            self.player_circle.set_circle()

    def on_pre_enter(self):
        global fps, enemy_fps, score
        score = 0
        Clock.schedule_interval(self.update, 1.0 / fps)
        Clock.schedule_interval(self.enemy_update,1.0 /  enemy_fps)

    def on_leave(self):
        Clock.unschedule(self.update)
        Clock.unschedule(self.enemy_update)


class GameOverScreen(Screen):
    global score, store

    best_result = str(store.get('highscore')['best'])

    game_score = StringProperty(score)
    highscore = StringProperty(best_result)

    def __init__(self, **kwargs):
        super(GameOverScreen, self).__init__(**kwargs)
        self.again_button = CircleButton(big_grey_circle_path, 'game_screen', 70, [window_x // 2, window_y // 2], 40,
                                         'again')
        self.menu_button = CircleButton(big_grey_circle_path, 'menu_screen', 40,
                                        [window_x // 2 + 125, window_y // 2 - 125], 20, 'menu')
        self.add_widget(self.again_button)
        self.add_widget(self.menu_button)

    def update(self, dt):
        global score, direction_time, sm
        self.game_score = str(score)

    def on_pre_enter(self):
        global score, store

        if score > int(self.highscore):
            self.highscore = str(score)
            store.put('highscore', best=self.highscore)
            highscore_sound.play()

        Clock.schedule_interval(self.update, 1.0 / 60)

    def on_leave(self):
        Clock.unschedule(self.update)


class MenuScreen(Screen):
    game_score = StringProperty(str(score))

    def __init__(self, **kwargs):
        global menu_circle
        super(MenuScreen, self).__init__(**kwargs)

        self.play_button = TinyButton(big_orange_circle_path, 'game_screen', 25, [40, window_y // 2 - 150], 25,
                                      '   play')
        self.htp_button = TinyButton(big_grey_circle_path, 'htp_screen', 25, [40, window_y // 2 - 220], 25,
                                     '                   how to play')
        self.menu_circle = menu_circle
        self.menu_player = Player(menu_circle, [], main_circle=menu_circle)

        self.add_widget(self.play_button)
        self.add_widget(self.htp_button)
        # self.add_widget(self.quit_button)
        self.circle_list = [menu_circle]

    def is360(self, player, main_circle, all=True, sound=True, second_circle=up_circle, third_circle=down_circle):

        global score

        if player.position not in player.actual_circle.was_position:
            player.actual_circle.was_position.append(player.position)
            if (len(player.actual_circle.was_position)) == len(player.actual_circle.position_list) / 2:
                player.actual_circle.is_full = True

                score += 1

        if all == True:
            if main_circle.is_full and second_circle.is_full and third_circle.is_full:
                score += 3
                for i in self.circle_list:
                    i.was_position = []
                    i.is_full = False

        else:

            if main_circle.is_full:
                main_circle.was_position = []
                main_circle.is_full = False

    def update(self, dt):
        self.menu_player.set_position()
        self.is360(self.menu_player, self.menu_circle, all=False)
        self.menu_circle.update()

    def on_pre_enter(self):
        Clock.schedule_interval(self.update, 1.0 / 60)

    def on_leave(self):
        Clock.unschedule(self.update)


class HtpScreen(Screen):
    def __init__(self, **kwargs):
        super(HtpScreen, self).__init__(**kwargs)

        self.back1tomenu_button = CircleButton(big_grey_circle_path, 'menu_screen', 80,
                                               [window_x // 2, window_y // 2 - 200], 25, 'back')
        self.add_widget(self.back1tomenu_button)


class My360App(App):
    def on_pause(self):
        return True

    def on_resume(self):
        pass

    def build(self):
        global sm, highscore

        music_sound.loop = True
        music_sound.play()
        game_screen = GameScreen(size=(400, 717), name='game_screen')
        menu_screen = MenuScreen(name='menu_screen')

        game_over_screen = GameOverScreen(name='game_over_screen')
        htp_screen = HtpScreen(name='htp_screen')

        menu_screen.add_widget(menu_screen.menu_player)
        menu_screen.add_widget(menu_circle)
        game_screen.add_widget(middle_circle)
        game_screen.add_widget(up_circle)
        game_screen.add_widget(down_circle)

        game_screen.add_widget(game_screen.middle_enemy)
        game_screen.add_widget(game_screen.down_enemy)
        game_screen.add_widget(game_screen.up_enemy)
        game_screen.add_widget(game_screen.player_circle)

        sm.add_widget(menu_screen)
        sm.add_widget(game_screen)
        sm.add_widget(game_over_screen)
        sm.add_widget(htp_screen)

        return sm


if __name__ == '__main__':
    My360App().run()
