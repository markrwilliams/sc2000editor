#!/usr/bin/env python

import gtk
import gtk.glade
import cairo
import city

class Editor(object):
    def __init__(self):
        glade_file = 'simple.glade'
        builder = gtk.Builder()
        builder.add_from_file(glade_file)
        builder.connect_signals(self)

        self.window =  builder.get_object('window1')
        self.open_dialog = builder.get_object('opendialog')

        self.city_name = builder.get_object('city_name_field')
        self.money = builder.get_object('money_field')
        self.year_started = builder.get_object('year_founded_field')
        self.national_pop = builder.get_object('nat_pop_field')
        self.days_elapsed = builder.get_object('days_elapsed_field')

        self.status_bar = builder.get_object('statusbar1')
        self.error_dialog = builder.get_object('errordialog')
        self.error_message = builder.get_object('errormessage')

        self.map_drawable = builder.get_object('drawingarea1')
        self.map_drawable.show()
        self.map_scale = 5
        self.map = None
        self.map_action = 'Raise'

        self.city = None

    def raise_error(self, error_message):
        self.error_message.set_label(error_message)
        self.error_dialog.run()
        self.error_dialog.hide()

    def add_statusbar_message(self, context, message):
        cid = self.status_bar.get_context_id(context)
        self.status_bar.push(cid, message)

    def pop_statusbar_message(self, context):
        cid = self.status_bar.get_context_id(context)
        self.status_bar.pop(cid)

    def draw_map(self, widget, area):
        if not self.city:
            return True
        
        style = widget.get_style()
        cr = widget.window.cairo_create()
        cr.rectangle(*area)
        cr.clip()
        
        if not self.map:
            self.cr, self.map = self.setup_map(cr)

        cr.scale(self.map_scale, self.map_scale)
        cr.set_source_surface(self.map, 0, 0)
        cr.paint()
        return True
        
    def drawable_expose_event(self, widget, event):
        return self.draw_map(widget, event.area)

    def open_dialog_show(self, widget):
        filename = None

        response = self.open_dialog.run()
        if response == 1:
            self.open_dialog.hide()
            filename = self.open_dialog.get_filename()
            try:
                self.city = city.City(filename)
                _, _, short_name = filename.rpartition('/')
                self.add_statusbar_message('openfile',
                                           'Current city: %s' % short_name)
                self.populate_basic_fields(self.city)
                self.map = None
            except IOError as error:
                message, = error.args
                self.raise_error(message)

        self.open_dialog.hide()

        return filename

    def populate_basic_fields(self, city):
        if not city.cityname:
            self.city_name.set_sensitive(False)
            self.city_name.set_text('None')
        else:
            self.city_name.set_sensitive(True)
            self.city_name.set_text(city.cityname)

        self.money.set_text(str(city.money))
        self.national_pop.set_text(str(city.national_pop))
        self.days_elapsed.set_text(str(city.days_elapsed))
        self.year_started.set_text(str(city.year_started))

    def money_validate(self, widget, event):
        val = widget.get_text()
        if val and self.city:
            if not val.isdigit() or int(val) > city.MAX_MONEY:
                self.raise_error('Money field must be an whole number less than %d!' %
                                 city.MAX_MONEY)

    def on_save(self, *args):
        self.city.cityname = self.city_name.get_text()
        self.city.money = int(self.money.get_text())
        self.city.national_pop = int(self.national_pop.get_text())
        self.city.days_elapsed = int(self.days_elapsed.get_text())
        self.city.year_started = int(self.year_started.get_text())
        self.add_statusbar_message('savecity',
                                   'Saving...')
        self.city.save()
        self.pop_statusbar_message('savecity')
        return True
    
    def on_map_option_change(self, button):
        if button.get_active():
            self.map_action = button.get_label()
        return True
    
    def setup_map(self, window):
        map = window.get_target().create_similar(cairo.CONTENT_COLOR, 128, 128)
        cr = cairo.Context(map)
        for y, row in enumerate(xrange(0, 128)):
            for x, c in enumerate(xrange(0, 128)):
                t = self.city.map[y][x]
                h = t.height / 15.
                if t.type in city.WATER_TILES:
                    cr.set_source_rgb(0, 0, h)
                else:
                    cr.set_source_rgb(h, h * .75, 0)
                cr.rectangle(x, y, 1, 1)
                cr.fill()
        return cr, map
        
    def on_map_button_press(self, widget, e):
        x, y = int(e.x / self.map_scale), int(e.y / self.map_scale)
        if 0 < x < 128 and 0 < y < 128:
            self.alter_map(x, y, self.map_action)
            self.draw_map(self.map_drawable, (0, 0, 128 * 5, 128 * 5))
        
    
    def alter_map(self, x, y, action):
        {'Raise': self.raise_tile}[action](x, y)

    def raise_tile(self, x, y):
        t = self.city.map[y][x]

        if t.type in city.WATER_TILES:
            return
        t.type = 0

        self.city.map[y + 1][x].type = 1
        self.city.map[y][x + 1].type = 2
        self.city.map[y][x - 1].type = 4
        self.city.map[y - 1][x].type = 3
        
        # self.city.map[y + 1][x + 1] = 5
        # self.city.map[y - 1][x + 1] = 9
        t.height += 1
        h = t.height / 15.
        self.cr.set_source_rgb(h, h * .75, 0)
        self.cr.rectangle(x, y, 1, 1)
        self.cr.fill()
        
        print x, y
        
        
    def on_quit(self, *args):
        gtk.main_quit()


if __name__ == '__main__':
    app = Editor()
    app.window.show()
    gtk.main()
    
