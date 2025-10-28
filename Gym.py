import flet as ft
from datetime import datetime

# Centralized config and utilities
from app.db import get_conn, init_db
from app.config import Theme
from app.utils import validar_data_brasil, sqlite_para_brasileiro, calcular_imc


# =============== UTILITÁRIOS ===============
# Utilitários foram movidos para app.utils

# =============== APLICATIVO ===============

def main(page: ft.Page):
    init_db()
    page.title = "Checklist de Treino (Academia)"
    page.theme_mode = Theme.THEME_MODE
    page.window_width = Theme.WINDOW_WIDTH
    page.window_height = Theme.WINDOW_HEIGHT

    # ---------- Helper: fundo em gradiente ----------
    def with_bg(content, colors=None):
        return ft.Container(
            expand=True,
            padding=20,
            gradient=ft.LinearGradient(
                begin=ft.alignment.top_left,
                end=ft.alignment.bottom_right,
                colors=colors or Theme.BG_GRADIENT
            ),
            content=ft.Container(alignment=ft.alignment.center, content=content),
        )

    conn = get_conn()
    cur = conn.cursor()

    # ---------- Helper: AppBar com botão Voltar persistente ----------
    current_back_handler = None

    def set_appbar(title: str, bgcolor=None, show_back: bool = False, on_back=None):
        nonlocal current_back_handler
        if show_back:
            current_back_handler = on_back or go_home
            leading = ft.IconButton(
                icon=ft.Icons.ARROW_BACK,
                tooltip="Voltar",
                on_click=lambda e: current_back_handler(e),
            )
        else:
            current_back_handler = None
            leading = None
        page.appbar = ft.AppBar(
            leading=leading,
            title=ft.Text(title),
            center_title=True,
            bgcolor=bgcolor,
        )
        # Acessibilidade: tecla Esc volta quando disponível
        def _on_kb(ev: ft.KeyboardEvent):
            if ev.key == "Escape" and current_back_handler:
                try:
                    current_back_handler(ev)
                except Exception:
                    pass
        page.on_keyboard_event = _on_kb
        page.update()

    def contagem():
        cur.execute("SELECT COUNT(*) FROM ALUNO;"); a = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM PLANO;"); p = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM SESSAO;"); s = cur.fetchone()[0]
        return a, p, s

    # ---------------- Home ----------------
    def go_home(_=None):
        page.clean()
        a, p, s = contagem()
        set_appbar("Checklist de Treino", ft.Colors.BLUE_GREY_800, show_back=False)

        card = ft.Card(
            content=ft.Container(
                padding=40,
                content=ft.Column(
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=18,
                    controls=[
                        ft.Text("Academia – Dashboard", size=28, weight=ft.FontWeight.BOLD),
                        ft.Divider(),
                        ft.Row(
                            alignment=ft.MainAxisAlignment.CENTER,
                            spacing=30,
                            controls=[
                                ft.Text(f"Alunos: {a}", size=16, color=ft.Colors.BLUE_300),
                                ft.Text(f"Planos: {p}", size=16, color=ft.Colors.GREEN_300),
                                ft.Text(f"Sessões: {s}", size=16, color=ft.Colors.ORANGE_300),
                            ],
                        ),
                        ft.Container(height=12),
                        ft.Text("CADASTROS", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_400),
                        ft.Row(
                            alignment=ft.MainAxisAlignment.CENTER, spacing=14,
                            controls=[
                                ft.ElevatedButton("Alunos", icon=ft.Icons.PERSON, width=220,
                                                  on_click=lambda e: tela_alunos(),
                                                  style=ft.ButtonStyle(bgcolor=Theme.SECONDARY, color=ft.Colors.WHITE)),
                                ft.ElevatedButton("Exercícios", icon=ft.Icons.FITNESS_CENTER, width=220,
                                                  on_click=lambda e: tela_exercicios(),
                                                  style=ft.ButtonStyle(bgcolor=Theme.PRIMARY, color=ft.Colors.WHITE)),
                                ft.ElevatedButton("Planos de Treino", icon=ft.Icons.VIEW_LIST, width=220,
                                                  on_click=lambda e: tela_planos(),
                                                  style=ft.ButtonStyle(bgcolor=ft.Colors.PURPLE_600, color=ft.Colors.WHITE)),
                            ],
                        ),
                        ft.Container(height=16),
                        ft.Text("TREINO", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.ORANGE_400),
                        ft.Row(
                            alignment=ft.MainAxisAlignment.CENTER, spacing=14,
                            controls=[
                                ft.ElevatedButton("Iniciar Treino (Checklist)", icon=ft.Icons.PLAY_ARROW, width=260,
                                                  on_click=lambda e: tela_iniciar_treino(),
                                                  style=ft.ButtonStyle(bgcolor=ft.Colors.ORANGE_600, color=ft.Colors.WHITE)),
                                ft.ElevatedButton("Relatório de Sessões", icon=ft.Icons.ANALYTICS, width=220,
                                                  on_click=lambda e: tela_relatorio_sessoes(),
                                                  style=ft.ButtonStyle(bgcolor=ft.Colors.BLUE_GREY_600, color=ft.Colors.WHITE)),
                            ],
                        ),
                    ],
                ),
            ),
            elevation=8,
        )
        page.add(with_bg(ft.Container(content=card, alignment=ft.alignment.center, padding=20)))

    # ---------------- Alunos ----------------
    def tela_alunos():
        page.clean()
        set_appbar("Alunos", ft.Colors.GREEN_700, show_back=True, on_back=go_home)

        nome = ft.TextField(label="Nome do Aluno", width=360)
        data = ft.TextField(label="Nascimento (DD/MM/YYYY)", width=180, max_length=10)
        altura = ft.TextField(label="Altura (m) – opcional", width=150, hint_text="ex.: 1.75")

        busca = ft.TextField(label="Buscar", prefix_icon=ft.Icons.SEARCH, width=540)
        status = ft.Text("", color=ft.Colors.BLUE_200)
        lista = ft.Column(spacing=6, scroll=ft.ScrollMode.AUTO)

        def validar_data(_):
            ok, _ = validar_data_brasil(data.value)
            data.error_text = None if ok else "Data inválida"
            page.update()

        data.on_blur = validar_data

        def salvar(_):
            if not (nome.value or "").strip():
                snack("Informe o nome do aluno.", error=True); nome.focus(); return
            ok, iso = validar_data_brasil(data.value)
            # print iso for logging
            if not ok:
                snack("Data inválida (DD/MM/YYYY).", error=True); data.focus(); return
            try:
                alt = float(altura.value) if altura.value else None
                if alt is not None and alt <= 0: raise ValueError
            except Exception:
                snack("Altura deve ser número positivo (ex.: 1.75).", error=True); altura.focus(); return
            cur.execute("INSERT INTO ALUNO (NOME, DATA_NASC, ALTURA_M) VALUES (?,?,?)", (nome.value.strip(), iso, alt))
            conn.commit()
            snack("Aluno cadastrado!")
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
                cur.execute("DELETE FROM ALUNO WHERE ID_ALUNO=?", (_id,))
                conn.commit()
                snack("Aluno removido.")
                carregar(busca.value)
            except Exception as ex:
                snack(f"Erro: {ex}", error=True)

        def snack(msg, error=False):
            page.snack_bar = ft.SnackBar(ft.Text(msg), bgcolor=ft.Colors.RED_400 if error else ft.Colors.GREEN_600)
            page.snack_bar.open = True
            page.update()

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

    # ---------------- Exercícios ----------------
    def tela_exercicios():
        page.clean()
        set_appbar("Exercícios", ft.Colors.BLUE_700, show_back=True, on_back=go_home)

        nome = ft.TextField(label="Nome do exercício", width=360)
        grupo = ft.TextField(label="Grupo muscular", width=220, hint_text="Peito, Costas, Pernas…")
        busca = ft.TextField(label="Buscar", prefix_icon=ft.Icons.SEARCH, width=540)
        status = ft.Text("", color=ft.Colors.BLUE_200)
        lista = ft.Column(spacing=6, scroll=ft.ScrollMode.AUTO)

        def salvar(_):
            if not (nome.value or "").strip() or not (grupo.value or "").strip():
                snack("Preencha nome e grupo.", True); return
            cur.execute("INSERT INTO EXERCICIO (NOME, GRUPO) VALUES (?,?)", (nome.value.strip(), grupo.value.strip()))
            conn.commit(); snack("Exercício criado.")
            nome.value = ""; grupo.value = ""; page.update()
            carregar(busca.value)

        def carregar(filtro=""):
            lista.controls.clear()
            if filtro:
                cur.execute("SELECT ID_EXERCICIO, NOME, GRUPO FROM EXERCICIO WHERE NOME LIKE ? OR GRUPO LIKE ? ORDER BY GRUPO, NOME",
                            (f"%{filtro}%", f"%{filtro}%"))
            else:
                cur.execute("SELECT ID_EXERCICIO, NOME, GRUPO FROM EXERCICIO ORDER BY GRUPO, NOME")
            rows = cur.fetchall()
            status.value = f"Total: {len(rows)}" if rows else "Nenhum exercício."
            for eid, enome, egrupo in rows:
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
                                    ft.IconButton(icon=ft.Icons.DELETE, icon_color=ft.Colors.RED_400,
                                                  tooltip="Excluir", on_click=lambda e, _id=eid: del_exercicio(_id)),
                                ],
                            ),
                        ),
                    )
                )
            page.update()

        def del_exercicio(_id):
            try:
                cur.execute("DELETE FROM EXERCICIO WHERE ID_EXERCICIO=?", (_id,))
                conn.commit(); snack("Exercício removido."); carregar(busca.value)
            except Exception as ex:
                snack(f"Erro: {ex}", True)

        def snack(msg, error=False):
            page.snack_bar = ft.SnackBar(ft.Text(msg), bgcolor=ft.Colors.RED_400 if error else ft.Colors.GREEN_600)
            page.snack_bar.open = True; page.update()

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
                        ft.Row([nome, grupo, ft.ElevatedButton("Salvar", icon=ft.Icons.SAVE, on_click=salvar)], alignment=ft.MainAxisAlignment.CENTER),
                        ft.Row([busca], alignment=ft.MainAxisAlignment.CENTER),
                        status,
                        ft.Container(content=lista, height=400, border=ft.border.all(1, ft.Colors.BLUE_200), border_radius=10, padding=6),
                    ],
                )
            )
        )
        carregar()

    # ---------------- Planos ----------------
    def tela_planos():
        page.clean()
        set_appbar("Planos de Treino", ft.Colors.PURPLE_700, show_back=True, on_back=go_home)

        nome_plano = ft.TextField(label="Nome do plano (ex.: Treino A)", width=260)
        busca = ft.TextField(label="Buscar plano", prefix_icon=ft.Icons.SEARCH, width=360)
        status = ft.Text("", color=ft.Colors.BLUE_200)
        lista = ft.Column(spacing=6, scroll=ft.ScrollMode.AUTO)

        def salvar(_):
            nome = (nome_plano.value or "").strip()
            if not nome:
                snack("Informe o nome do plano.", True); nome_plano.focus(); return
            try:
                cur.execute("INSERT INTO PLANO (NOME) VALUES (?)", (nome,))
                conn.commit(); snack("Plano criado.")
                nome_plano.value = ""; page.update()
                carregar(busca.value)
            except Exception as ex:
                snack(f"Erro ao criar plano: {ex}", True)

        def carregar(filtro=""):
            lista.controls.clear()
            if filtro:
                cur.execute("SELECT ID_PLANO, NOME FROM PLANO WHERE NOME LIKE ? ORDER BY NOME", (f"%{filtro}%",))
            else:
                cur.execute("SELECT ID_PLANO, NOME FROM PLANO ORDER BY NOME")
            rows = cur.fetchall()
            status.value = f"Total: {len(rows)}" if rows else "Nenhum plano."
            for pid, pnome in rows:
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
                                    ft.Row(spacing=0, controls=[
                                        ft.IconButton(icon=ft.Icons.PLAYLIST_ADD, tooltip="Editar exercícios do plano",
                                                      on_click=lambda e, _id=pid, _nome=pnome: editar_plano_exercicios(_id, _nome)),
                                        ft.IconButton(icon=ft.Icons.DELETE, icon_color=ft.Colors.RED_400,
                                                      tooltip="Excluir plano", on_click=lambda e, _id=pid: del_plano(_id)),
                                    ]),
                                ],
                            ),
                        ),
                    )
                )
            page.update()

        def del_plano(_id):
            try:
                cur.execute("DELETE FROM PLANO WHERE ID_PLANO=?", (_id,))
                conn.commit(); snack("Plano removido."); carregar(busca.value)
            except Exception as ex:
                snack(f"Erro: {ex}", True)

        def snack(msg, error=False):
            page.snack_bar = ft.SnackBar(ft.Text(msg), bgcolor=ft.Colors.RED_400 if error else ft.Colors.GREEN_600)
            page.snack_bar.open = True; page.update()

        def editar_plano_exercicios(_id_plano, _nome):
            dialog = ft.AlertDialog(modal=True)
            page.overlay.append(dialog)

            lista_itens = ft.Column(scroll=ft.ScrollMode.AUTO, height=280)
            ex_dd = ft.Dropdown(label="Exercício", width=360)
            series_tf = ft.TextField(label="Séries", width=90)
            reps_tf = ft.TextField(label="Reps", width=90)
            ordem_tf = ft.TextField(label="Ordem", width=90)

            def load_exercicios():
                ex_dd.options.clear()
                cur.execute("SELECT ID_EXERCICIO, NOME, GRUPO FROM EXERCICIO ORDER BY GRUPO, NOME")
                for eid, en, gr in cur.fetchall():
                    ex_dd.options.append(ft.dropdown.Option(key=str(eid), text=f"{gr} - {en}"))
                page.update()

            def load_itens():
                lista_itens.controls.clear()
                cur.execute("""
                    SELECT pe.ORDEM, e.NOME, e.GRUPO, pe.SERIES, pe.REPS, e.ID_EXERCICIO
                    FROM PLANO_EXERCICIO pe
                    JOIN EXERCICIO e ON e.ID_EXERCICIO = pe.ID_EXERCICIO
                    WHERE pe.ID_PLANO=? ORDER BY pe.ORDEM
                """, (_id_plano,))
                rows = cur.fetchall()
                if not rows:
                    lista_itens.controls.append(ft.Text("Nenhum exercício no plano.", italic=True))
                else:
                    for ordem, enome, egrupo, series, reps, eid in rows:
                        lista_itens.controls.append(
                            ft.Card(
                                elevation=1,
                                content=ft.Container(
                                    padding=8,
                                    content=ft.Row(
                                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                        controls=[
                                            ft.Text(f"{ordem:02d}", width=50, weight=ft.FontWeight.BOLD),
                                            ft.Text(f"{egrupo} - {enome}", expand=True),
                                            ft.Text(f"{series} x {reps}", width=110),
                                            ft.IconButton(icon=ft.Icons.DELETE, icon_color=ft.Colors.RED_400,
                                                          tooltip="Remover", on_click=lambda e, _eid=eid: rm_item(_eid)),
                                        ],
                                    ),
                                ),
                            )
                        )
                page.update()

            def rm_item(_eid):
                cur.execute("DELETE FROM PLANO_EXERCICIO WHERE ID_PLANO=? AND ID_EXERCICIO=?", (_id_plano, _eid))
                conn.commit(); load_itens()

            def add_item(_):
                if not ex_dd.value or not series_tf.value or not reps_tf.value or not ordem_tf.value:
                    snack("Preencha exercício, séries, reps e ordem.", True); return
                try:
                    eid = int(ex_dd.value); s = int(series_tf.value); r = int(reps_tf.value); o = int(ordem_tf.value)
                    if s <= 0 or r <= 0 or o <= 0: raise ValueError
                except Exception:
                    snack("Use números positivos em séries/reps/ordem.", True); return
                cur.execute("""
                    INSERT OR REPLACE INTO PLANO_EXERCICIO (ID_PLANO, ID_EXERCICIO, ORDEM, SERIES, REPS)
                    VALUES (?,?,?,?,?)
                """, (_id_plano, eid, o, s, r))
                conn.commit()
                series_tf.value = ""; reps_tf.value = ""; ordem_tf.value = ""; page.update()
                load_itens()

            def close_dialog():
                dialog.open = False
                page.update()
                carregar(busca.value)

            dialog.content = ft.Container(
                width=720,
                padding=16,
                content=ft.Column(
                    spacing=12,
                    controls=[
                        ft.Text(f"Editar Plano: {_nome}", size=18, weight=ft.FontWeight.BOLD),
                        ft.Row([ex_dd, series_tf, reps_tf, ordem_tf, ft.ElevatedButton("Adicionar", icon=ft.Icons.ADD, on_click=add_item)],
                               alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ft.Divider(),
                        lista_itens,
                        ft.Row(alignment=ft.MainAxisAlignment.END, controls=[ft.TextButton("Fechar", on_click=lambda e: close_dialog())]),
                    ],
                ),
            )

            dialog.open = True
            page.update()
            load_exercicios(); load_itens()

        # atalhos de teclado
        nome_plano.on_submit = salvar
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
                        ft.Row([nome_plano, ft.ElevatedButton("Criar", icon=ft.Icons.SAVE, on_click=salvar)], alignment=ft.MainAxisAlignment.CENTER),
                        ft.Row([busca], alignment=ft.MainAxisAlignment.CENTER),
                        status,
                        ft.Container(content=lista, height=400, border=ft.border.all(1, ft.Colors.PURPLE_200), border_radius=10, padding=6),
                    ],
                )
            )
        )
        carregar()

    # ---------------- Iniciar Treino (Checklist) ----------------
    def tela_iniciar_treino():
        page.clean()
        set_appbar("Iniciar Treino – Checklist", ft.Colors.ORANGE_700, show_back=True, on_back=go_home)

        busca_aluno = ft.TextField(label="Buscar aluno", width=360, prefix_icon=ft.Icons.SEARCH)
        dd_aluno = ft.Dropdown(label="Aluno", width=360)
        dd_plano = ft.Dropdown(label="Plano", width=260)
        data_tf = ft.TextField(label="Data (DD/MM/YYYY)", width=180, value=datetime.now().strftime("%d/%m/%Y"), max_length=10)

        lista_check = ft.Column(scroll=ft.ScrollMode.AUTO, height=320)
        status = ft.Text("", color=ft.Colors.ORANGE_200)

        def load_alunos(f=""):
            """Carrega alunos e seleciona automaticamente o 1º resultado encontrado."""
            dd_aluno.options.clear()
            if f:
                cur.execute("SELECT ID_ALUNO, NOME FROM ALUNO WHERE NOME LIKE ? ORDER BY NOME", (f"%{f}%",))
            else:
                cur.execute("SELECT ID_ALUNO, NOME FROM ALUNO ORDER BY NOME")
            rows = cur.fetchall()
            for aid, an in rows:
                dd_aluno.options.append(ft.dropdown.Option(key=str(aid), text=f"{an} (ID {aid})"))
            dd_aluno.value = str(rows[0][0]) if rows else None
            page.update()

        def load_planos():
            """Carrega planos, seleciona o 1º e tenta carregar a checklist."""
            dd_plano.options.clear()
            cur.execute("SELECT ID_PLANO, NOME FROM PLANO ORDER BY NOME")
            rows = cur.fetchall()
            for pid, pn in rows:
                dd_plano.options.append(ft.dropdown.Option(key=str(pid), text=pn))
            dd_plano.value = str(rows[0][0]) if rows else None
            page.update()

            if dd_plano.value:
                load_checklist()
            else:
                status.value = "Nenhum plano cadastrado. Crie um em 'Planos de Treino'."
                page.update()

        def load_checklist():
            lista_check.controls.clear()

            if not dd_plano.value:
                status.value = "Selecione um plano."
                page.update(); return

            pid = int(dd_plano.value)
            cur.execute("""
                SELECT pe.ORDEM, e.ID_EXERCICIO, e.NOME, e.GRUPO, pe.SERIES, pe.REPS
                FROM PLANO_EXERCICIO pe
                JOIN EXERCICIO e ON e.ID_EXERCICIO = pe.ID_EXERCICIO
                WHERE pe.ID_PLANO=? ORDER BY pe.ORDEM
            """, (pid,))
            rows = cur.fetchall()

            if not rows:
                status.value = "Este plano não possui exercícios. Adicione em 'Planos de Treino' (ícone de lista)."
                page.update(); return

            status.value = f"Exercícios: {len(rows)}"

            for ordem, eid, enome, egrupo, series, reps in rows:
                chk = ft.Checkbox(label=f"{ordem:02d} • {egrupo} – {enome} ({series}x{reps})")
                reps_tf = ft.TextField(label="Reps (média)", width=120)
                peso_tf = ft.TextField(label="Peso (médio)", width=120)
                series_tf = ft.TextField(label="Séries feitas", width=120)
                obs_tf = ft.TextField(label="Observações", width=240)

                linha = ft.Card(
                    elevation=1,
                    content=ft.Container(
                        padding=8,
                        content=ft.Column(
                            spacing=8,
                            controls=[
                                chk,
                                ft.Row([series_tf, reps_tf, peso_tf, obs_tf], spacing=8),
                            ],
                        ),
                    ),
                )
                linha._meta = {"id_exercicio": eid, "chk": chk, "series": series_tf, "reps": reps_tf, "peso": peso_tf, "obs": obs_tf}
                lista_check.controls.append(linha)

            page.update()

        def salvar_sessao(_):
            if not dd_aluno.value: snack("Selecione o aluno.", True); return
            if not dd_plano.value: snack("Selecione o plano.", True); return
            ok, iso = validar_data_brasil(data_tf.value)
            if not ok: snack("Data inválida.", True); return

            # criar sessão
            cur.execute("INSERT INTO SESSAO (ID_ALUNO, ID_PLANO, DATA_SESSAO) VALUES (?,?,?)",
                        (int(dd_aluno.value), int(dd_plano.value), iso))
            id_sessao = cur.lastrowid

            total = 0
            for card in lista_check.controls:
                m = getattr(card, "_meta", None)
                if not m: continue
                feito = 1 if m["chk"].value else 0
                try:
                    s = int(m["series"].value) if m["series"].value else None
                    r = int(m["reps"].value) if m["reps"].value else None
                    p = float(m["peso"].value) if m["peso"].value else None
                except Exception:
                    snack("Valores numéricos inválidos (séries/reps/peso).", True); return
                obs = (m["obs"].value or "").strip() or None

                cur.execute("""
                    INSERT INTO SESSAO_ITEM (ID_SESSAO, ID_EXERCICIO, FEITO, SERIES_FEITAS, REPS_MEDIA, PESO_MEDIA, OBS)
                    VALUES (?,?,?,?,?,?,?)
                """, (id_sessao, m["id_exercicio"], feito, s, r, p, obs))
                total += 1

            conn.commit()
            snack(f"Sessão registrada com {total} exercícios.")
            lista_check.controls.clear(); status.value = ""; page.update()

        def snack(msg, error=False):
            page.snack_bar = ft.SnackBar(ft.Text(msg), bgcolor=ft.Colors.RED_400 if error else ft.Colors.GREEN_600)
            page.snack_bar.open = True; page.update()

        busca_aluno.on_change = lambda e: load_alunos(busca_aluno.value)
        busca_aluno.on_submit = lambda e: load_alunos(busca_aluno.value)
        dd_plano.on_change = lambda e: load_checklist()

        page.add(
            with_bg(
                ft.Column(
                    spacing=12,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Text("Iniciar Treino (Checklist)", size=22, weight=ft.FontWeight.BOLD),
                        ft.Divider(),
                        ft.Row([busca_aluno, dd_aluno, dd_plano, data_tf], alignment=ft.MainAxisAlignment.CENTER, spacing=10),
                        status,
                        ft.Container(content=lista_check, height=360, border=ft.border.all(1, ft.Colors.ORANGE_200), border_radius=10, padding=6),
                        ft.Row(
                            alignment=ft.MainAxisAlignment.CENTER,
                            spacing=12,
                            controls=[
                                ft.ElevatedButton("Carregar exercícios", icon=ft.Icons.LIST, on_click=lambda e: load_checklist()),
                                ft.ElevatedButton("Salvar sessão", icon=ft.Icons.SAVE, on_click=salvar_sessao),
                            ],
                        ),
                    ],
                )
            )
        )
        load_alunos(); load_planos()

    # ---------------- Relatório de Sessões ----------------
    def tela_relatorio_sessoes():
        page.clean()
        set_appbar("Relatório de Sessões", ft.Colors.BLUE_GREY_700, show_back=True, on_back=go_home)

        busca_aluno = ft.TextField(label="Filtrar por nome do aluno", prefix_icon=ft.Icons.SEARCH, width=480)
        lista = ft.Column(spacing=6, scroll=ft.ScrollMode.AUTO)
        status = ft.Text("", color=ft.Colors.BLUE_200)

        def carregar(f=""):
            lista.controls.clear()
            if f:
                cur.execute("""
                    SELECT s.ID_SESSAO, s.DATA_SESSAO, a.NOME, p.NOME
                    FROM SESSAO s
                    JOIN ALUNO a ON a.ID_ALUNO = s.ID_ALUNO
                    JOIN PLANO p ON p.ID_PLANO = s.ID_PLANO
                    WHERE a.NOME LIKE ?
                    ORDER BY s.DATA_SESSAO DESC, s.ID_SESSAO DESC
                """, (f"%{f}%",))
            else:
                cur.execute("""
                    SELECT s.ID_SESSAO, s.DATA_SESSAO, a.NOME, p.NOME
                    FROM SESSAO s
                    JOIN ALUNO a ON a.ID_ALUNO = s.ID_ALUNO
                    JOIN PLANO p ON p.ID_PLANO = s.ID_PLANO
                    ORDER BY s.DATA_SESSAO DESC, s.ID_SESSAO DESC
                """)
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
                                            ft.IconButton(icon=ft.Icons.DELETE, icon_color=ft.Colors.RED_400,
                                                          tooltip="Excluir sessão", on_click=lambda e, _sid=sid: excluir(_sid)),
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

            cur.execute("""
                SELECT e.NOME, e.GRUPO, si.FEITO, si.SERIES_FEITAS, si.REPS_MEDIA, si.PESO_MEDIA, si.OBS
                FROM SESSAO_ITEM si
                JOIN EXERCICIO e ON e.ID_EXERCICIO = si.ID_EXERCICIO
                WHERE si.ID_SESSAO=? ORDER BY si.ID_ITEM
            """, (_sid,))
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

            dialog.content = ft.Container(
                width=720,
                padding=16,
                content=ft.Column(spacing=12, controls=[
                    ft.Text(f"Sessão #{_sid}", size=18, weight=ft.FontWeight.BOLD),
                    corpo,
                    ft.Row(alignment=ft.MainAxisAlignment.END, controls=[ft.TextButton("Fechar", on_click=lambda e: close_dialog())])
                ])
            )

            def close_dialog():
                dialog.open = False; page.update()

            dialog.open = True; page.update()

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

    # Helpers
    def snack(msg, error=False):
        page.snack_bar = ft.SnackBar(ft.Text(msg), bgcolor=ft.Colors.RED_400 if error else ft.Colors.GREEN_600)
        page.snack_bar.open = True; page.update()

    # Inicial
    go_home()

ft.app(target=main)
