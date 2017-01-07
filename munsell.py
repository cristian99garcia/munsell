# Copyright (c) 2014,2015 Walter Bender
#
# This program is free software you can redistribute it and/or
# modify it under the terms of the The GNU Affero General Public
# License as published by the Free Software Foundation either
# version 3 of the License, or (at your option) any later version.
#
# You should have received a copy of the GNU Affero General Public
# License along with this library if not, write to the Free Software
# Foundation, 51 Franklin Street, Suite 500 Boston, MA 02110-1335 USA
#
# Munsell data derived from CPAN Color::Model::Munsell
# http:#search.cpan.org/~tonodera/Color-Model-Munsell-0.02/
# which is a vast improvement over the Munsell Perl module 
# written by Walter Bender and Jon Orwant back in the day.

import math

from data import MUNSELL
from data import COLORS40

import gi
gi.require_version("Gtk", "3.0")

from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GObject


def hex_to_cairo(hex_code):
    if hex_code.startswith("#"):
        hex_code = hex_code[1:]

    r = int(hex_code[0:2], 16)
    g = int(hex_code[2:4], 16)
    b = int(hex_code[4:6], 16)

    return (r / 255.0, g / 255.0, b / 255.0)


class MunsellColorItem(Gtk.DrawingArea):

    __gsignals__ = {
        "clicked": (GObject.SIGNAL_RUN_LAST, None, []),
    }

    def __init__(self, color, index):
        Gtk.DrawingArea.__init__(self)

        self.x = 0
        self.y = 0
        self.color = color
        self.index = index
        self.cairo_color = hex_to_cairo(color)
        self.mouse_over = False

        self.add_events(Gdk.EventMask.ENTER_NOTIFY_MASK |
                        Gdk.EventMask.LEAVE_NOTIFY_MASK |
                        Gdk.EventMask.BUTTON_PRESS_MASK)

        self.connect("draw", self.__draw_cb)
        self.connect("enter-notify-event", self.__enter_cb)
        self.connect("leave-notify-event", self.__leave_cb)
        self.connect("button-press-event", self.__press_cb)

        self.show()

    def __draw_cb(self, widget, context):
        alloc = self.get_allocation()

        context.set_source_rgb(*self.cairo_color)
        context.rectangle(0, 0, alloc.width, alloc.height)
        context.fill()

        if self.mouse_over:
            color = (1, 1, 1)
            r, g, b = self.cairo_color
            if r >= 0.8 and g >= 0.8 and b >= 0.8:
                color = (0, 0, 0)

            context.set_line_width(4)
            context.set_source_rgb(*color)
            context.rectangle(0, 0, alloc.width, alloc.height)
            context.stroke()

    def __enter_cb(self, button, event):
        self.set_mouse_over(True)

    def __leave_cb(self, button, event):
        self.set_mouse_over(False)

    def __press_cb(self, button, event):
        if event.button == 1:
            self.emit("clicked")

    def set_mouse_over(self, over):
        self.mouse_over = over
        self.queue_draw()


class ColorWheel(Gtk.Layout):

    __gsignals__ = {
        "selected": (GObject.SIGNAL_RUN_LAST, None, [int]),
    }

    def __init__(self):
        Gtk.Layout.__init__(self)

        self.radius = 0
        self.color_size = 0

        self.set_size_request(200, 200)
        self._make_items()

        self.connect("draw", self.__draw_cb)

    def __draw_cb(self, widget, context):
        alloc = self.get_allocation()
        width = alloc.width
        height = alloc.height
        self.color_size = min(width, height) / 20
        self.radius = min(width, height) / 2 - self.color_size / 2

        for item in self.items:
            item.set_size_request(self.color_size, self.color_size)
            angle = item.index * (2 * math.pi / len(self.items)) - math.pi / 2.0
            item.x = self.radius * math.cos(angle) + width / 2.0 - self.color_size / 2
            item.y = self.radius * math.sin(angle) + height / 2.0 - self.color_size / 2

            self.move(item, item.x, item.y)

    def __item_clicked_cb(self, item):
        self.emit("selected", item.index)

    def _make_items(self):
        self.items = []
        index = 0
        for data in COLORS40:
            item = MunsellColorItem(data[2], index)
            item.set_size_request(self.color_size, self.color_size)
            item.connect("clicked", self.__item_clicked_cb)
            self.put(item, item.x, item.y)

            self.items.append(item)
            index += 1

        self.show_all()


class HueGrid(Gtk.Grid):

    __gsignals__ = {
        "selected": (GObject.SIGNAL_RUN_LAST, None, [str]),
    }

    def __init__(self):
        Gtk.Grid.__init__(self)

        self.items = []
        self.palette = 0

        self.set_hexpand(False)
        self.set_vexpand(False)
        self.add_events(Gdk.EventMask.POINTER_MOTION_MASK)
        self.set_color(0)

    def __item_clicked_cb(self, item):
        start = self.palette * 165
        end = (self.palette + 1) * 165
        self.emit("selected", MUNSELL[start:end][item.index])

    def set_color(self, color_index):
        self.clear()
        self.palette = color_index

        start = 165 * color_index
        end = 165 * (color_index + 1)
        colors = MUNSELL[start:end]

        x = 0
        y = 0
        idx = 0
        for color in colors:
            item = MunsellColorItem(color, idx)
            item.set_size_request(20, 20)
            item.set_hexpand(True)
            item.set_vexpand(True)
            item.connect("clicked", self.__item_clicked_cb)
            self.attach(item, x, y, 1, 1)

            self.items.append(item)

            x += 1
            if x >= 15:
                x = 0
                y += 1

            idx += 1

        self.show_all()

    def clear(self):
        while self.items != []:
            item = self.items[0]
            self.remove(item)
            self.items.remove(item)
            del item


class MunsellColorPicker(Gtk.Grid):

    __gsignals__ = {
        "selected": (GObject.SIGNAL_RUN_LAST, None, [str]),
    }

    def __init__(self):
        Gtk.Grid.__init__(self)

        self.set_border_width(2)
        self.set_column_spacing(5)

        self.wheel = ColorWheel()
        self.wheel.connect("selected", self.__wheel_selected_cb)
        self.attach(self.wheel, 0, 0, 1, 1)

        self.grid = HueGrid()
        self.grid.connect("selected", self.__color_selected_cb)
        self.attach(self.grid, 1, 0, 1, 1)

    def __wheel_selected_cb(self, widget, idx):
        self.grid.set_color(idx)

    def __color_selected_cb(self, widget, color):
        self.emit("selected", color)


if __name__ == "__main__":
    def color_selected(picker, color, clipboard):
        clipboard.set_text(color, -1)

    clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)

    win = Gtk.Window()
    win.set_resizable(False)
    win.set_title("Munsell color picker")
    win.connect("destroy", Gtk.main_quit)

    picker = MunsellColorPicker()
    picker.connect("selected", color_selected, clipboard)
    win.add(picker)

    win.show_all()
    Gtk.main()
