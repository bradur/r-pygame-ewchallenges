# -*- coding: utf-8 -*-
import pygame
import datetime
import os

from pygame.locals import (QUIT, KEYDOWN, K_ESCAPE, K_DELETE, MOUSEBUTTONDOWN)
from input_box import InputBox
from button import Button
from title import Title
from bar import Bar


class BarchartApp(object):
    def __init__(self):
        pygame.init()
        os.environ["SDL_VIDEO_CENTERED"] = '1'  # Center the game window
        info = pygame.display.Info()            # get display info
        screen_height = info.current_h
        screen_width = info.current_w
        self.width, self.height = 800, 800
        if screen_height < 800:
            self.height = 600
            self.width = 600
            if screen_height < 600:
                self.height = screen_height
                self.width = screen_width
        self.maxheight = int(self.height*0.75)
        self.bbarheight = self.height/8
        self.padding = self.width/80
        self.buttonheight = self.padding*4
        self.screen = pygame.display.set_mode((self.width, self.height))
        title = "BarchartApp | {width}x{height}".format(
            width=self.width,
            height=self.height
        )
        pygame.display.set_caption(title)   # Set app name
        pygame.key.set_repeat(200, 80)

        self.fps = 60
        self.background = pygame.Surface((self.width, self.height))
        self.background.fill((255, 255, 255))
        self.background.convert()

        # grey bar that contains the GUI
        self.bottombar = pygame.Surface((self.width, self.bbarheight))
        self.bottombar.fill((240, 240, 240))

        # container for text inputs and buttons
        self.menu = pygame.sprite.OrderedUpdates()

        # container for the text input labels
        self.titles = pygame.sprite.Group()

        # container for the bar info section
        self.bartitles = pygame.sprite.Group()

        # container for the bars
        self.bars = pygame.sprite.OrderedUpdates()

        self.mouse = pygame.sprite.GroupSingle()
        self.mouse.add(Mouse())

    def main(self):
        self.main_menu()

        while True:
            if self.input() is False:
                return False
            self.menu.update(pygame.time.get_ticks())
            self.bars.update()
            self.draw()

    def input(self):
        self.mouse.sprite.move(pygame.mouse.get_pos())
        for event in pygame.event.get():

            # handle menu hover states
            for button in self.menu:
                if pygame.sprite.spritecollide(button, self.mouse, False):
                    button.hover()
                else:
                    button.normal()

            # handle bar hover states
            for bar in self.bars:
                if pygame.sprite.spritecollide(bar, self.mouse, False):
                    bar.hover()
                else:
                    bar.normal()

            if event.type == QUIT:
                return False

            if event.type == MOUSEBUTTONDOWN:

                # handle menuitem clicks
                for button in self.menu:
                    if pygame.sprite.spritecollide(button, self.mouse, False):
                        if button.action:
                            self.perform_action(button.action)
                        if not button.error:
                            button.select()
                    else:
                        button.deselect()

                # handle bar clicks
                for bar in self.bars:
                    if pygame.sprite.spritecollide(bar, self.mouse, False):
                        for _bar in self.bars:
                            _bar.deselect()
                        bar.select()
                        break
                if self.bars:
                    self.bar_menu()

            if event.type == KEYDOWN:

                # delete key deletes a selected bar
                if event.key == K_DELETE:
                    for bar in self.bars:
                        if bar.selected:
                            self.delete_bar()

                # escape key exits the app
                if event.key == K_ESCAPE:
                    return False

                # handle input to input boxes
                for box in self.menu:

                    # objects in self.menu with id 0 or 1 are input boxes
                    if box.selected and box.id in [0, 1]:
                        box.update_data(event.unicode)

    def bar_menu(self):

        # clear sprite groups for bar labels
        self.bartitles.empty()

        font = {"family": "Arial", "size": self.padding*1.5}

        colors = {
            "background": (205, 205, 205),
            "selected": (200, 200, 150),
            "hover": (150, 200, 150),
            "error": (200, 150, 150),
            "text": (25, 25, 25)
        }

        colors_text = {
            "background": (225, 225, 225),
            "selected": (250, 250, 200),
            "hover": (200, 250, 200),
            "error": (250, 200, 200),
            "text": (75, 75, 75)
        }

        bar_selected = ""

        # find the selected bar
        for bar in self.bars:
            if bar.selected:
                bar_selected = bar

        if bar_selected:

            font["size"] = int(self.height/80*2)

            padd = self.padding*5
            xpos = padd+self.height/8*3+font["size"]*3*2+self.bbarheight

            button_delete_rect = pygame.Rect(
                xpos,
                self.height-self.buttonheight-self.padding,
                self.bbarheight,
                self.buttonheight
            )

            self.menu.add(Button(font, colors, button_delete_rect, "Delete",
                                 "delete_bar", id=4))

            # Name label
            font["size"] = int(self.padding*1.5)
            self.bartitles.add(Title(
                font,
                colors,
                (xpos, self.height-self.bbarheight),
                "Name:")
            )

            # Value label
            self.bartitles.add(Title(
                font,
                colors,
                (xpos, self.height-self.bbarheight+font["size"]+2),
                "Value:")
            )

            # Name
            self.bartitles.add(Title(
                font,
                colors_text,
                (xpos+self.padding*6,  self.height-self.bbarheight),
                bar_selected.caption)
            )

            # Value
            self.bartitles.add(Title(
                font,
                colors_text,
                (
                    xpos+self.padding*6,
                    self.height-self.bbarheight+font["size"]+2
                ),
                str(bar_selected.value))
            )

    def save_image(self):
        # deselect any selected bars for the image saving
        for bar in self.bars:
            if bar.selected:
                bar.deselect()
                bar.update()
        self.draw()

        # get current date and time to use as filename
        date = datetime.datetime.now().strftime("%Y-%m-%d %H-%M-%S")

        # only save the barchart, not the GUI
        surface = self.screen.subsurface(pygame.Rect(
            0,
            0,
            self.width,
            self.height-self.bbarheight)
        )
        filename = str(date)+".png"
        pygame.image.save(surface, filename)
        print "Saved image as "+filename

    def delete_bar(self):
        x = 0

        for bar in self.bars:
            if bar.selected:
                # get bar position so other bars can be relocated
                x = bar.rect.x
                self.bars.remove(bar)

                # move bars to fill the gap left by the deleted bar
                for bar in self.bars:
                    if bar.rect.x > x:
                        bar.move(-bar.rect.width-self.padding)
                break

                # update the barchart and the GUI
                self.bar_menu()
                self.main_menu()

    def main_menu(self):
        # clear the GUI
        self.menu.empty()
        self.titles.empty()

        font = {"family": "Arial", "size": int(self.width/80*2)}

        colors = {
            "background": (225, 225, 225),
            "selected": (250, 250, 200),
            "hover": (200, 250, 200),
            "error": (250, 200, 200),
            "text": (75, 75, 75)
        }

        xpos = self.padding
        input_caption_rect = pygame.Rect(
            xpos,
            self.height-self.buttonheight-self.padding,
            self.height/8*3,
            self.buttonheight
        )
        input_caption = InputBox(font, colors, input_caption_rect, self.fps, 0)

        xpos += self.height/8*3+self.padding
        input_value_rect = pygame.Rect(
            xpos,
            self.height-self.buttonheight-self.padding,
            font["size"]*3,
            self.buttonheight
        )
        input_value = InputBox(font, colors, input_value_rect, self.fps, 1)

        button_colors = {
            "background": (205, 205, 205),
            "selected": (200, 200, 150),
            "hover": (150, 200, 150),
            "error": (200, 150, 150),
            "text": (25, 25, 25)
        }

        xpos += font["size"]*3+self.padding
        button_submit_rect = pygame.Rect(
            xpos,
            self.height-self.buttonheight-self.padding,
            font["size"]*3,
            self.buttonheight
        )
        button_submit = Button(font, button_colors, button_submit_rect,
                               "Add", "submit_values")

        xpos += font["size"]*3+self.padding
        button_save_rect = pygame.Rect(
            xpos,
            self.height-self.buttonheight-self.padding,
            self.bbarheight,
            self.buttonheight
        )
        button_save = Button(font, button_colors, button_save_rect,
                             "Save image", "save_image", id=3)

        self.menu.add(input_caption)
        self.menu.add(input_value)
        self.menu.add(button_submit)
        self.menu.add(button_save)

        self.titles.add(Title(
            font, colors,
            (self.padding, self.width-self.bbarheight+self.padding),
            "Caption:")
        )
        self.titles.add(Title(
            font, colors,
            (
                self.height/8*3+self.padding*2,
                self.width-self.bbarheight+self.padding
            ),
            "Value:")
        )

    def submit_values(self):
        caption = ""
        value = 0

        # get data from input boxes
        for button in self.menu:

            # input box id 0 is the caption box
            if button.id == 0:
                # so the data is a string
                caption = str(button.data)

            # input box id 1 is the value box
            elif button.id == 1:

                # so the data should be int
                try:
                    value = int(button.data)
                except:
                    print "Incorrect input!"

        # if either data field is empty or invalid
        if caption == "" or value < 1:
            for button in self.menu:
                if button.id == 2:

                    # flash the "Add" button red
                    button.throw_error()

        else:
            maxvalue = value

            if self.bars:
                # get greatest current value of a bar
                maxvalue = max(bar.value for bar in self.bars)
                # if new value is bigger than current maxvalue
                if value > maxvalue:
                    # set it as new maxvalue
                    maxvalue = value
                    for bar in self.bars:
                        # and scale all bars according to it
                        bar.set_size(maxvalue)

            barwidth = self.buttonheight+self.padding*3
            bars = len(self.bars)*barwidth
            oldpadding = len(self.bars)*self.padding
            # other bar paddings and bars, padding left
            x = oldpadding+bars+self.padding

            # don't let the user add more bars if end of window is reached
            if x+self.buttonheight+self.padding*3 > self.width:
                for button in self.menu:
                    if button.id == 2:
                        button.throw_error()
            else:
                y = self.height-self.bbarheight-self.buttonheight
                self.bars.add(Bar(
                    caption, value, maxvalue,
                    self.maxheight, x,
                    y-self.padding*2, barwidth)
                )

    # pass a string to this function; function with the same name as the
    # string is executed
    def perform_action(self, name):
        function = getattr(self, name)
        if function() is False:
            return False

    def draw(self):
        self.screen.blit(self.background, (0, 0))
        self.screen.blit(self.bottombar, (0, self.height-self.bbarheight))
        self.menu.draw(self.screen)
        self.titles.draw(self.screen)
        self.bars.draw(self.screen)
        self.bartitles.draw(self.screen)
        pygame.display.update()


class Mouse(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.rect = pygame.Rect(0, 0, 1, 1)

    def move(self, pos):
        self.rect.x, self.rect.y = pos

if __name__ == "__main__":
    app = BarchartApp()
    app.main()
