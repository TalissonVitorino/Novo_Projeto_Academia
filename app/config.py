import flet as ft
import os

# Centralize visual settings and app constants here to make customization easy.

BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
DB_DIR = os.path.join(BASE_DIR, "bd")
DB_PATH = os.path.join(DB_DIR, "academia.db")
os.makedirs(DB_DIR, exist_ok=True)


# Paleta de cores do Tema Gym
class GymColors:
    # ==========================
    # Cores principais - Tema Claro (Azul claro + Preto)
    # ==========================
    LIGHT_PRIMARY = "#3B82F6"       # Azul principal
    LIGHT_SECONDARY = "#0EA5E9"     # Azul/ciã secundário
    LIGHT_ACCENT = "#F97316"        # Laranja de destaque
    LIGHT_BACKGROUND = "#F3F4F6"    # Cinza bem claro (quase branco)
    LIGHT_SURFACE = "#FFFFFF"       # Branco
    LIGHT_ERROR = "#DC2626"         # Vermelho de erro
    LIGHT_ON_PRIMARY = "#FFFFFF"    # Texto sobre azul
    LIGHT_ON_BACKGROUND = "#000000" # Texto padrão (preto)
    LIGHT_ON_SURFACE = "#000000"    # Texto sobre superfícies

    # ==========================
    # Cores principais - Tema Escuro (Verde + Preto)
    # ==========================
    DARK_PRIMARY = "#22C55E"        # Verde principal
    DARK_SECONDARY = "#16A34A"      # Verde mais escuro
    DARK_ACCENT = "#A3E635"         # Verde lima de destaque
    DARK_BACKGROUND = "#020617"     # Fundo quase preto (azul bem escuro)
    DARK_SURFACE = "#020617"        # Superfície igual ao fundo (flat)
    DARK_ERROR = "#F97373"          # Vermelho suave
    DARK_ON_PRIMARY = "#000000"     # Texto sobre o verde (fica legível)
    DARK_ON_BACKGROUND = "#E5E7EB"  # Texto claro sobre fundo escuro
    DARK_ON_SURFACE = "#E5E7EB"     # Texto claro sobre superfícies


class GymTheme:
    @staticmethod
    def light_theme():
        """Retorna o tema claro do Gym (azul claro)"""
        # Algumas versões do Flet não possuem InputDecorationTheme; tornar opcional
        theme_kwargs = dict(
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
        try:
            # Só adiciona se a classe existir nesta versão do Flet
            _ = ft.InputDecorationTheme  # type: ignore[attr-defined]
            theme_kwargs["input_decoration_theme"] = ft.InputDecorationTheme(  # type: ignore[assignment]
                label_style=ft.TextStyle(color="#1f2937"),   # cinza escuro (legível no claro)
                hint_style=ft.TextStyle(color="#6b7280"),    # cinza médio
                input_style=ft.TextStyle(color="#111827"),   # quase preto
            )
        except AttributeError:
            pass
        return ft.Theme(**theme_kwargs)

    @staticmethod
    def dark_theme():
        """Retorna o tema escuro do Gym (verde + preto)"""
        theme_kwargs = dict(
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
        try:
            _ = ft.InputDecorationTheme  # type: ignore[attr-defined]
            theme_kwargs["input_decoration_theme"] = ft.InputDecorationTheme(  # type: ignore[assignment]
                label_style=ft.TextStyle(color="#e5e7eb"),   # cinza claro
                hint_style=ft.TextStyle(color="#cbd5e1"),    # cinza claro 2
                input_style=ft.TextStyle(color="#f8fafc"),   # quase branco
            )
        except AttributeError:
            pass
        return ft.Theme(**theme_kwargs)


class Theme:
    # Window
    WINDOW_WIDTH = 980
    WINDOW_HEIGHT = 700
    THEME_MODE = ft.ThemeMode.DARK  # app inicia no tema escuro (verde + preto)

    # Colors & palette (para componentes que usam Theme.PRIMARY etc)
    PRIMARY = ft.Colors.GREEN_500
    SECONDARY = ft.Colors.GREEN_700
    ACCENT = ft.Colors.LIGHT_GREEN_400
    DANGER = ft.Colors.RED_600
    INFO = ft.Colors.BLUE_GREY_600

    TEXT_TITLE = ft.Colors.BLUE_400        # Títulos na Home ("CADASTROS")
    TEXT_SECTION = ft.Colors.ORANGE_400    # Seções em laranja como solicitado

    # Background gradients (top-left -> bottom-right)
    # Escuro: cinza → preto (tranquilo, sem verde)
    BG_GRADIENT_DARK = ["#0a0a0a", "#111111", "#1a1a1a"]
    # Claro: branco suave → azul bebê, sem "borda" branca destacada
    BG_GRADIENT_LIGHT = ["#f5f9ff", "#eaf3ff", "#d6e9ff"]

    # Mantido por compatibilidade (escolha padrão)
    BG_GRADIENT = BG_GRADIENT_DARK

    # App Themes (Light/Dark) for Gym
    @staticmethod
    def light_theme() -> ft.Theme:
        # Usa o tema claro definido no GymTheme
        return GymTheme.light_theme()

    @staticmethod
    def dark_theme() -> ft.Theme:
        # Usa o tema escuro definido no GymTheme
        return GymTheme.dark_theme()
