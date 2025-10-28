import flet as ft
from app.ui.components import with_bg, set_appbar, snack
from app.db import get_conn


def show_exercicios(page: ft.Page, on_back):
    page.clean()
    set_appbar(page, "Exercícios", ft.Colors.BLUE_700, show_back=True, on_back=lambda e=None: on_back())

    nome = ft.TextField(label="Nome do exercício", width=360)
    grupo = ft.TextField(label="Grupo muscular", width=220, hint_text="Peito, Costas, Pernas…")
    busca = ft.TextField(label="Buscar", prefix_icon=ft.Icons.SEARCH, width=540)
    status = ft.Text("", color=ft.Colors.BLUE_200)
    lista = ft.Column(spacing=6, scroll=ft.ScrollMode.AUTO)

    conn = get_conn()
    cur = conn.cursor()

    def salvar(_):
        if not (nome.value or "").strip() or not (grupo.value or "").strip():
            snack(page, "Preencha nome e grupo.", True); return
        cur.execute("INSERT INTO EXERCICIO (NOME, GRUPO) VALUES (?,?)", (nome.value.strip(), grupo.value.strip()))
        conn.commit(); snack(page, "Exercício criado.")
        nome.value = ""; grupo.value = ""; page.update()
        carregar(busca.value)

    def carregar(filtro=""):
        lista.controls.clear()
        if filtro:
            cur.execute(
                "SELECT ID_EXERCICIO, NOME, GRUPO FROM EXERCICIO WHERE NOME LIKE ? OR GRUPO LIKE ? ORDER BY GRUPO, NOME",
                (f"%{filtro}%", f"%{filtro}%"),
            )
        else:
            cur.execute("SELECT ID_EXERCICIO, NOME, GRUPO FROM EXERCICIO ORDER BY GRUPO, NOME")
        rows = cur.fetchall()
        status.value = f"Total: {len(rows)}" if rows else "Nenhum exercício."
        for eid, enome, egrupo in rows:
            def make_delete_button(exercicio_id, exercicio_nome):
                return ft.Container(
                    padding=6,
                    content=ft.IconButton(
                        icon=ft.Icons.DELETE,
                        icon_color=ft.Colors.RED_400,
                        icon_size=22,
                        tooltip="Excluir",
                        on_click=lambda e: confirmar_exclusao(exercicio_id, exercicio_nome),
                    ),
                )

            lista.controls.append(
                ft.Card(
                    elevation=2,
                    content=ft.Container(
                        padding=10,
                        content=ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            controls=[
                                ft.Text(f"{egrupo}", width=140, weight=ft.FontWeight.BOLD),
                                ft.Text(enome, expand=True),
                                make_delete_button(eid, enome),
                            ],
                        ),
                    ),
                )
            )
        page.update()

    def confirmar_exclusao(_id, _nome):
        def fechar_confirmacao(confirmar=False):
            dlg_confirm.open = False
            page.update()
            if confirmar:
                del_exercicio(_id)

        dlg_confirm = ft.AlertDialog(
            modal=True,
            title=ft.Text("Confirmar exclusão"),
            content=ft.Text(f"Tem certeza que deseja excluir o exercício '{_nome}'?"),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: fechar_confirmacao(False)),
                ft.TextButton("Excluir", on_click=lambda e: fechar_confirmacao(True)),
            ],
        )
        page.dialog = dlg_confirm
        dlg_confirm.open = True
        page.update()

    def del_exercicio(_id):
        try:
            cur.execute("DELETE FROM EXERCICIO WHERE ID_EXERCICIO= ?", (_id,))
            conn.commit(); snack(page, "Exercício removido."); carregar(busca.value)
        except Exception as ex:
            snack(page, f"Erro: {ex}", True)

    busca.on_change = lambda e: carregar(busca.value)
    busca.on_submit = lambda e: carregar(busca.value)

    page.add(
        with_bg(
            ft.Column(
                spacing=12,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Text("Catálogo de Exercícios", size=22, weight=ft.FontWeight.BOLD),
                    ft.Divider(),
                    ft.Row([nome, grupo, ft.ElevatedButton("Salvar", icon=ft.Icons.SAVE, on_click=salvar)], alignment=ft.MainAxisAlignment.CENTER, spacing=10, run_spacing=10, wrap=True),
                    ft.Row([busca], alignment=ft.MainAxisAlignment.CENTER),
                    status,
                    ft.Container(content=lista, height=400, border=ft.border.all(1, ft.Colors.BLUE_200), border_radius=10, padding=6),
                ],
            )
        )
    )

    carregar()
