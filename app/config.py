import flet as ft
import os

# Centralize visual settings and app constants here to make customization easy.

BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
DB_DIR = os.path.join(BASE_DIR, "bd")
DB_PATH = os.path.join(DB_DIR, "academia.db")
os.makedirs(DB_DIR, exist_ok=True)


# Paleta de cores do Tema Gym
class GymColors:
    # Cores principais - Tema Claro
    LIGHT_PRIMARY = "#FF6B35"  # Laranja vibrante (energia)
    LIGHT_SECONDARY = "#004E89"  # Azul escuro (confiança)
    LIGHT_ACCENT = "#FFD700"  # Dourado (conquista)
    LIGHT_BACKGROUND = "#F7F7F7"  # Cinza muito claro
    LIGHT_SURFACE = "#FFFFFF"  # Branco
    LIGHT_ERROR = "#D32F2F"  # Vermelho
    LIGHT_ON_PRIMARY = "#FFFFFF"  # Texto sobre primário
    LIGHT_ON_BACKGROUND = "#212121"  # Texto sobre fundo
    LIGHT_ON_SURFACE = "#212121"  # Texto sobre superfície

    # Cores principais - Tema Escuro
    DARK_PRIMARY = "#FF8C42"  # Laranja mais suave
    DARK_SECONDARY = "#1A8FE3"  # Azul médio
    DARK_ACCENT = "#FFC107"  # Amarelo dourado
    DARK_BACKGROUND = "#121212"  # Preto suave
    DARK_SURFACE = "#1E1E1E"  # Cinza muito escuro
    DARK_ERROR = "#CF6679"  # Vermelho suave
    DARK_ON_PRIMARY = "#000000"  # Texto sobre primário
    DARK_ON_BACKGROUND = "#E0E0E0"  # Texto sobre fundo
    DARK_ON_SURFACE = "#E0E0E0"  # Texto sobre superfície


class GymTheme:
    @staticmethod
    def light_theme():
        """Retorna o tema claro do Gym"""
        return ft.Theme(
            color_scheme_seed=GymColors.LIGHT_PRIMARY,
            color_scheme=ft.ColorScheme(
                primary=GymColors.LIGHT_PRIMARY,
                on_primary=GymColors.LIGHT_ON_PRIMARY,
                secondary=GymColors.LIGHT_SECONDARY,
                on_secondary=GymColors.LIGHT_ON_PRIMARY,
                error=GymColors.LIGHT_ERROR,
                on_error=GymColors.LIGHT_ON_PRIMARY,
                background=GymColors.LIGHT_BACKGROUND,
                on_background=GymColors.LIGHT_ON_BACKGROUND,
                surface=GymColors.LIGHT_SURFACE,
                on_surface=GymColors.LIGHT_ON_SURFACE,
            ),
            font_family="Roboto",
        )

    @staticmethod
    def dark_theme():
        """Retorna o tema escuro do Gym"""
        return ft.Theme(
            color_scheme_seed=GymColors.DARK_PRIMARY,
            color_scheme=ft.ColorScheme(
                primary=GymColors.DARK_PRIMARY,
                on_primary=GymColors.DARK_ON_PRIMARY,
                secondary=GymColors.DARK_SECONDARY,
                on_secondary=GymColors.DARK_ON_PRIMARY,
                error=GymColors.DARK_ERROR,
                on_error=GymColors.DARK_ON_PRIMARY,
                background=GymColors.DARK_BACKGROUND,
                on_background=GymColors.DARK_ON_BACKGROUND,
                surface=GymColors.DARK_SURFACE,
                on_surface=GymColors.DARK_ON_SURFACE,
            ),
            font_family="Roboto",
        )


class Theme:
    # Window
    WINDOW_WIDTH = 980
    WINDOW_HEIGHT = 700
    THEME_MODE = ft.ThemeMode.DARK

    # Colors & palette (Gym)
    PRIMARY = ft.Colors.BLUE_600
    SECONDARY = ft.Colors.GREEN_600
    ACCENT = ft.Colors.ORANGE_600
    DANGER = ft.Colors.RED_600
    INFO = ft.Colors.BLUE_GREY_600

    TEXT_TITLE = ft.Colors.BLUE_400
    TEXT_SECTION = ft.Colors.ORANGE_400

    # Background gradient (top-left -> bottom-right)
    BG_GRADIENT = ["#0b1220", "#111827", "#1f2937"]

    # App Themes (Light/Dark) for Gym
    @staticmethod
    def light_theme() -> ft.Theme:
        # Seeded palette using PRIMARY to keep identity
        return GymTheme.light_theme()

    @staticmethod
    def dark_theme() -> ft.Theme:
        return GymTheme.dark_theme()
