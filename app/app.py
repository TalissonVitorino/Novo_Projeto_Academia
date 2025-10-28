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
    page.theme_mode = Theme.THEME_MODE
    page.window_width = Theme.WINDOW_WIDTH
    page.window_height = Theme.WINDOW_HEIGHT

    # Navigation callbacks
    def go_home():
        show_home(
            page,
            on_go_alunos=go_alunos,
            on_go_exercicios=go_exercicios,
            on_go_planos=go_planos,
            on_go_treino=go_treino,
            on_go_relatorios=go_relatorios,
        )

    def go_alunos():
        show_alunos(page, on_back=go_home)

    def go_exercicios():
        show_exercicios(page, on_back=go_home)

    def go_planos():
        show_planos(page, on_back=go_home)

    def go_treino():
        show_treino(page, on_back=go_home)

    def go_relatorios():
        show_relatorios(page, on_back=go_home)

    # Start at home
    go_home()
