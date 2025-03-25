import os


def get_config_path():
    """
    Retorna o caminho do arquivo de configuração.
    Exemplo de uso: AppData\Inventario\config.json (no Windows)
    ou ~/.Inventario/config.json (no Linux).
    """
    base_dir = os.getenv("APPDATA") or os.path.expanduser("~")
    config_folder = os.path.join(base_dir, "Inventario")
    if not os.path.exists(config_folder):
        os.makedirs(config_folder)
    return os.path.join(config_folder, "config.json")
