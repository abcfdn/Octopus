# -*- encoding: UTF-8 -*-

import os
import sys

from PIL import ImageFont, ImageDraw, Image, ImageOps
import numpy as np

FONT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fonts')


class ImageComposer:
    def __init__(self, pieces):
        self.imgs = [p.get_img() for p in pieces]

    def vstack(self):
        stacked = np.vstack((np.asarray(img) for img in self.imgs))
        self.comb = Image.fromarray(stacked)

    def zstack(self, start_point):
        if len(self.imgs) != 2:
            print("Only two imgs are supported in zstack")
        [background, foreground] = self.imgs
        background.paste(foreground, start_point, foreground)
        self.comb = background

    def to_img_piece(self):
        return ImagePiece(self.comb)

    def save(self, filename):
        self.comb.save(filename)


class ImagePiece:
    def __init__(self, img):
        self.img = img

    @classmethod
    def from_file(cls, filename):
        return cls(Image.open(filename))

    def get_font(self, font_setting):
        font_path = os.path.join(FONT_PATH, '%s.ttf' % font_setting['type'])
        return ImageFont.truetype(font_path, font_setting['size'])

    def word_size(self, font, word):
        width = 0
        for c in word:
            w, h = font.getsize(c)
            width += w
        return width, h

    def draw_text(self, text, settings):
        [x_pos, y_pos] = settings['start']
        x_max = settings['x_max']
        font = self.get_font(settings['font'])
        gap = settings['gap']
        fill = tuple(settings['fill'])

        draw = ImageDraw.Draw(self.img)
        for word in text.split(' '):
            ww, wh = self.word_size(font, word)
            if x_pos + ww >= x_max:
                x_pos = settings['start'][0]
                y_pos += wh

            for c in (word + ' '):
                if c == '\n' or c == '\r':
                    x_pos = settings['start'][0]
                    y_pos += wh
                    continue

                w, h = font.getsize(c)
                draw.text((x_pos, y_pos), c, font=font, fill=fill)
                x_pos += (w + gap)

    def to_circle_thumbnail(self, size):
        bigsize = (size[0] * 3, size[1] * 3)
        mask = Image.new('L', bigsize, 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0) + bigsize, fill=255)
        mask = mask.resize(size, Image.ANTIALIAS)

        self.img = self.img.resize(size, Image.ANTIALIAS)
        self.img = ImageOps.fit(
            self.img, size, method=Image.ANTIALIAS, centering=(0.5, 0.5))
        self.img.putalpha(mask)

    def get_img(self):
        return self.img

    def save(self, filename):
        self.img.save(filename)
