import flet as ft
from app.ui.components import with_bg, set_appbar, snack
from app.config import Theme
from app.db import get_conn
from app.utils import validar_data_brasil, sqlite_para_brasileiro, calcular_imc


def show_alunos(page: ft.Page, on_back):
    page.clean()
    set_appbar(page, "Alunos", ft.Colors.GREEN_700, show_back=True, on_back=lambda e=None: on_back())

    # Responsividade simples
    is_small = (page.width or 0) <= 420

    nome = ft.TextField(label="Nome do Aluno", expand=1)
    data = ft.TextField(label="Nascimento (DD/MM/YYYY)", width=140 if is_small else 180, max_length=10)
    altura = ft.TextField(label="Altura (m) – opcional", width=120 if is_small else 150, hint_text="ex.: 1.75")
    peso = ft.TextField(label="Peso (kg) – opcional", width=120 if is_small else 150, hint_text="ex.: 75.5")

    busca = ft.TextField(label="Buscar", prefix_icon=ft.Icons.SEARCH, expand=1)
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
                raise ValueError("Altura inválida")
        except Exception:
            snack(page, "Altura deve ser número positivo (ex.: 1.75).", error=True); altura.focus(); return
        try:
            pes = float(peso.value) if peso.value else None
            if pes is not None and pes <= 0:
                raise ValueError("Peso inválido")
        except Exception:
            snack(page, "Peso deve ser número positivo (ex.: 75.5).", error=True); peso.focus(); return
        cur.execute("INSERT INTO ALUNO (NOME, DATA_NASC, ALTURA_M, PESO_KG) VALUES (?,?,?,?)", (nome.value.strip(), iso, alt, pes))
        conn.commit()
        snack(page, "Aluno cadastrado!")
        nome.value = ""; data.value = ""; altura.value = ""; peso.value = ""; page.update()
        carregar(busca.value)

    def carregar(filtro=""):
        lista.controls.clear()
        if filtro:
            cur.execute("SELECT ID_ALUNO, NOME, DATA_NASC, ALTURA_M, PESO_KG FROM ALUNO WHERE NOME LIKE ? ORDER BY NOME", (f"%{filtro}%",))
        else:
            cur.execute("SELECT ID_ALUNO, NOME, DATA_NASC, ALTURA_M, PESO_KG FROM ALUNO ORDER BY NOME")
        rows = cur.fetchall()
        status.value = f"Total: {len(rows)}" if rows else "Nenhum aluno."
        for aid, anome, dn, alt, pes in rows:
            data_br = sqlite_para_brasileiro(dn)
            imc_val, imc_cat, imc_cor = calcular_imc(pes, alt)

            def make_delete_button(aluno_id, aluno_nome):
                return ft.Container(
                    padding=6,
                    content=ft.IconButton(
                        icon=ft.Icons.DELETE,
                        icon_color=ft.Colors.RED_400,
                        icon_size=22,
                        tooltip="Excluir",
                        on_click=lambda e: confirmar_exclusao(aluno_id, aluno_nome),
                    ),
                )

            linha = ft.Card(
                elevation=2,
                content=ft.Container(
                    padding=12,
                    content=ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        wrap=True,
                        run_spacing=6,
                        controls=[
                            ft.Text(f"ID: {aid}", width=60 if is_small else 70, weight=ft.FontWeight.BOLD),
                            ft.Text(anome, expand=True),
                            ft.Text(f"Nasc: {data_br}", width=120 if is_small else 130),
                            ft.Text(f"Alt: {'-' if alt is None else f'{alt}m'}", width=80 if is_small else 90),
                            ft.Text(f"Peso: {'-' if pes is None else f'{pes}kg'}", width=90 if is_small else 100),
                            ft.Container(
                                padding=ft.padding.symmetric(horizontal=8, vertical=4),
                                border_radius=8,
                                bgcolor=imc_cor,
                                content=ft.Text(f"IMC: {imc_val} ({imc_cat})", size=11, color=ft.Colors.WHITE),
                            ),
                            make_delete_button(aid, anome),
                        ],
                    ),
                ),
            )
            lista.controls.append(linha)
        page.update()

    def confirmar_exclusao(_id, _nome):
        def fechar_confirmacao(confirmar=False):
            dlg_confirm.open = False
            page.update()
            if confirmar:
                del_aluno(_id)

        dlg_confirm = ft.AlertDialog(
            modal=True,
            title=ft.Text("Confirmar exclusão"),
            content=ft.Text(f"Tem certeza que deseja excluir o aluno '{_nome}'?\nTodas as sessões deste aluno também serão excluídas."),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: fechar_confirmacao(False)),
                ft.TextButton("Excluir", on_click=lambda e: fechar_confirmacao(True)),
            ],
        )
        page.dialog = dlg_confirm
        dlg_confirm.open = True
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
                    ft.Row([nome, data, altura, peso, ft.ElevatedButton("Salvar", icon=ft.Icons.SAVE, on_click=salvar)], alignment=ft.MainAxisAlignment.CENTER, spacing=10, run_spacing=10, wrap=True),
                    ft.Row([busca], alignment=ft.MainAxisAlignment.CENTER),
                    status,
                    ft.Container(content=lista, height=360, border=ft.border.all(1, ft.Colors.BLUE_200), border_radius=10, padding=6),
                ],
            )
        )
    )

    carregar()
