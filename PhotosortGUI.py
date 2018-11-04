#!/usr/bin/env python
# -*- coding: utf-8 -*-
from ren2date_class import Ren2Date 
import kivy

#kivy.require('1.0.6') # replace with your current kivy version !
from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput


class GUI(GridLayout):

    def __init__(self, **kwargs):
        super(GUI, self).__init__(**kwargs)
        r2d = Ren2Date()
        r2d.open_conf('PetersTelefon')
        folder_list = sorted(r2d.conf.items()[1:])
        
        folder_text = ""
        for item in folder_list:
            item = "%s: %s" % item
            folder_text += ''.join(item) + "\n"
            
        self.cols = 2
        self.add_widget(Label(text="Folders"))
        self.add_widget(Label(text=folder_text))



class PhotosortGUI(App):
    def build(self):
        return GUI()


if __name__ == '__main__':
    ps_gui = PhotosortGUI()
    PhotosortGUI().run()
