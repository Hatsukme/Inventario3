import os
import sqlite3
import shutil
import datetime
import zipfile
import json

# Caminho padrão: o banco de dados na mesma pasta do executável
NOME_DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "inventario.db")
# Diretório padrão de imagens, relativo ao banco
IMAGES_FOLDER = os.path.join(os.path.dirname(NOME_DB), "imagens_originais")

def set_database_path(path):
    """Define o caminho do banco e atualiza o diretório de imagens correspondente."""
    global NOME_DB, IMAGES_FOLDER
    NOME_DB = path
    IMAGES_FOLDER = os.path.join(os.path.dirname(path), "imagens_originais")

MODO_CONEXAO = "rw"

def obter_conexao():
    global MODO_CONEXAO
    try:
        # Tenta abrir em modo leitura-escrita
        conn = sqlite3.connect(NOME_DB, timeout=5, check_same_thread=False)
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("BEGIN IMMEDIATE;")
        conn.commit()
        MODO_CONEXAO = "rw"
        print("Conexão em modo leitura-escrita estabelecida.")
        return conn
    except sqlite3.OperationalError as e:
        if "database is locked" in str(e):
            print("Banco de dados bloqueado, abrindo em modo somente leitura.")
            conn = sqlite3.connect(f"file:{NOME_DB}?mode=ro", uri=True, check_same_thread=False)
            MODO_CONEXAO = "ro"
            return conn
        else:
            raise

def verificar_ou_criar_db():
    novo_db = not os.path.exists(NOME_DB)
    try:
        with obter_conexao() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS directories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    parent_id INTEGER,
                    note TEXT,
                    FOREIGN KEY(parent_id) REFERENCES directories(id)
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    responsible TEXT,
                    quantity INTEGER,
                    description TEXT,
                    image_path TEXT,
                    directory_id INTEGER,
                    note TEXT,
                    FOREIGN KEY(directory_id) REFERENCES directories(id)
                )
            """)
            if novo_db:
                cursor.execute("INSERT INTO directories (name, parent_id) VALUES (?, ?)", ("Equipamentos", None))
            conn.commit()
    except Exception as e:
        print("Erro ao criar/verificar banco de dados:", e)
        raise

def criar_pasta_imagens():
    """Cria a pasta para armazenar as imagens, se ela não existir."""
    if not os.path.exists(IMAGES_FOLDER):
        os.makedirs(IMAGES_FOLDER)