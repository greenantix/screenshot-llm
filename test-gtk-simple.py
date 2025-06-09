#!/usr/bin/env python3
"""Simple GTK test"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

class TestWindow(Gtk.Window):
    def __init__(self):
        super().__init__(title="Test GTK Window")
        self.set_default_size(400, 300)
        
        # Add a simple label
        label = Gtk.Label(label="GTK Test Window - Working!")
        self.add(label)
        
        self.connect("destroy", Gtk.main_quit)

def main():
    window = TestWindow()
    window.show_all()
    Gtk.main()

if __name__ == "__main__":
    main()