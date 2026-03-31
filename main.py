#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Книги в аудио - Графическое приложение для конвертации книг в аудиофайлы
С использованием XTTS
"""

import tkinter as tk
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gui.main_window import MainWindow

def main():
    root = tk.Tk()
    app = MainWindow(root)
    root.mainloop()

if __name__ == "__main__":
    main()