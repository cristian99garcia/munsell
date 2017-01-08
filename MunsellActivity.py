#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2014-2016, Cristian García <cristian99garcia@gmail.com>
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 3 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place - Suite 330,
# Boston, MA 02111-1307, USA.

import os
import dbus

from munsell import MunsellColorPicker

import gi
gi.require_version("Gtk", "3.0")

from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import Gio
from gi.repository import GdkPixbuf

from sugar3 import profile
from sugar3.activity import activity
from sugar3.graphics.toolbarbox import ToolbarBox
from sugar3.activity.widgets import ActivityToolbarButton
from sugar3.activity.widgets import StopButton
from sugar3.graphics.toolbutton import ToolButton
from sugar3.graphics.alert import ConfirmationAlert
from sugar3.graphics.alert import NotifyAlert

from gettext import gettext as _


class MunsellActivity(activity.Activity):

    def __init__(self, handle):
        activity.Activity.__init__(self, handle)

        if profile.get_color() is not None:
            self.colors = profile.get_color().to_string().split(",")
        else:
            self.colors = ["#A0FFA0", "#FF8080"]

        self.make_toolbar()

        scroll = Gtk.ScrolledWindow()
        self.set_canvas(scroll)

        self.vbox = Gtk.VBox()
        scroll.add(self.vbox)

        self.image = Gtk.Image()
        self.vbox.pack_start(self.image, True, True, 0)

        hbox = Gtk.HBox()
        hbox.set_border_width(40)
        self.vbox.pack_end(hbox, False, False, 0)

        self.picker1 = MunsellColorPicker()
        self.picker1.connect("selected", self._selected_cb, 0)
        hbox.pack_start(self.picker1, True, True, 0)

        self.picker2 = MunsellColorPicker()
        self.picker2.connect("selected", self._selected_cb, 1)
        hbox.pack_start(self.picker2, True, True, 0)

        self.make_pixbuf()
        self.show_all()

    def make_toolbar(self):
        toolbarbox = ToolbarBox()
        self.set_toolbar_box(toolbarbox)

        toolbar = toolbarbox.toolbar

        button = ActivityToolbarButton(self)
        toolbar.insert(button, -1)

        separator = Gtk.SeparatorToolItem()
        separator.props.draw = False
        separator.set_expand(True)
        toolbar.insert(separator, -1)

        button = ToolButton("save-colors")
        button.set_tooltip(_("Save colors"))
        button.connect("clicked", self._save_colors)
        toolbar.insert(button, -1)

        button = StopButton(self)
        toolbar.insert(button, -1)

    def _selected_cb(self, picker, color, idx):
        self.colors[idx] = color
        self.make_pixbuf()

    def _save_colors(self, widget):
        alert = ConfirmationAlert()
        alert.props.title = _("Saving colors")
        alert.props.msg = _("Do you want to save these colors?")
        alert.connect('response', self._alert_response_cb)
        self.add_alert(alert)
        alert.show_all()

    def _alert_response_cb(self, alert, response_id):
        if response_id == Gtk.ResponseType.OK:
            self.remove_alert(alert)
            self._confirm_save()

        elif response_id == Gtk.ResponseType.CANCEL:
            self.remove_alert(alert)

    def _notify_response_cb(self, alert, response_id):
        self.remove_alert(alert)

    def _confirm_save(self):
        color1 = self.colors[0].upper()
        color2 = self.colors[1].upper()

        settings = Gio.Settings("org.sugarlabs.user")
        settings.set_string("color", "%s,%s" % (color1, color2))

        alert = NotifyAlert()
        alert.props.title = _('Saving colors')
        alert.props.msg = _('A restart is required before your new colors will appear.')
        alert.connect("response", self._notify_response_cb)
        self.add_alert(alert)
        alert.show_all()

    def make_pixbuf(self):
        color1, color2 = self.colors

        img_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "xo-icon.svg")

        with open(img_path, "r") as img_file:
            svg = img_file.read()
            svg = svg.replace('#000000', '%s' % color1)
            svg = svg.replace('#FFFFFF', '%s' % color2)

        pl = GdkPixbuf.PixbufLoader.new_with_type("svg")
        pl.write(svg)
        pl.close()

        self.vbox.remove(self.image)
        del self.image

        self.image = Gtk.Image.new_from_pixbuf(pl.get_pixbuf())
        self.vbox.pack_start(self.image, True, True, 0)

        self.show_all()
