import sqlite3
from .config import DB_PATH


def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db():
    conn = get_conn()
    cur = conn.cursor()

    # ---- Núcleo
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS ALUNO (
            ID_ALUNO        INTEGER PRIMARY KEY AUTOINCREMENT,
            NOME            TEXT NOT NULL,
            DATA_NASC       TEXT NOT NULL,
            ALTURA_M        REAL,
            PESO_KG         REAL
        );
    """
    )

    # Migração: adicionar coluna PESO_KG se não existir
    try:
        cur.execute("SELECT PESO_KG FROM ALUNO LIMIT 1")
    except Exception:
        # Coluna não existe, adicionar
        cur.execute("ALTER TABLE ALUNO ADD COLUMN PESO_KG REAL")
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS EXERCICIO (
            ID_EXERCICIO    INTEGER PRIMARY KEY AUTOINCREMENT,
            NOME            TEXT NOT NULL,
            GRUPO           TEXT NOT NULL
        );
    """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS PLANO (
            ID_PLANO        INTEGER PRIMARY KEY AUTOINCREMENT,
            NOME            TEXT NOT NULL
        );
    """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS PLANO_EXERCICIO (
            ID_PLANO        INTEGER NOT NULL,
            ID_EXERCICIO    INTEGER NOT NULL,
            ORDEM           INTEGER NOT NULL,
            SERIES          INTEGER NOT NULL,
            REPS            INTEGER NOT NULL,
            PRIMARY KEY (ID_PLANO, ID_EXERCICIO),
            FOREIGN KEY (ID_PLANO) REFERENCES PLANO(ID_PLANO) ON DELETE CASCADE,
            FOREIGN KEY (ID_EXERCICIO) REFERENCES EXERCICIO(ID_EXERCICIO) ON DELETE RESTRICT
        );
    """
    )
    # ---- Sessão (treino do dia)
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS SESSAO (
            ID_SESSAO       INTEGER PRIMARY KEY AUTOINCREMENT,
            ID_ALUNO        INTEGER NOT NULL,
            ID_PLANO        INTEGER NOT NULL,
            DATA_SESSAO     TEXT NOT NULL,
            FOREIGN KEY (ID_ALUNO) REFERENCES ALUNO(ID_ALUNO) ON DELETE CASCADE,
            FOREIGN KEY (ID_PLANO) REFERENCES PLANO(ID_PLANO) ON DELETE CASCADE
        );
    """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS SESSAO_ITEM (
            ID_ITEM         INTEGER PRIMARY KEY AUTOINCREMENT,
            ID_SESSAO       INTEGER NOT NULL,
            ID_EXERCICIO    INTEGER NOT NULL,
            FEITO           INTEGER NOT NULL DEFAULT 0,
            SERIES_FEITAS   INTEGER,
            REPS_MEDIA      INTEGER,
            PESO_MEDIA      REAL,
            OBS             TEXT,
            FOREIGN KEY (ID_SESSAO) REFERENCES SESSAO(ID_SESSAO) ON DELETE CASCADE,
            FOREIGN KEY (ID_EXERCICIO) REFERENCES EXERCICIO(ID_EXERCICIO) ON DELETE RESTRICT
        );
    """
    )

    # Índices úteis
    cur.execute("CREATE INDEX IF NOT EXISTS idx_aluno_nome ON ALUNO (NOME);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_exercicio_nome ON EXERCICIO (NOME);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_plano_nome ON PLANO (NOME);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_sessao_data ON SESSAO (DATA_SESSAO DESC);")

    # Seed mínimo de exercícios se tabela estiver vazia
    cur.execute("SELECT COUNT(*) FROM EXERCICIO;")
    if cur.fetchone()[0] == 0:
        base_ex = [
            ("Supino reto", "Peito"),
            ("Crucifixo (halteres)", "Peito"),
            ("Remada curvada", "Costas"),
            ("Puxada na frente", "Costas"),
            ("Agachamento livre", "Pernas"),
            ("Leg press", "Pernas"),
            ("Desenvolvimento ombro", "Ombros"),
            ("Elevação lateral", "Ombros"),
            ("Rosca direta", "Bíceps"),
            ("Tríceps corda", "Tríceps"),
            ("Abdominal infra", "Core"),
        ]
        cur.executemany("INSERT INTO EXERCICIO (NOME, GRUPO) VALUES (?,?)", base_ex)

    conn.commit()
    conn.close()
