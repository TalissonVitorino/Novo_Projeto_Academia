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

    page.theme_mode = Theme.THEME_MODE

    # Window size only for desktop (not for web/mobile)
    try:
        if page.web:
            pass  # Skip window size for web
        else:
            page.window_width = Theme.WINDOW_WIDTH
            page.window_height = Theme.WINDOW_HEIGHT
    except Exception:
        pass

    # Keep track of current renderer to re-render on resize
    current_render = {"fn": None}

    def render(fn):
        current_render["fn"] = fn
        fn()

    # Debounce e threshold para evitar loop de re-render no navegador mobile
    resize_state = {
        "last_w": None,
        "last_h": None,
        "last_ts": 0.0,
    }

    def _get_size():
        # Em web, page.width/height refletem o viewport. Em desktop, usar window_*.
        w = getattr(page, "width", None)
        h = getattr(page, "height", None)
        if w is None or h is None:
            # fallback desktop
            w = getattr(page, "window_width", None)
            h = getattr(page, "window_height", None)
        return w, h

    def on_resize(e):
        fn = current_render.get("fn")
        if not callable(fn):
            return

        # Parâmetros diferentes para web vs desktop
        is_web = False
        try:
            is_web = bool(page.web)
        except Exception:
            is_web = False

        # Thresholds de variação mínima e intervalo mínimo entre re-renderizações
        min_interval = 0.35 if is_web else 0.10
        min_delta = 24 if is_web else 8

        # Medir tamanho atual e comparar com último
        try:
            import time as _time
            now = _time.monotonic()
        except Exception:
            now = 0.0

        w, h = _get_size()
        lw, lh = resize_state["last_w"], resize_state["last_h"]

        # Se ainda não temos referência, apenas armazenar e evitar re-render imediato
        if lw is None or lh is None:
            resize_state["last_w"], resize_state["last_h"], resize_state["last_ts"] = w, h, now
            return

        dw = 0 if (w is None or lw is None) else abs(w - lw)
        dh = 0 if (h is None or lh is None) else abs(h - lh)

        # Evitar re-render por pequenas oscilações (ex.: barra de endereço do mobile)
        if dw < min_delta and dh < min_delta and (now - resize_state["last_ts"]) < min_interval:
            return

        # Atualiza referência e re-renderiza a view atual
        resize_state["last_w"], resize_state["last_h"], resize_state["last_ts"] = w, h, now
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
