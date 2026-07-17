import getpass
import os

import keyring
from dotenv import load_dotenv, set_key
from keyring.errors import KeyringError, NoKeyringError

SERVICE_NAME = "py-polyglot"
PROVIDER_SPECS: dict[str, dict[str, str]] = {
    "openai": {"model_env": "OPENAI_MODEL", "api_key_env": "OPENAI_API_KEY"},
    "anthropic": {"model_env": "ANTHROPIC_MODEL", "api_key_env": "ANTHROPIC_API_KEY"},
    "gemini": {"model_env": "GEMINI_MODEL", "api_key_env": "GEMINI_API_KEY"},
    "huggingface": {"model_env": "HF_MODEL", "api_key_env": "HF_TOKEN"},
}
SETTINGS_SPEC: dict[str, dict[str, bool]] = {
    "HF_MODEL": {"secret": False},
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
            print(
                f"Warning: could not get {key} to the system keyring. "
                f"You can save it in {get_config_file_path()} but this is not secure."
            )

    return None


def save_setting_to_config_file(key: str, value: str) -> None:
    config_path = get_config_file_path()
    if not os.path.exists(config_path):
        os.makedirs(get_config_dir(), exist_ok=True)
        with open(config_path, "w"):
            pass
        os.chmod(config_path, 0o0600)

    set_key(dotenv_path=config_path, key_to_set=key, value_to_set=value)


def save_setting(key: str, value: str) -> None:
    spec = SETTINGS_SPEC[key]

    if spec["secret"]:
        try:
            keyring.set_password(SERVICE_NAME, key, value)
        except (KeyringError, NoKeyringError):
            print(
                f"Warning: could not save {key} to the system keyring. "
                f"Saving it in {get_config_file_path()} instead."
            )
            save_setting_to_config_file(key, value)
    else:
        save_setting_to_config_file(key, value)

    os.environ[key] = value


def get_api_key_for_provider(provider: str) -> str | None:
    return get_setting(PROVIDER_SPECS[provider]["api_key_env"])


def get_model_ids_for_provider(provider: str) -> list[str]:
    api_key = get_api_key_for_provider(provider)

    match provider:
        case "huggingface":
            from huggingface_hub import list_models as list_huggingface_models

            return [
                model.id
                for model in list_huggingface_models(
                    author="Helsinki-NLP",
                    token=api_key,
                )
            ]

        case "openai":
            from openai import OpenAI

            client = OpenAI(api_key=api_key)
            return [model.id for model in client.models.list().data]

        case "anthropic":
            from anthropic import Anthropic

            client = Anthropic(api_key=api_key)
            return [model.id for model in client.models.list().data]

        case "gemini":
            from google import genai

            client = genai.Client(api_key=api_key)
            return [
                model.name
                for model in client.models.list()
                if "generateContent" in model.supported_actions
            ]

        case _:
            raise NotImplementedError(
                f"Model configuration for provider {provider} is not implemented."
            )


def list_models() -> None:
    provider = get_setting("PROVIDER")
    if provider not in PROVIDER_SPECS:
        raise NotImplementedError(
            f"Model configuration for provider {provider} is not implemented."
        )

    print(f"{provider} was identified as the model provider.")
    print("You can choose among the following models:")
    for model_id in get_model_ids_for_provider(provider):
        print(model_id)


def set_model_name(model_name: str) -> None:
    provider = get_setting("PROVIDER")
    if provider not in PROVIDER_SPECS:
        raise NotImplementedError(
            f"Model configuration for provider {provider} is not implemented."
        )

    if not model_name:
        model_name = input("Enter model name: ").strip()

    if provider == "huggingface" and "opus-mt_tiny" not in model_name:
        raise ValueError(
            f"The model name given is '{model_name}' but only the 'opus-mt_tiny' models are supported. Use 'run_local config --list_model_names' flag to find all supported models."
        )

    model_ids = get_model_ids_for_provider(provider)
    model_found = any(model_name == model_id for model_id in model_ids)
    if not model_found:
        raise ValueError(f"The model {model_name} is not provided by {provider}.")

    model_env = PROVIDER_SPECS[provider]["model_env"]
    save_setting(key=model_env, value=model_name)
    print(f"{model_env} has been set to {model_name}")


def set_provider(provider: str) -> None:
    if provider not in PROVIDER_SPECS:
        print(f"The provider {provider} is not supported. Please choose among the following model providers:")
        for i, prov in enumerate(PROVIDER_SPECS.keys(), start=1):
            print(f"{i}. {prov}")
        while provider not in PROVIDER_SPECS:
            provider = input("Enter provider: ")

    save_setting("PROVIDER", provider)
    print(f"PROVIDER set to {provider}")

def set_api_key() -> None:
    provider = get_setting(key="PROVIDER")
    if provider not in PROVIDER_SPECS:
        print(f"The provider {provider} is not supported. Please choose among the following model providers:")
        for i, prov in enumerate(PROVIDER_SPECS.keys(), start=1):
            print(f"{i}. {prov}")
        while provider not in PROVIDER_SPECS:
            provider = input("Enter provider: ")

    api_key = getpass.getpass(f"Enter API key or token for {provider}: ").strip()
    save_setting(key=PROVIDER_SPECS[provider]["api_key_env"], value=api_key)
    print(f"Save API for provider {provider}")


def configure_remote_provider(remote_provider: str) -> None:
    supported_providers = tuple(PROVIDER_SPECS.keys())

    if not remote_provider:
        print("Supported providers are:")
        for provider in supported_providers:
            print(provider)

        remote_provider = input("Enter provider: ")

    if remote_provider not in supported_providers:
        raise ValueError(
            f"The remote provider '{remote_provider}' is not supported. Choose one of: {', '.join(supported_providers)}"
        )

    save_setting(key="LLM_PROVIDER", value=remote_provider)
    print(f"LLM_PROVIDER set to {remote_provider}")


def configure_remote_model() -> None:
    remote_provider = get_configured_remote_provider()
    remote_api_key = get_setting(PROVIDER_SPECS[remote_provider]["api_key_env"])
    remote_model_name = get_setting(PROVIDER_SPECS[remote_provider]["model_env"])

    if remote_provider not in PROVIDER_SPECS:
        raise NotImplementedError(
            f"Model configuration for provider {remote_provider} is not implemented yet."
        )

    if not remote_api_key:
        configure_remote_api_key()
        remote_api_key = get_setting(PROVIDER_SPECS[remote_provider]["api_key_env"])

    if remote_model_name:
        print(
            f"The current model for the provider {remote_provider} is currently {remote_model_name}"
        )
        print("Confirm you want to change it by entering 1, otherwise press enter.")
        flag = input("Enter: ").strip()

        if flag != "1":
            return

    if remote_provider == "openai":
        from openai import OpenAI

        client = OpenAI(api_key=remote_api_key)
        model_ids = [model.id for model in client.models.list().data]

        print("OpenAI was identified as the LLM provider.")
        print("Choose among the following models:")
        for model_id in model_ids:
            print(model_id)

    elif remote_provider == "anthropic":
        from anthropic import Anthropic

        client = Anthropic(api_key=remote_api_key)
        model_ids = [model.id for model in client.models.list().data]

        print("Anthropic was identified as the LLM provider.")
        print("Choose among the following models:")
        for model_id in model_ids:
            print(model_id)

    elif remote_provider == "gemini":
        from google import genai

        client = genai.Client(api_key=remote_api_key)
        model_ids = [
            model.name
            for model in client.models.list()
            if "generateContent" in model.supported_actions
        ]

        print("Gemini was identified as the LLM provider.")
        print("Choose among the following models:")
        for model_id in model_ids:
            print(model_id)

    remote_model_name = ""
    while remote_model_name not in model_ids:
        remote_model_name = input("Input model name: ").strip()

    model_env = PROVIDER_SPECS[remote_provider]["model_env"]
    save_setting(key=model_env, value=remote_model_name)
    print(f"{model_env} has been set to {remote_model_name}")

