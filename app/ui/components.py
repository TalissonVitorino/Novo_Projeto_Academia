import flet as ft
from app.config import Theme


def with_bg(content: ft.Control, colors=None) -> ft.Container:
    # Wrapper com gradiente, SafeArea e rolagem para evitar conteúdo oculto em telas pequenas
    return ft.Container(
        expand=True,
        padding=20,
        gradient=ft.LinearGradient(
            begin=ft.alignment.top_left,
            end=ft.alignment.bottom_right,
            colors=colors or Theme.BG_GRADIENT,
        ),
        content=ft.Container(
            alignment=ft.alignment.top_center,
            content=ft.SafeArea(
                content=ft.Column(
                    controls=[content],
                    scroll=ft.ScrollMode.AUTO,
                    spacing=0,
                )
            ),
        ),
    )


def set_appbar(page: ft.Page, title: str, bgcolor=None, show_back: bool = False, on_back=None):
    # Armazena handler no objeto page para permitir tecla ESC voltar
    if show_back and on_back:
        page._back_handler = on_back
        # Aumenta a área clicável do botão Voltar para evitar problemas de clique
        leading = ft.Container(
            padding=8,
            content=ft.IconButton(
                icon=ft.Icons.ARROW_BACK,
                icon_size=28,
                tooltip="Voltar",
                on_click=lambda e: on_back(e),
            ),
        )
    else:
        page._back_handler = None
        leading = None

    page.appbar = ft.AppBar(
        leading=leading,
        title=ft.Text(title),
        center_title=True,
        bgcolor=bgcolor,
    )

    def _on_kb(ev: ft.KeyboardEvent):
        if ev.key == "Escape" and getattr(page, "_back_handler", None):
            try:
                page._back_handler(ev)
            except Exception:
                pass

    page.on_keyboard_event = _on_kb
    page.update()


def snack(page: ft.Page, msg: str, error: bool = False):
    page.snack_bar = ft.SnackBar(
        ft.Text(msg), bgcolor=ft.Colors.RED_400 if error else ft.Colors.GREEN_600
    )
    page.snack_bar.open = True
    page.update()
