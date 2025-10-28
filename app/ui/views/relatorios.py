import flet as ft
from app.ui.components import with_bg, set_appbar
from app.db import get_conn
from app.utils import sqlite_para_brasileiro


def show_relatorios(page: ft.Page, on_back):
    page.clean()
    set_appbar(page, "Relatório de Sessões", ft.Colors.BLUE_GREY_700, show_back=True, on_back=lambda e=None: on_back())

    busca_aluno = ft.TextField(label="Filtrar por nome do aluno", prefix_icon=ft.Icons.SEARCH, width=480)
    lista = ft.Column(spacing=6, scroll=ft.ScrollMode.AUTO)
    status = ft.Text("", color=ft.Colors.BLUE_200)

    conn = get_conn()
    cur = conn.cursor()

    def carregar(f=""):
        lista.controls.clear()
        if f:
            cur.execute(
                """
                SELECT s.ID_SESSAO, s.DATA_SESSAO, a.NOME, p.NOME
                FROM SESSAO s
                JOIN ALUNO a ON a.ID_ALUNO = s.ID_ALUNO
                JOIN PLANO p ON p.ID_PLANO = s.ID_PLANO
                WHERE a.NOME LIKE ?
                ORDER BY s.DATA_SESSAO DESC, s.ID_SESSAO DESC
                """,
                (f"%{f}%",),
            )
        else:
            cur.execute(
                """
                SELECT s.ID_SESSAO, s.DATA_SESSAO, a.NOME, p.NOME
                FROM SESSAO s
                JOIN ALUNO a ON a.ID_ALUNO = s.ID_ALUNO
                JOIN PLANO p ON p.ID_PLANO = s.ID_PLANO
                ORDER BY s.DATA_SESSAO DESC, s.ID_SESSAO DESC
                """
            )
        rows = cur.fetchall()
        status.value = f"Total: {len(rows)}" if rows else "Nenhuma sessão."
        for sid, d, an, pn in rows:
            data_br = sqlite_para_brasileiro(d)
            lista.controls.append(
                ft.Card(
                    elevation=2,
                    content=ft.Container(
                        padding=10,
                        content=ft.Column(
                            controls=[
                                ft.Row(
                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                    controls=[
                                        ft.Text(f"#{sid} • {data_br}", weight=ft.FontWeight.BOLD),
                                        ft.Text(f"{an} – {pn}"),
                                        ft.TextButton("Detalhes", on_click=lambda e, _sid=sid: detalhar(_sid)),
                                        ft.IconButton(
                                            icon=ft.Icons.DELETE,
                                            icon_color=ft.Colors.RED_400,
                                            tooltip="Excluir sessão",
                                            on_click=lambda e, _sid=sid: excluir(_sid),
                                        ),
                                    ],
                                ),
                            ],
                        ),
                    ),
                )
            )
        page.update()

    def detalhar(_sid):
        dialog = ft.AlertDialog(modal=True)
        page.overlay.append(dialog)
        corpo = ft.Column(spacing=6, scroll=ft.ScrollMode.AUTO, height=360)

        cur.execute(
            """
            SELECT e.NOME, e.GRUPO, si.FEITO, si.SERIES_FEITAS, si.REPS_MEDIA, si.PESO_MEDIA, si.OBS
            FROM SESSAO_ITEM si
            JOIN EXERCICIO e ON e.ID_EXERCICIO = si.ID_EXERCICIO
            WHERE si.ID_SESSAO=? ORDER BY si.ID_ITEM
            """,
            (_sid,),
        )
        rows = cur.fetchall()
        if not rows:
            corpo.controls.append(ft.Text("Sem itens."))
        for enome, egrupo, feito, s, r, p, obs in rows:
            badge = ft.Container(
                padding=ft.padding.symmetric(horizontal=8, vertical=2),
                border_radius=8,
                bgcolor=ft.Colors.GREEN_600 if feito else ft.Colors.GREY_600,
                content=ft.Text("Feito" if feito else "Pendente", size=11, color=ft.Colors.WHITE),
            )
            corpo.controls.append(
                ft.Card(
                    elevation=1,
                    content=ft.Container(
                        padding=8,
                        content=ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            controls=[
                                ft.Text(f"{egrupo} – {enome}", expand=True),
                                ft.Text(f"Séries: {s or '-'}  Reps: {r or '-'}  Peso: {p or '-'}"),
                                badge,
                            ],
                        ),
                    ),
                )
            )

        def close_dialog():
            dialog.open = False
            page.update()

        dialog.content = ft.Container(
            width=720,
            padding=16,
            content=ft.Column(
                spacing=12,
                controls=[
                    ft.Text(f"Sessão #{_sid}", size=18, weight=ft.FontWeight.BOLD),
                    corpo,
                    ft.Row(alignment=ft.MainAxisAlignment.END, controls=[ft.TextButton("Fechar", on_click=lambda e: close_dialog())]),
                ],
            ),
        )
        dialog.open = True
        page.update()

    def excluir(_sid):
        cur.execute("DELETE FROM SESSAO WHERE ID_SESSAO=?", (_sid,))
        conn.commit()
        carregar(busca_aluno.value)

    busca_aluno.on_change = lambda e: carregar(busca_aluno.value)
    busca_aluno.on_submit = lambda e: carregar(busca_aluno.value)

    page.add(
        with_bg(
            ft.Column(
                spacing=12,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Text("Relatório de Sessões", size=22, weight=ft.FontWeight.BOLD),
                    ft.Divider(),
                    ft.Row([busca_aluno], alignment=ft.MainAxisAlignment.CENTER),
                    status,
                    ft.Container(content=lista, height=420, border=ft.border.all(1, ft.Colors.BLUE_GREY_200), border_radius=10, padding=6),
                ],
            )
        )
    )

    carregar()
