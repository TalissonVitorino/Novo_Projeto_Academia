import flet as ft
from app.ui.components import with_bg, set_appbar, snack
from app.db import get_conn
from app.utils import sqlite_para_brasileiro


def show_relatorios(page: ft.Page, on_back):
    page.clean()
    # AppBar adaptativa ao tema (bgcolor automático)
    set_appbar(page, "Relatório de Sessões", None, show_back=True, on_back=lambda e=None: on_back())

    # Responsividade simples
    is_small = (page.width or 0) <= 420

    busca_aluno = ft.TextField(
        label="Filtrar por nome do aluno",
        prefix_icon=ft.Icons.SEARCH,
        width=None,
        expand=1,
    )
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

            def make_buttons(sessao_id, info_str):
                return [
                    ft.TextButton("Detalhes", on_click=lambda e: detalhar(sessao_id)),
                    ft.Container(
                        padding=6,
                        content=ft.IconButton(
                            icon=ft.Icons.DELETE,
                            icon_color=ft.Colors.RED_400,
                            icon_size=22,
                            tooltip="Excluir sessão",
                            on_click=lambda e: confirmar_exclusao(sessao_id, info_str),
                        ),
                    ),
                ]

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
                                    ] + make_buttons(sid, f"{an} – {pn} em {data_br}"),
                                ),
                            ],
                        ),
                    ),
                )
            )
        page.update()

    def detalhar(_sid):
        dialog = ft.AlertDialog(modal=True)
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
            card_controls = [
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Text(f"{egrupo} – {enome}", expand=True, weight=ft.FontWeight.BOLD),
                        ft.Text(f"Séries: {s or '-'}  Reps: {r or '-'}  Peso: {p or '-'}"),
                        badge,
                    ],
                )
            ]
            if obs:
                card_controls.append(ft.Text(f"Obs: {obs}", size=12, italic=True, color=ft.Colors.BLUE_GREY_300))
            corpo.controls.append(
                ft.Card(
                    elevation=1,
                    content=ft.Container(
                        padding=8,
                        content=ft.Column(spacing=4, controls=card_controls),
                    ),
                )
            )

        def close_dialog():
            dialog.open = False
            page.update()

        # Largura responsiva do diálogo para telas pequenas (Android)
        try:
            pw = int(page.width or 360)
        except Exception:
            pw = 360
        dlg_w = max(300, min(720, pw - 32))

        dialog.content = ft.Container(
            width=dlg_w,
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

    def confirmar_exclusao(_sid, _info):
        def fechar_confirmacao(confirmar=False):
            dlg_confirm.open = False
            page.update()
            if confirmar:
                excluir(_sid)

        dlg_confirm = ft.AlertDialog(
            modal=True,
            title=ft.Text("Confirmar exclusão"),
            content=ft.Text(f"Tem certeza que deseja excluir a sessão #{_sid}?\n{_info}"),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: fechar_confirmacao(False)),
                ft.TextButton("Excluir", on_click=lambda e: fechar_confirmacao(True)),
            ],
        )
        page.dialog = dlg_confirm
        dlg_confirm.open = True
        page.update()

    def excluir(_sid):
        try:
            cur.execute("DELETE FROM SESSAO WHERE ID_SESSAO=?", (_sid,))
            conn.commit()
            snack(page, "Sessão excluída.")
            carregar(busca_aluno.value)
        except Exception as ex:
            conn.rollback()
            snack(page, f"Erro ao excluir sessão: {ex}", True)

    busca_aluno.on_change = lambda e: carregar(busca_aluno.value)
    busca_aluno.on_submit = lambda e: carregar(busca_aluno.value)

    page.add(
        with_bg(
            page,
            ft.Column(
                spacing=12,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Text("Relatório de Sessões", size=22, weight=ft.FontWeight.BOLD),
                    ft.Divider(),
                    ft.Row([busca_aluno], alignment=ft.MainAxisAlignment.CENTER),
                    status,
                    ft.Container(
                        content=ft.Scrollbar(content=lista, thumb_visibility=True, interactive=True),
                        height=420,
                        border=ft.border.all(1, ft.Colors.BLUE_GREY_200),
                        border_radius=10,
                        padding=6,
                    ),
                ],
            )
        )
    )

    carregar()
