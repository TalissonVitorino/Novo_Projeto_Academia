import flet as ft
from datetime import datetime
from app.ui.components import with_bg, set_appbar, snack
from app.db import get_conn
from app.utils import validar_data_brasil


def show_treino(page: ft.Page, on_back):
    page.clean()
    set_appbar(page, "Iniciar Treino – Checklist", ft.Colors.ORANGE_700, show_back=True, on_back=lambda e=None: on_back())

    # Responsividade simples
    is_small = (page.width or 0) <= 420

    busca_aluno = ft.TextField(label="Buscar aluno", prefix_icon=ft.Icons.SEARCH, expand=1)
    dd_aluno = ft.Dropdown(label="Aluno", width=200 if is_small else 300)
    dd_plano = ft.Dropdown(label="Plano", width=180 if is_small else 240)
    data_tf = ft.TextField(label="Data (DD/MM/YYYY)", width=120 if is_small else 140, value=datetime.now().strftime("%d/%m/%Y"), max_length=10)

    lista_check = ft.Column(scroll=ft.ScrollMode.AUTO, height=320)
    status = ft.Text("", color=ft.Colors.ORANGE_200)

    conn = get_conn()
    cur = conn.cursor()

    def load_alunos(f=""):
        dd_aluno.options.clear()
        if f:
            cur.execute("SELECT ID_ALUNO, NOME FROM ALUNO WHERE NOME LIKE ? ORDER BY NOME", (f"%{f}%",))
        else:
            cur.execute("SELECT ID_ALUNO, NOME FROM ALUNO ORDER BY NOME")
        rows = cur.fetchall()
        if not rows:
            status.value = "Nenhum aluno cadastrado. Cadastre em 'Alunos'."
            dd_aluno.value = None
            page.update()
            return
        for aid, an in rows:
            dd_aluno.options.append(ft.dropdown.Option(key=str(aid), text=f"{an} (ID {aid})"))
        dd_aluno.value = str(rows[0][0]) if rows else None
        page.update()

    def load_planos():
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
        cur.execute(
            """
            SELECT pe.ORDEM, e.ID_EXERCICIO, e.NOME, e.GRUPO, pe.SERIES, pe.REPS
            FROM PLANO_EXERCICIO pe
            JOIN EXERCICIO e ON e.ID_EXERCICIO = pe.ID_EXERCICIO
            WHERE pe.ID_PLANO=? ORDER BY pe.ORDEM
            """,
            (pid,),
        )
        rows = cur.fetchall()
        if not rows:
            status.value = "Este plano não possui exercícios. Adicione em 'Planos de Treino' (ícone de lista)."
            page.update(); return
        status.value = f"Exercícios: {len(rows)}"
        for ordem, eid, enome, egrupo, series, reps in rows:
            chk = ft.Checkbox(label=f"{ordem:02d} • {egrupo} – {enome} ({series}x{reps})")
            reps_tf = ft.TextField(label="Reps (média)", width=100 if is_small else 120)
            peso_tf = ft.TextField(label="Peso (médio)", width=100 if is_small else 120)
            series_tf = ft.TextField(label="Séries feitas", width=100 if is_small else 120)
            obs_tf = ft.TextField(label="Observações", expand=1)
            linha = ft.Card(
                elevation=1,
                content=ft.Container(
                    padding=8,
                    content=ft.Column(
                        spacing=8,
                        controls=[
                            chk,
                            ft.Row([series_tf, reps_tf, peso_tf, obs_tf], spacing=8, wrap=True, run_spacing=8),
                        ],
                    ),
                ),
            )
            linha._meta = {"id_exercicio": eid, "chk": chk, "series": series_tf, "reps": reps_tf, "peso": peso_tf, "obs": obs_tf}
            lista_check.controls.append(linha)
        page.update()

    def salvar_sessao(_):
        if not dd_aluno.value:
            snack(page, "Selecione o aluno.", True); return
        if not dd_plano.value:
            snack(page, "Selecione o plano.", True); return
        if not lista_check.controls:
            snack(page, "Nenhum exercício carregado. Selecione um plano com exercícios.", True); return
        ok, iso = validar_data_brasil(data_tf.value)
        if not ok:
            snack(page, "Data inválida.", True); data_tf.focus(); return
        # criar sessão
        try:
            cur.execute(
                "INSERT INTO SESSAO (ID_ALUNO, ID_PLANO, DATA_SESSAO) VALUES (?,?,?)",
                (int(dd_aluno.value), int(dd_plano.value), iso),
            )
            id_sessao = cur.lastrowid
            total = 0
            for card in lista_check.controls:
                m = getattr(card, "_meta", None)
                if not m:
                    continue
                feito = 1 if m["chk"].value else 0
                try:
                    s = int(m["series"].value) if m["series"].value else None
                    r = int(m["reps"].value) if m["reps"].value else None
                    # aceitar vírgula ou ponto para decimais
                    peso_str = m["peso"].value.strip() if m["peso"].value else ""
                    if peso_str:
                        peso_str = peso_str.replace(".", "").replace(",", ".") if peso_str.count(",") == 1 and peso_str.count(".") > 1 else peso_str.replace(",", ".")
                    p = float(peso_str) if peso_str else None
                except Exception:
                    conn.rollback()
                    snack(page, "Valores numéricos inválidos (séries/reps/peso).", True); return
                obs = (m["obs"].value or "").strip() or None
                cur.execute(
                    """
                    INSERT INTO SESSAO_ITEM (ID_SESSAO, ID_EXERCICIO, FEITO, SERIES_FEITAS, REPS_MEDIA, PESO_MEDIA, OBS)
                    VALUES (?,?,?,?,?,?,?)
                    """,
                    (id_sessao, m["id_exercicio"], feito, s, r, p, obs),
                )
                total += 1
            conn.commit()
            snack(page, f"Sessão registrada com {total} exercícios.")
            lista_check.controls.clear(); status.value = ""; page.update()
        except Exception as ex:
            conn.rollback()
            snack(page, f"Erro ao salvar sessão: {ex}", True)

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
                    ft.Row([busca_aluno, dd_aluno, dd_plano, data_tf], alignment=ft.MainAxisAlignment.CENTER, spacing=10, wrap=True, run_spacing=10),
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
