import flet as ft
from app.ui.components import with_bg, set_appbar, snack
from app.db import get_conn


def show_planos(page: ft.Page, on_back):
    page.clean()
    set_appbar(page, "Planos de Treino", ft.Colors.PURPLE_700, show_back=True, on_back=lambda e=None: on_back())

    nome_plano = ft.TextField(label="Nome do plano (ex.: Treino A)", width=260)
    busca = ft.TextField(label="Buscar plano", prefix_icon=ft.Icons.SEARCH, width=360)
    status = ft.Text("", color=ft.Colors.BLUE_200)
    lista = ft.Column(spacing=6, scroll=ft.ScrollMode.AUTO)

    conn = get_conn()
    cur = conn.cursor()

    def salvar(_):
        nome = (nome_plano.value or "").strip()
        if not nome:
            snack(page, "Informe o nome do plano.", True); nome_plano.focus(); return
        try:
            cur.execute("INSERT INTO PLANO (NOME) VALUES (?)", (nome,))
            conn.commit(); snack(page, "Plano criado.")
            nome_plano.value = ""; page.update()
            carregar(busca.value)
        except Exception as ex:
            snack(page, f"Erro ao criar plano: {ex}", True)

    def carregar(filtro=""):
        lista.controls.clear()
        if filtro:
            cur.execute("SELECT ID_PLANO, NOME FROM PLANO WHERE NOME LIKE ? ORDER BY NOME", (f"%{filtro}%",))
        else:
            cur.execute("SELECT ID_PLANO, NOME FROM PLANO ORDER BY NOME")
        rows = cur.fetchall()
        status.value = f"Total: {len(rows)}" if rows else "Nenhum plano."
        for pid, pnome in rows:
            def make_menu(plano_id, plano_nome):
                def on_select(e):
                    try:
                        idx = int(e.data) if e.data is not None else -1
                    except Exception:
                        idx = -1
                    if idx == 0:
                        editar_plano_exercicios(plano_id, plano_nome)
                    elif idx == 1:
                        confirmar_exclusao(plano_id, plano_nome)
                return ft.PopupMenuButton(
                    icon=ft.Icons.MORE_VERT,
                    tooltip="Opções",
                    on_select=on_select,
                    items=[
                        ft.PopupMenuItem(
                            text="Editar exercícios",
                            icon=ft.Icons.LIST,
                        ),
                        ft.PopupMenuItem(
                            text="Excluir",
                            icon=ft.Icons.DELETE,
                        ),
                    ]
                )

            lista.controls.append(
                ft.Card(
                    elevation=2,
                    content=ft.Container(
                        padding=10,
                        content=ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            controls=[
                                ft.Text(f"ID: {pid}", width=80, weight=ft.FontWeight.BOLD),
                                ft.Text(pnome, expand=True),
                                make_menu(pid, pnome),
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
                del_plano(_id)

        dlg_confirm = ft.AlertDialog(
            modal=True,
            title=ft.Text("Confirmar exclusão"),
            content=ft.Text(f"Tem certeza que deseja excluir o plano '{_nome}'?"),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: fechar_confirmacao(False)),
                ft.TextButton("Excluir", on_click=lambda e: fechar_confirmacao(True)),
            ],
        )
        page.dialog = dlg_confirm
        dlg_confirm.open = True
        page.update()

    def del_plano(_id):
        try:
            # Remover dependências manualmente para bancos antigos sem CASCADE
            # 1) Remover itens de sessões que pertencem a sessões do plano
            cur.execute("SELECT ID_SESSAO FROM SESSAO WHERE ID_PLANO=?", (_id,))
            sess_ids = [row[0] for row in cur.fetchall()]
            if sess_ids:
                # Monta placeholders para IN
                placeholders = ",".join(["?"] * len(sess_ids))
                cur.execute(f"DELETE FROM SESSAO_ITEM WHERE ID_SESSAO IN ({placeholders})", sess_ids)
                cur.execute(f"DELETE FROM SESSAO WHERE ID_SESSAO IN ({placeholders})", sess_ids)
            # 2) Remover relações do plano com exercícios
            cur.execute("DELETE FROM PLANO_EXERCICIO WHERE ID_PLANO=?", (_id,))
            # 3) Remover o plano em si
            cur.execute("DELETE FROM PLANO WHERE ID_PLANO= ?", (_id,))
            conn.commit(); snack(page, "Plano removido."); carregar(busca.value)
        except Exception as ex:
            conn.rollback()
            snack(page, f"Erro: {ex}", True)

    def editar_plano_exercicios(_id_plano: int, _nome: str):
        # Dialog to add/remove exercises for the plan
        dlg_content = ft.Column(spacing=10, width=640, scroll=ft.ScrollMode.AUTO)
        titulo = ft.Text(f"Plano: {_nome}", size=18, weight=ft.FontWeight.BOLD)
        lista_exercicios = ft.Dropdown(label="Exercício")
        series = ft.TextField(label="Séries", width=90, value="3")
        reps = ft.TextField(label="Reps", width=90, value="10")
        itens = ft.Column(spacing=6, height=260, scroll=ft.ScrollMode.AUTO)

        def load_exercicios():
            lista_exercicios.options.clear()
            cur.execute("SELECT ID_EXERCICIO, NOME, GRUPO FROM EXERCICIO ORDER BY GRUPO, NOME")
            rows = cur.fetchall()
            for eid, enome, egrupo in rows:
                # Use explicit kwargs to avoid any API incompatibilities
                lista_exercicios.options.append(ft.dropdown.Option(key=str(eid), text=f"{egrupo} - {enome}"))
            # Select first option by default (if any) so add works immediately
            lista_exercicios.value = str(rows[0][0]) if rows else None

        def load_itens():
            itens.controls.clear()
            cur.execute(
                "SELECT pe.ID_EXERCICIO, e.NOME, e.GRUPO, pe.SERIES, pe.REPS, pe.ORDEM "
                "FROM PLANO_EXERCICIO pe JOIN EXERCICIO e ON e.ID_EXERCICIO = pe.ID_EXERCICIO "
                "WHERE pe.ID_PLANO=? ORDER BY pe.ORDEM",
                (_id_plano,),
            )
            for eid, enome, egrupo, s, r, ordem in cur.fetchall():
                def make_remove_button(exercicio_id):
                    return ft.Container(
                        padding=6,
                        content=ft.IconButton(
                            icon=ft.Icons.DELETE,
                            icon_color=ft.Colors.RED_400,
                            icon_size=22,
                            tooltip="Remover",
                            on_click=lambda e: rm_item(exercicio_id),
                        ),
                    )

                itens.controls.append(
                    ft.Card(
                        elevation=1,
                        content=ft.Container(
                            padding=8,
                            content=ft.Row(
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                controls=[
                                    ft.Text(f"{ordem:02d} - {egrupo}", width=140, weight=ft.FontWeight.BOLD),
                                    ft.Text(f"{enome}", expand=True),
                                    ft.Text(f"{s}x{r}", width=80),
                                    make_remove_button(eid),
                                ],
                            ),
                        ),
                    )
                )
            page.update()

        def rm_item(_eid):
            cur.execute("DELETE FROM PLANO_EXERCICIO WHERE ID_PLANO=? AND ID_EXERCICIO=?", (_id_plano, _eid))
            conn.commit()
            snack(page, "Exercício removido do plano.")
            load_itens()

        def add_item(_):
            if not lista_exercicios.value:
                snack(page, "Selecione um exercício.", True); return
            try:
                s = int(series.value or 0); r = int(reps.value or 0)
                if s <= 0 or r <= 0: raise ValueError
            except Exception:
                snack(page, "Séries e reps devem ser inteiros positivos.", True); return
            cur.execute("SELECT COALESCE(MAX(ORDEM),0)+1 FROM PLANO_EXERCICIO WHERE ID_PLANO=?", (_id_plano,))
            ordem = cur.fetchone()[0]
            cur.execute(
                "INSERT OR REPLACE INTO PLANO_EXERCICIO (ID_PLANO, ID_EXERCICIO, ORDEM, SERIES, REPS) VALUES (?,?,?,?,?)",
                (_id_plano, int(lista_exercicios.value), ordem, s, r),
            )
            conn.commit()
            snack(page, "Exercício adicionado ao plano.")
            load_itens()

        def close_dialog():
            dialog.open = False
            page.update()

        load_exercicios(); load_itens()

        dlg_content.controls = [
            titulo,
            ft.Row([lista_exercicios, series, reps, ft.ElevatedButton("Adicionar", icon=ft.Icons.ADD, on_click=add_item)], spacing=10, run_spacing=10, wrap=True),
            ft.Container(height=6),
            ft.Text("Exercícios do Plano", weight=ft.FontWeight.BOLD),
            ft.Container(content=itens, border=ft.border.all(1, ft.Colors.BLUE_200), border_radius=10, padding=6),
            ft.Container(height=8),
            ft.Row([ft.ElevatedButton("Fechar", on_click=lambda e: close_dialog())], alignment=ft.MainAxisAlignment.END),
        ]
        dialog = ft.AlertDialog(content=dlg_content, modal=True)
        page.dialog = dialog
        dialog.open = True
        page.update()

    busca.on_change = lambda e: carregar(busca.value)
    busca.on_submit = lambda e: carregar(busca.value)

    page.add(
        with_bg(
            ft.Column(
                spacing=12,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Text("Planos de Treino", size=22, weight=ft.FontWeight.BOLD),
                    ft.Divider(),
                    ft.Row([nome_plano, ft.ElevatedButton("Salvar", icon=ft.Icons.SAVE, on_click=salvar)], alignment=ft.MainAxisAlignment.CENTER, spacing=10, run_spacing=10, wrap=True),
                    ft.Row([busca], alignment=ft.MainAxisAlignment.CENTER),
                    status,
                    ft.Container(content=lista, height=400, border=ft.border.all(1, ft.Colors.BLUE_200), border_radius=10, padding=6),
                ],
            )
        )
    )

    carregar()
