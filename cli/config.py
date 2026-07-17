import os

import keyring
from dotenv import load_dotenv, set_key
from keyring.errors import KeyringError, NoKeyringError

SERVICE_NAME = "py-polyglot"
SETTINGS_SPEC: dict[str, dict[str, bool]] = {
    "MODEL_NAME": {"secret": False},
    "PROVIDER": {"secret": False},
    "OPENAI_MODEL": {"secret": False},
    "ANTHROPIC_MODEL": {"secret": False},
    "GEMINI_MODEL": {"secret": False},
    "HF_TOKEN": {"secret": True},
    "OPENAI_API_KEY": {"secret": True},
    "ANTHROPIC_API_KEY": {"secret": True},
    "GEMINI_API_KEY": {"secret": True},
}


def get_config_dir() -> str:
    if "APPDATA" in os.environ:
        config_home = os.environ["APPDATA"]
    elif "XDG_CONFIG_HOME" in os.environ:
        config_home = os.environ["XDG_CONFIG_HOME"]
    else:
        config_home = os.path.join(os.environ["HOME"], ".config")
    return os.path.join(config_home, "py-polyglot")


def get_config_file_path() -> str:
    config_home = get_config_dir()
    return os.path.join(config_home, "config.env")


def load_config_file() -> bool:
    return load_dotenv(get_config_file_path())


def get_setting(key: str) -> str | None:
    spec = SETTINGS_SPEC[key]

    value = os.environ.get(key)
    if value:
        return value

    if spec["secret"]:
        try:
            return keyring.get_password(SERVICE_NAME, key)
        except (KeyringError, NoKeyringError) as e:
            raise RuntimeError(
                f"Could not read {key} from the system keyring. "
                "You can set it as an environment variable instead."
            ) from e

    return None


def save_setting(key: str, value: str) -> None:
    spec = SETTINGS_SPEC[key]

    if spec["secret"]:
        try:
            keyring.set_password(SERVICE_NAME, key, value)
        except (KeyringError, NoKeyringError) as e:
            raise RuntimeError(f"Could not save {key} to the system keyring.") from e
    else:
        config_path = get_config_file_path()
        if not os.path.exists(config_path):
            os.makedirs(get_config_dir(), exist_ok=True)
            with open(config_path, "w"):
                pass
            os.chmod(config_path, 0o0600)

        set_key(dotenv_path=config_path, key_to_set=key, value_to_set=value)

    os.environ[key] = value

def get_api_key_for_provider(provider: str) -> str:
    if provider == "HuggingFace":
        return "HF_TOKEN"
    elif provider == "openai":
        return "OPENAI_API_KEY"
    elif provider == "anthropic":
        return "ANTHROPIC_API_KEY"
    elif provider == "gemini":
        return "GEMINI_API_KEY"
    else:
        return ''

def list_models() -> None:
    provider = get_setting("PROVIDER")
    api_key = get_api_key_for_provider(provider)

    if provider not in ["HuggingFace", "openai", "anthropic", "gemini"]:
        raise NotImplementedError(
            f"Model configuration for provider {provider} is not implemented."
        )

    match provider:
        case "HuggingFace":
            from huggingface_hub import list_models

            model_list = list_models(author="Helsinki-NLP")
            for model in model_list:
                print(model.id)

        case "openai":
            from openai import OpenAI

            client = OpenAI(api_key=api_key)
            model_ids = [model.id for model in client.models.list().data]

            print("OpenAI was identified as the LLM provider.")
            print("You can choose among the following models:")
            for model_id in model_ids:
                print(model_id)


