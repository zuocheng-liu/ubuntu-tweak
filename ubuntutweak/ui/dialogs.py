#!/usr/bin/python

# Ubuntu Tweak - PyGTK based desktop configuration tool
#
# Copyright (C) 2007-2008 TualatriX <tualatrix@gmail.com>
#
# Ubuntu Tweak is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# Ubuntu Tweak is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ubuntu Tweak; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA

import gtk
import vte
import thread
import gobject
import pango

class BusyDialog(gtk.Dialog):
    def __init__(self, parent=None):
        gtk.Dialog.__init__(self, parent=parent)

        if parent:
            self.parent_window = parent
        else:
            self.parent_window = None

    def set_busy(self):
        if self.parent_window:
            self.parent_window.window.set_cursor(gtk.gdk.Cursor(gtk.gdk.WATCH))
            self.parent_window.set_sensitive(False)

    def unset_busy(self):
        if self.parent_window:
            self.parent_window.window.set_cursor(None)
            self.parent_window.set_sensitive(True)

    def run(self):
        self.set_busy()
        return super(BusyDialog, self).run()

    def destroy(self):
        self.unset_busy()
        super(BusyDialog, self).destroy()

class ProcessDialog(BusyDialog):
    def __init__(self, parent):
        super(ProcessDialog, self).__init__(parent=parent)

        vbox = gtk.VBox(False, 5)
        self.vbox.add(vbox)
        self.set_border_width(8)
        self.set_title('')
        self.set_has_separator(False)
        self.set_resizable(False)

        self.__label = gtk.Label()
        self.__label.set_alignment(0, 0.5)
        vbox.pack_start(self.__label, False, False, 0)

        self.__progressbar = gtk.ProgressBar()
        self.__progressbar.set_ellipsize(pango.ELLIPSIZE_END)
        self.__progressbar.set_size_request(320, -1)
        vbox.pack_start(self.__progressbar, False, False, 0)

        self.set_position(gtk.WIN_POS_CENTER_ON_PARENT)
        self.show_all()

    def run(self):
        thread.start_new_thread(self.process_data, ())
        gobject.timeout_add(100, self.on_timeout)
        super(ProcessDialog, self).run()

    def pulse(self):
        self.__progressbar.pulse()

    def set_dialog_lable(self, text):
        self.__label.set_markup('<b><big>%s</big></b>' % text)

    def set_progress_text(self, text):
        self.__progressbar.set_text(text)

    def process_data(self):
        return NotImplemented

    def on_timeout(self):
        return NotImplemented

class BaseMessageDialog(gtk.MessageDialog):
    def __init__(self, type, buttons):
        gtk.MessageDialog.__init__(self, None, gtk.DIALOG_MODAL, type, buttons)

    def set_title(self, title):
        self.set_markup('<big><b>%s</b></big>' % title)

    def set_content(self, message, title):
        if title:
            self.set_title(title)
            self.format_secondary_markup(message)
        else:
            self.set_markup(message)

    def add_widget(self, widget):
        '''Add a widget to serve more actions, such as an Entry to get text input'''
        vbox = self.get_content_area()
        hbox = gtk.HBox()
        vbox.pack_start(hbox, False, False, 0)
        hbox.pack_end(widget, True, True, 0)

        hbox.show_all()

    def add_widget_with_scrolledwindow(self, widget, width=-1, height=200):
        '''Add a widget with a scrolled window, it is often used to add a TreeView'''
        vbox = self.get_content_area()

        sw = gtk.ScrolledWindow()
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        sw.set_size_request(width, height)
        vbox.pack_start(sw, False, False, 0)
        sw.add(widget)

        vbox.show_all()

    def launch(self):
        self.run()
        self.destroy()

    def add_option_button(self, button):
        '''Add an option button to the left. It will not grab the default response.'''
        vbox = self.get_child()
        hbuttonbox = vbox.get_children()[-1]

        hbox = gtk.HBox(False, 12)
        vbox.pack_start(hbox, False, False, 0)
        vbox.remove(hbuttonbox)

        new_hbuttonbox = gtk.HButtonBox()
        new_hbuttonbox.set_layout(gtk.BUTTONBOX_START)
        new_hbuttonbox.pack_start(button)

        hbox.pack_start(new_hbuttonbox)
        hbox.pack_start(hbuttonbox)

        hbuttonbox.get_children()[-1].grab_focus()

        vbox.show_all()

class InfoDialog(BaseMessageDialog):
    def __init__(self, message, type = gtk.MESSAGE_INFO, buttons = gtk.BUTTONS_OK, title = None):
        BaseMessageDialog.__init__(self, type, buttons)
        self.set_content(message, title)

class QuestionDialog(BaseMessageDialog):
    def __init__(self, message, type = gtk.MESSAGE_QUESTION, buttons = gtk.BUTTONS_YES_NO, title = None):
        BaseMessageDialog.__init__(self, type, buttons)
        self.set_content(message, title)

class ErrorDialog(BaseMessageDialog):
    def __init__(self, message, type = gtk.MESSAGE_ERROR, buttons = gtk.BUTTONS_OK, title = None):
        BaseMessageDialog.__init__(self, type, buttons)
        self.set_content(message, title)

class WarningDialog(BaseMessageDialog):
    def __init__(self, message, type = gtk.MESSAGE_WARNING, buttons = gtk.BUTTONS_YES_NO, title = None):
        BaseMessageDialog.__init__(self, type, buttons)
        self.set_content(message, title)

class AuthenticateFailDialog(ErrorDialog):
    def __init__(self):
        ErrorDialog.__init__(self, 
                _('An unexpected error has occurred.'), 
                title = _('Could not authenticate'))

class ServerErrorDialog(ErrorDialog):
    def __init__(self):
        ErrorDialog.__init__(self,
                _('You need to restart your computer.'), 
                title = _("Service hasn't initialized yet"))

class SmartTerminal(vte.Terminal):
    def insert(self, string):
        column_count = self.get_column_count ()
        column, row = self.get_cursor_position()
        if column == 0:
            column = column_count
        if column != column_count:
            self.feed(' ' * (column_count - column))
        space_length = column_count - len(string)
        string = string + ' ' * space_length
        self.feed(string)

class TerminalDialog(ProcessDialog):
    def __init__(self, parent):
        super(TerminalDialog, self).__init__(parent=parent)

        self.set_position(gtk.WIN_POS_CENTER_ALWAYS)
        self.expendar = gtk.Expander()
        self.expendar.set_spacing(6)
        self.expendar.set_label(_('Details'))
        self.vbox.pack_start(self.expendar, False, False, 6)

        self.terminal = SmartTerminal()
        self.terminal.set_size_request(562, 362)
        self.expendar.add(self.terminal)

        self.vbox.show_all()
