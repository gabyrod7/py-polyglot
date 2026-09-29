import getpass
import os
from dataclasses import dataclass
from pathlib import Path

import keyring
from dotenv import dotenv_values, set_key
from keyring.errors import KeyringError

from core.result import Result

@dataclass(repr=False)
class Setting:
    key: str
    value: str | None = None
    secret: bool = False
    environment_info: str = ""

    def __repr__(self) -> str:
        value = "<redacted>" if self.secret else self.value

        return (
            f"{type(self).__name__}("
            f"key={self.key!r}, "
            f"value={value!r}, "
            f"secret={self.secret!r})"
            f"environment_info={self.environment_info!r})"
        )




class Settings:
    def __init__(self):
        self.provider_name = Setting(
            "PROVIDER",
            value="huggingface",
            environment_info=("Provider to use (for example, huggingface or openai)."),
        )
        self.source_language = Setting(
            "SOURCE_LANGUAGE",
            value="German",
            environment_info="Language of the text to translate (for example, German).",
        )
        self.target_language = Setting(
            "TARGET_LANGUAGE",
            value="English",
            environment_info="Language to translate the text into (for example, English).",
        )
        self.hf_model = Setting(
            "HF_MODEL",
            value="Helsinki-NLP/opus-mt_tiny_deu-eng",
            environment_info="Hugging Face model ID to use for translations.",
        )
        self.hf_token = Setting(
            "HF_TOKEN",
            secret=True,
            environment_info="Access token used to authenticate with Hugging Face.",
        )
        self.hf_model_author = Setting(
            "HF_MODEL_AUTHOR",
            value="Helsinki-NLP",
            environment_info="Author or organization used to filter Hugging Face models.",
        )
        self.openai_model = Setting(
            "OPENAI_MODEL",
            value="gpt-5.6-luna",
            environment_info="OpenAI model ID to use for translations.",
        )
        self.openai_api_key = Setting(
            "OPENAI_API_KEY",
            secret=True,
            environment_info="API key used to authenticate with OpenAI.",
        )
        self.anthropic_model = Setting(
            "ANTHROPIC_MODEL",
            value="claude-haiku-4-5",
            environment_info="Anthropic model ID to use for translations.",
        )
        self.anthropic_api_key = Setting(
            "ANTHROPIC_API_KEY",
            secret=True,
            environment_info="API key used to authenticate with Anthropic.",
        )
        self.gemini_model = Setting(
            "GEMINI_MODEL",
            value="gemini-3.5-flash-lite",
            environment_info="Gemini model ID to use for translations.",
        )
        self.gemini_api_key = Setting(
            "GEMINI_API_KEY",
            secret=True,
            environment_info="API key used to authenticate with Gemini.",
        )
        self.verbose = Setting(
            "VERBOSE",
            value="False",
            environment_info=("Increase print messages."),
        )

        self.allowed_providers = {
            "openai": {"model": self.openai_model, "api_key": self.openai_api_key},
            "anthropic": {
                "model": self.anthropic_model,
                "api_key": self.anthropic_api_key,
            },
            "gemini": {"model": self.gemini_model, "api_key": self.gemini_api_key},
            "huggingface": {"model": self.hf_model, "api_key": self.hf_token},
        }

    def __repr__(self) -> str:
        values = ", ".join(
            f"{name}={setting!r}"
            for name, setting in vars(self).items()
            if isinstance(setting, Setting)
        )
        return (
            f"{type(self).__name__}("
            f"{values}, allowed_providers={list(self.allowed_providers)!r})"
        )


class SettingsManager:
    SERVICE_NAME = "py-polyglot"

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.allowed_languages = ["English", "German", "Spanish"]

        if not self.get_config_file_path().exists():
            self.get_config_dir().mkdir(parents=True, exist_ok=True)
            self.get_config_file_path().touch(mode=0o600)

    def load(self) -> Result:
        """Load all settings into the current Settings object."""
        config_file_dict = dotenv_values(self.get_config_file_path())

        for setting in vars(self.settings).values():
            if not isinstance(setting, Setting):
                continue

            result = self.load_setting(setting, config_file_dict)
            if not result.ok:
                return result

        return Result()

    def load_setting(
        self,
        setting: Setting,
        config_file_dict: dict[str, str | None],
    ) -> Result:
        if setting.key in os.environ:
            setting.value = os.environ[setting.key]
            return Result()

        if setting.secret:
            try:
                setting.value = keyring.get_password(
                    self.SERVICE_NAME,
                    setting.key,
                )
            except KeyringError:
                setting.value = None
                return Result(
                    error_code="KEYRING_READ_FAILED",
                    message=f"Could not read {setting.key} from the system keyring.",
                )

            return Result()

        if setting.key in config_file_dict:
            setting.value = config_file_dict.get(setting.key)

        return Result()

    def set_setting(self, setting: Setting, value: str) -> Result:
        if setting.secret:
            try:
                keyring.set_password(self.SERVICE_NAME, setting.key, value)
            except KeyringError:
                return Result(
                    error_code="KEYRING_WRITE_FAILED",
                    message=(
                        f"Could not set {setting.key} in the system keyring. "
                        "Previous password was not changed."
                    ),
                )
        else:
            set_key(
                dotenv_path=str(self.get_config_file_path()),
                key_to_set=setting.key,
                value_to_set=value,
            )

        setting.value = value
        return Result()

    #    def verify_settings(self):
    #        allowed_languages = ['English', 'German', 'Spanish']
    #
    #        if self.settings.source_language in allowed_languages:
    #            return Result()
    #        else:
    #            return Result(
    #                error_code="UNSOPPORTED_LANGUAGE",
    #                error_message=""
    #            )

    @classmethod
    def get_config_dir(cls) -> Path:
        if appdata := os.environ.get("APPDATA"):
            config_home = Path(appdata)
        elif xdg_config_home := os.environ.get("XDG_CONFIG_HOME"):
            config_home = Path(xdg_config_home)
        else:
            config_home = Path.home() / ".config"

        return config_home / cls.SERVICE_NAME

    @classmethod
    def get_config_file_path(cls) -> Path:
        return cls.get_config_dir() / "config.env"

    def get_selected_model(self) -> str:
        return self.settings.allowed_providers[self.settings.provider_name.value]["model"].value

    def set_api_key(self) -> Result:
        provider_name = self.settings.provider_name.value
        provider = self.settings.allowed_providers.get(provider_name or "")
        if provider is None:
            return Result(
                error_code="PROVIDER_NOT_SUPPORTED",
                message=f"The provider {provider_name} is not supported.",
            )

        api_key = getpass.getpass(
            f"Enter API key or token for {provider_name}: "
        ).strip()
        if not api_key:
            return Result(
                error_code="EMPTY_API_KEY",
                message="ERROR: Empty api key.",
            )

        result = self.set_setting(provider["api_key"], api_key)
        if not result.ok:
            return result

        print(f"Saved API key for provider {provider_name}")
        return Result()

    def set_language(self, language: str, to: str) -> Result:
        if not language:
            language = input("Enter language: ").strip()

        if language not in self.allowed_languages:
            return Result(
                error_code="BAD", message=f"ERROR: {language} not supported"
            )

        if to not in ("source", "target"):
            return Result(
                error_code="BAD",
                message=f"ERROR: {to} was proivded but only 'source' and 'target' are allowed",
            )

        lang = (
            self.settings.source_language
            if to == "source"
            else self.settings.target_language
        )

        self.set_setting(lang, language)
        print(f"{lang.key} has been set to {language}")
        return Result()

    def set_provider(self, provider_name: str) -> Result:
        result = self.set_setting(self.settings.provider_name, provider_name)
        if not result.ok:
            return result

        return Result()

    def set_model_name(self, model_name: str) -> Result:
        provider_name = self.settings.provider_name.value
        if provider_name not in self.settings.allowed_providers:
            return Result(
                error_code="PROVIDER_NOT_SUPPORTED",
                message=f"The provider {provider_name} is not supported.",
            )

        if not model_name:
            model_name = input("Enter model name: ").strip()

        model_setting = self.settings.allowed_providers[provider_name]["model"]

        model_ids = self.get_model_ids_for_provider()
        if not any(model_name == model_id for model_id in model_ids):
            return Result(
                error_code="MODEL_NOT_FOUND",
                message=f"Model name '{model_name}' not found in list of model ids.",
            )

        result = self.set_setting(model_setting, model_name)
        if not result.ok:
            return result

        #print(f"{model_setting.key} set to {model_name}")
        return Result(message=f"{model_setting.key} set to {model_name}")

    def list_models(self) -> None:
        provider = self.settings.provider_name.value

        if provider is None:
            return Result(error_code="No provider", message="Issue: provider is set to None. No models to list.")

        #print(f"{provider} was identified as the model provider.")
        #print("You can choose among the following models:")
        #for model_id in self.get_model_ids_for_provider():
        #    print(model_id)
        
        model_ids = self.get_model_ids_for_provider()
        return Result(value=model_ids)

    def get_model_ids_for_provider(self) -> list[str]:
        provider_name = self.settings.provider_name.value
        api_key = self.settings.allowed_providers[provider_name]["api_key"].value

        match provider_name:
            case "huggingface":
                from huggingface_hub import list_models as list_huggingface_models

                author = self.settings.hf_model_author.value

                if author == "Helsinki-NLP":
                    return [
                        "Helsinki-NLP/opus-mt-es_en",
                        "Helsinki-NLP/opus-mt-es_de",
                        "Helsinki-NLP/opus-mt-en_es",
                        "Helsinki-NLP/opus-mt-en_de",
                        "Helsinki-NLP/opus-mt-de_es",
                        "Helsinki-NLP/opus-mt-de_en",
                        "Helsinki-NLP/opus-mt_tiny_esp_eng",
                        "Helsinki-NLP/opus-mt_tiny_esp_deu",
                        "Helsinki-NLP/opus-mt_tiny_eng_esp",
                        "Helsinki-NLP/opus-mt_tiny_eng_deu",
                        "Helsinki-NLP/opus-mt_tiny_deu_spa",
                        "Helsinki-NLP/opus-mt_tiny_deu_eng",
                    ]
                else:
                    return [
                        model.id
                        for model in list_huggingface_models(
                            author=author,
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
                    f"Model configuration for provider {provider_name} is not implemented."
                )

    def print_environment_info(self) -> None:
        settings = [
            setting
            for setting in vars(self.settings).values()
            if isinstance(setting, Setting)
        ]

        label_width = (
            max(
                (len(setting.key) + 1 for setting in settings),
                default=0,
            )
            + 3
        )

        for setting in settings:
            label = f"{setting.key}:"
            print(f"{label:<{label_width}}{setting.environment_info}")


if __name__ == "__main__":
    settings = Settings()
    manager = SettingsManager(settings)
    result = manager.load()
    if not result.ok:
        print(result.message)
    print(settings)
