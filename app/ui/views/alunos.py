import flet as ft
from app.ui.components import with_bg, set_appbar, snack
from app.config import Theme
from app.db import get_conn
from app.utils import validar_data_brasil, sqlite_para_brasileiro


def show_alunos(page: ft.Page, on_back):
    page.clean()
    set_appbar(page, "Alunos", ft.Colors.GREEN_700, show_back=True, on_back=lambda e=None: on_back())

    nome = ft.TextField(label="Nome do Aluno", width=360)
    data = ft.TextField(label="Nascimento (DD/MM/YYYY)", width=180, max_length=10)
    altura = ft.TextField(label="Altura (m) – opcional", width=150, hint_text="ex.: 1.75")

    busca = ft.TextField(label="Buscar", prefix_icon=ft.Icons.SEARCH, width=540)
    status = ft.Text("", color=ft.Colors.BLUE_200)
    lista = ft.Column(spacing=6, scroll=ft.ScrollMode.AUTO)

    def validar_data(_):
        ok, _iso = validar_data_brasil(data.value)
        data.error_text = None if ok else "Data inválida"
        page.update()

    data.on_blur = validar_data

    conn = get_conn()
    cur = conn.cursor()

    def salvar(_):
        if not (nome.value or "").strip():
            snack(page, "Informe o nome do aluno.", error=True); nome.focus(); return
        ok, iso = validar_data_brasil(data.value)
        if not ok:
            snack(page, "Data inválida (DD/MM/YYYY).", error=True); data.focus(); return
        try:
            alt = float(altura.value) if altura.value else None
            if alt is not None and alt <= 0:
                raise ValueError
        except Exception:
            snack(page, "Altura deve ser número positivo (ex.: 1.75).", error=True); altura.focus(); return
        cur.execute("INSERT INTO ALUNO (NOME, DATA_NASC, ALTURA_M) VALUES (?,?,?)", (nome.value.strip(), iso, alt))
        conn.commit()
        snack(page, "Aluno cadastrado!")
        nome.value = ""; data.value = ""; altura.value = ""; page.update()
        carregar(busca.value)

    def carregar(filtro=""):
        lista.controls.clear()
        if filtro:
            cur.execute("SELECT ID_ALUNO, NOME, DATA_NASC, ALTURA_M FROM ALUNO WHERE NOME LIKE ? ORDER BY NOME", (f"%{filtro}%",))
        else:
            cur.execute("SELECT ID_ALUNO, NOME, DATA_NASC, ALTURA_M FROM ALUNO ORDER BY NOME")
        rows = cur.fetchall()
        status.value = f"Total: {len(rows)}" if rows else "Nenhum aluno."
        for aid, anome, dn, alt in rows:
            data_br = sqlite_para_brasileiro(dn)
            linha = ft.Card(
                elevation=2,
                content=ft.Container(
                    padding=12,
                    content=ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Text(f"ID: {aid}", width=80, weight=ft.FontWeight.BOLD),
                            ft.Text(anome, expand=True),
                            ft.Text(f"Nasc: {data_br}", width=140),
                            ft.Text(f"Alt: {'-' if alt is None else alt}", width=110),
                            ft.IconButton(icon=ft.Icons.DELETE, icon_color=ft.Colors.RED_400,
                                          tooltip="Excluir", on_click=lambda e, _id=aid: del_aluno(_id)),
                        ],
                    ),
                ),
            )
            lista.controls.append(linha)
        page.update()

    def del_aluno(_id):
        try:
            cur.execute("DELETE FROM ALUNO WHERE ID_ALUNO= ?", (_id,))
            conn.commit()
            snack(page, "Aluno removido.")
            carregar(busca.value)
        except Exception as ex:
            snack(page, f"Erro: {ex}", error=True)

    busca.on_change = lambda e: carregar(busca.value)
    busca.on_submit = lambda e: carregar(busca.value)

    page.add(
        with_bg(
            ft.Column(
                spacing=12,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Text("Cadastro de Alunos", size=22, weight=ft.FontWeight.BOLD),
                    ft.Divider(),
                    ft.Row([nome, data, altura, ft.ElevatedButton("Salvar", icon=ft.Icons.SAVE, on_click=salvar)], alignment=ft.MainAxisAlignment.CENTER),
                    ft.Row([busca], alignment=ft.MainAxisAlignment.CENTER),
                    status,
                    ft.Container(content=lista, height=360, border=ft.border.all(1, ft.Colors.BLUE_200), border_radius=10, padding=6),
                ],
            )
        )
    )

    carregar()
