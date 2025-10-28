import flet as ft
import os

# Centralize visual settings and app constants here to make customization easy.

BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
DB_DIR = os.path.join(BASE_DIR, "bd")
DB_PATH = os.path.join(DB_DIR, "academia.db")
os.makedirs(DB_DIR, exist_ok=True)

class Theme:
    # Window
    WINDOW_WIDTH = 980
    WINDOW_HEIGHT = 700
    THEME_MODE = ft.ThemeMode.DARK

    # Colors & palette
    PRIMARY = ft.Colors.BLUE_600
    SECONDARY = ft.Colors.GREEN_600
    ACCENT = ft.Colors.ORANGE_600
    DANGER = ft.Colors.RED_600
    INFO = ft.Colors.BLUE_GREY_600

    TEXT_TITLE = ft.Colors.BLUE_400
    TEXT_SECTION = ft.Colors.ORANGE_400

    # Background gradient (top-left -> bottom-right)
    BG_GRADIENT = ["#0b1220", "#111827", "#1f2937"]
