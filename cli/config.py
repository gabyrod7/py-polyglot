import os
from dotenv import load_dotenv, set_key

def get_config_dir() -> str:
    if 'APPDATA' in os.environ:
        config_home = os.environ['APPDATA']
    elif 'XDG_CONFIG_HOME' in os.environ:
        config_home = os.environ['XDG_CONFIG_HOME']
    else:
        config_home = os.path.join(os.environ['HOME'], '.config')
    return os.path.join(config_home, 'translate')

def get_config_path() -> str:
    config_home = get_config_dir()
    return os.path.join(config_home, 'config.env')

def load_config_file() -> bool:
    return load_dotenv(get_config_path())

def save_environment_variable(key: str, value: str) -> None:
    config_path = get_config_path()
    if not os.path.exists(config_path):
        os.makedirs(get_config_dir(), exist_ok=True)
        with open(config_path, 'w'):
            pass
        os.chmod(config_path, 0o0600)

    set_key(dotenv_path=config_path, key_to_set=key, value_to_set=value)
