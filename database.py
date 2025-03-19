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

def obter_conexao():
    try:
        conn = sqlite3.connect(NOME_DB, check_same_thread=False)
        conn.execute("PRAGMA journal_mode=WAL;")
        return conn
    except Exception as e:
        print("Erro ao conectar ao banco:", e)
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