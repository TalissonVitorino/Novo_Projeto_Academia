import flet as ft
from app.ui.components import with_bg, set_appbar
from app.config import Theme
from app.db import get_conn


def _contagem():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM ALUNO;"); a = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM PLANO;"); p = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM SESSAO;"); s = cur.fetchone()[0]
    conn.close()
    return a, p, s


def show_home(
    page: ft.Page,
    on_go_alunos,
    on_go_exercicios,
    on_go_planos,
    on_go_treino,
    on_go_relatorios,
):
    page.clean()
    a, p, s = _contagem()
    set_appbar(page, "Checklist de Treino", ft.Colors.BLUE_GREY_800, show_back=False)

    # Responsividade simples baseada na largura atual da página
    is_small = (page.width or 0) <= 420
    btn_w_small = 180
    btn_w = 220
    treino_btn_w = 260

    card = ft.Card(
        content=ft.Container(
            padding=16 if is_small else 40,
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=18,
                controls=[
                    ft.Text("Academia – Dashboard", size=28, weight=ft.FontWeight.BOLD),
                    ft.Divider(),
                    ft.Row(
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=30,
                        run_spacing=10,
                        wrap=True,
                        controls=[
                            ft.Text(f"Alunos: {a}", size=16, color=ft.Colors.BLUE_300),
                            ft.Text(f"Planos: {p}", size=16, color=ft.Colors.GREEN_300),
                            ft.Text(f"Sessões: {s}", size=16, color=ft.Colors.ORANGE_300),
                        ],
                    ),
                    ft.Container(height=12),
                    ft.Text("CADASTROS", size=18, weight=ft.FontWeight.BOLD, color=Theme.TEXT_TITLE),
                    ft.Row(
                        alignment=ft.MainAxisAlignment.CENTER, spacing=14, run_spacing=10, wrap=True,
                        controls=[
                            ft.ElevatedButton(
                                "Alunos", icon=ft.Icons.PERSON, width=(btn_w_small if is_small else btn_w),
                                on_click=lambda e: on_go_alunos(),
                                style=ft.ButtonStyle(bgcolor=Theme.SECONDARY, color=ft.Colors.WHITE)
                            ),
                            ft.ElevatedButton(
                                "Exercícios", icon=ft.Icons.FITNESS_CENTER, width=(btn_w_small if is_small else btn_w),
                                on_click=lambda e: on_go_exercicios(),
                                style=ft.ButtonStyle(bgcolor=Theme.PRIMARY, color=ft.Colors.WHITE)
                            ),
                            ft.ElevatedButton(
                                "Planos de Treino", icon=ft.Icons.VIEW_LIST, width=(btn_w_small if is_small else btn_w),
                                on_click=lambda e: on_go_planos(),
                                style=ft.ButtonStyle(bgcolor=ft.Colors.PURPLE_600, color=ft.Colors.WHITE)
                            ),
                        ],
                    ),
                    ft.Container(height=16),
                    ft.Text("TREINO", size=18, weight=ft.FontWeight.BOLD, color=Theme.TEXT_SECTION),
                    ft.Row(
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=14,
                        run_spacing=10,
                        wrap=True,
                        controls=[
                            ft.ElevatedButton(
                                "Iniciar Treino (Checklist)", icon=ft.Icons.PLAY_ARROW,
                                width=(btn_w if not is_small else btn_w_small),
                                on_click=lambda e: on_go_treino(),
                                style=ft.ButtonStyle(bgcolor=ft.Colors.ORANGE_600, color=ft.Colors.WHITE)
                            ),
                            ft.ElevatedButton(
                                "Relatório de Sessões", icon=ft.Icons.ANALYTICS,
                                width=(btn_w if not is_small else btn_w_small),
                                on_click=lambda e: on_go_relatorios(),
                                style=ft.ButtonStyle(bgcolor=ft.Colors.BLUE_GREY_600, color=ft.Colors.WHITE)
                            ),
                        ],
                    ),
                ],
            ),
        ),
        elevation=8,
    )

    page.add(with_bg(ft.Container(content=card, alignment=ft.alignment.center, padding=20)))
