import flet as ft

from app.config import Theme
from app.db import init_db
from app.ui.views.home import show_home
from app.ui.views.alunos import show_alunos
from app.ui.views.exercicios import show_exercicios
from app.ui.views.planos import show_planos
from app.ui.views.treino import show_treino
from app.ui.views.relatorios import show_relatorios


def main(page: ft.Page):
    # Init & theme
    init_db()
    page.title = "Checklist de Treino (Academia)"

    # Apply Gym themes (light/dark palettes)
    page.theme = Theme.light_theme()
    page.dark_theme = Theme.dark_theme()

    # Try to restore saved theme from client storage (web/mobile) or keep default
    try:
        saved = page.client_storage.get("theme_mode")
    except Exception:
        saved = None
    if saved == "light":
        page.theme_mode = ft.ThemeMode.LIGHT
    elif saved == "dark":
        page.theme_mode = ft.ThemeMode.DARK
    else:
        page.theme_mode = Theme.THEME_MODE

    page.window_width = Theme.WINDOW_WIDTH
    page.window_height = Theme.WINDOW_HEIGHT

    # Keep track of current renderer to re-render on resize
    current_render = {"fn": None}

    def render(fn):
        current_render["fn"] = fn
        fn()

    def on_resize(e):
        fn = current_render.get("fn")
        if callable(fn):
            fn()

    page.on_resized = on_resize

    # Navigation callbacks
    def go_home():
        def _show():
            show_home(
                page,
                on_go_alunos=go_alunos,
                on_go_exercicios=go_exercicios,
                on_go_planos=go_planos,
                on_go_treino=go_treino,
                on_go_relatorios=go_relatorios,
            )
        render(_show)

    def go_alunos():
        render(lambda: show_alunos(page, on_back=go_home))

    def go_exercicios():
        render(lambda: show_exercicios(page, on_back=go_home))

    def go_planos():
        render(lambda: show_planos(page, on_back=go_home))

    def go_treino():
        render(lambda: show_treino(page, on_back=go_home))

    def go_relatorios():
        render(lambda: show_relatorios(page, on_back=go_home))

    # Start at home
    go_home()
