import json
import os

from database import NOME_DB  # To get the DB directory


def get_notes_path():
    """Returns the path of the notes JSON stored in the same directory as the DB."""
    db_dir = os.path.dirname(NOME_DB)
    return os.path.join(db_dir, "notes.json")


def load_notes():
    """Loads and returns notes from the DB JSON. Returns an empty dict if not exists."""
    path = get_notes_path()
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print("Error loading notes from DB:", e)
    return {}


def save_notes(notes):
    """Saves the notes dictionary to the DB JSON file."""
    path = get_notes_path()
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(notes, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print("Error saving notes to DB:", e)


# Functions for warnings dialog configuration stored in AppData.
def get_appdata_config_path():
    """Returns the path for the configuration JSON in the user's AppData (or home) directory."""
    base_dir = os.getenv("APPDATA") or os.path.expanduser("~")
    config_folder = os.path.join(base_dir, "Inventory")
    if not os.path.exists(config_folder):
        os.makedirs(config_folder)
    return os.path.join(config_folder, "config.json")


def load_warnings_config():
    """Loads the warnings dialog configuration from the AppData config file."""
    config_path = get_appdata_config_path()
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            return config.get("warnings_dialog", {})
        except Exception as e:
            print("Error loading warnings config:", e)
    return {}


def save_warnings_config(warnings_config):
    """Saves the warnings dialog configuration into the AppData config file."""
    config_path = get_appdata_config_path()
    config = {}
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
        except:
            config = {}
    config["warnings_dialog"] = warnings_config
    try:
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4)
    except Exception as e:
        print("Error saving warnings config:", e)


# Also include the load_appdata_notes if needed:
def get_appdata_notes_path():
    """Returns the path for the notes JSON in AppData."""
    base_dir = os.getenv("APPDATA") or os.path.expanduser("~")
    config_folder = os.path.join(base_dir, "Inventory")
    if not os.path.exists(config_folder):
        os.makedirs(config_folder)
    return os.path.join(config_folder, "notes.json")


def load_appdata_notes():
    path = get_appdata_notes_path()
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print("Error loading appdata notes:", e)
    return {}


def get_directory_paths():
    """Queries all directories from the DB and returns a dict mapping directory id to its full path."""
    from database import obter_conexao
    paths = {}
    with obter_conexao() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, parent_id FROM directories")
        rows = cursor.fetchall()
    # Cria um dicionário com os dados dos diretórios.
    dirs = {row[0]: {"name": row[1], "parent": row[2]} for row in rows}

    def build_path(dir_id):
        d = dirs[dir_id]
        if d["parent"] is None:
            return d["name"]
        else:
            return build_path(d["parent"]) + "/" + d["name"]

    for d_id in dirs:
        paths[d_id] = build_path(d_id)
    return paths
