import os
import sqlite3
import shutil
import datetime
import zipfile
import json

# Constantes
NOME_DB = "inventario.db"
IMAGES_FOLDER = "imagens_originais"

def obter_conexao():
    """Retorna uma conexão com o banco de dados SQLite."""
    try:
        conn = sqlite3.connect(NOME_DB)
        return conn
    except Exception as e:
        print("Erro ao conectar ao banco:", e)
        raise

def verificar_ou_criar_db():
    """Verifica se o DB existe; se não, cria o banco e as tabelas necessárias."""
    novo_db = not os.path.exists(NOME_DB)
    try:
        with obter_conexao() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS directories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    parent_id INTEGER,
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
                    FOREIGN KEY(directory_id) REFERENCES directories(id)
                )
            """)
            # Se for um banco novo, insere um diretório inicial
            if novo_db:
                cursor.execute(
                    "INSERT INTO directories (name, parent_id) VALUES (?, ?)",
                    ("Equipamentos", None)
                )
            conn.commit()
    except Exception as e:
        print("Erro ao criar/verificar banco de dados:", e)
        raise

def criar_pasta_imagens():
    """Cria a pasta para armazenar as imagens, se ela não existir."""
    if not os.path.exists(IMAGES_FOLDER):
        os.makedirs(IMAGES_FOLDER)
