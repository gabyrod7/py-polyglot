import argparse

from core.config import Settings, SettingsManager
from core.result import Result


def main(
    argv: list[str] | None = None,
    settings_manager: SettingsManager | None = None,
) -> int:
    if settings_manager is None:
        settings = Settings()
        settings_manager = SettingsManager(settings)
        result = settings_manager.load()
        if not result.ok:
            print(result.message)
            return 1
    else:
        settings = settings_manager.settings

    parser = argparse.ArgumentParser(
        prog="py-polyglot",
        description="Translate text using Hugging Face or remote LLM providers.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    translate_parser = subparsers.add_parser(
        "translate",
        help="Translate text",
    )
    translate_parser.add_argument("query", type=str, help="Word or phrase to translate")
    translate_parser.add_argument("--verbose", action="store_true", help="")
    translate_parser.add_argument(
        "-s",
        "--source_language",
        dest="source_language",
        type=str,
        default="",
        help="Source language to translate from",
    )
    translate_parser.add_argument(
        "-t",
        "--target_language",
        dest="target_language",
        type=str,
        default="",
        help="Target language to translate to",
    )

    subparsers.add_parser(
        "info",
        help="Show supported environment variables",
        description="Show supported environment variables.",
    )

    config_parser = subparsers.add_parser(
        "config",
        help="Configure translation settings",
    )
    config_parser.add_argument(
        "--list_model_names",
        action="store_true",
        help="Provide list of available local models.",
    )
    config_parser.add_argument(
        "--set_model_name",
        nargs="?",
        const="",
        type=str,
        default=None,
        help="Model name to use for local translations",
    )
    config_parser.add_argument(
        "--set_provider",
        nargs="?",
        const="",
        type=str,
        default=None,
        help="Choose remote model provider",
    )
    config_parser.add_argument(
        "--set_api_key",
        action="store_true",
        help="Set remote provider API key",
    )
    config_parser.add_argument(
        "--set_source_language",
        nargs="?",
        const="",
        type=str,
        default=None,
        help="Source language to translate from",
    )
    config_parser.add_argument(
        "--set_target_language",
        nargs="?",
        const="",
        type=str,
        default=None,
        help="Target language to translate to",
    )
    config_parser.add_argument(
        "--print_config_file_path",
        action="store_true",
        help="Print path to file where settings are stored.",
    )

    args = parser.parse_args(argv)

    match args.command:
        case "translate":
            from core.translate import run_translate

            if args.source_language:
                settings.source_language.value = args.source_language
            if args.target_language:
                settings.target_language.value = args.target_language
            if args.verbose:
                settings.verbose.value = "True"

            result = run_translate(settings, args.query)
            if not result.ok:
                print(result.message)
                return 1

            print(result.value)

        case "info":
            settings_manager.print_environment_info()

        case "config":
            config_args_used = any(
                getattr(args, action.dest) != config_parser.get_default(action.dest)
                for action in config_parser._actions
                if action.dest != "help"
            )

            if not config_args_used:
                config_parser.print_help()

            if args.list_model_names:
                settings_manager.list_models()
            if args.set_model_name is not None:
                result = settings_manager.set_model_name(model_name=args.set_model_name)
                if not result.ok:
                    print(result.message)
            if args.set_provider is not None:
                result = set_provider(settings_manager, args.set_provider)
                if not result.ok:
                    print(result.message)
            if args.set_api_key:
                result = settings_manager.set_api_key()
                if not result.ok:
                    print(result.message)
            if args.set_source_language is not None:
                result = settings_manager.set_language(args.set_source_language, "source")
                if not result.ok:
                    print(result.message)
            if args.set_target_language is not None:
                result = settings_manager.set_language(args.set_target_language, "target")
                if not result.ok:
                    print(result.message)
            if args.print_config_file_path:
                print(settings_manager.get_config_file_path())

        case _:
            parser.print_help()

    return 0


def set_provider(settings_manager: SettingsManager, provider_name: str) -> Result:
    settings = settings_manager.settings
    if provider_name not in settings.allowed_providers:
        print("Choose among the following providers:")
        for provider in settings.allowed_providers:
            print(provider)

    while provider_name not in settings.allowed_providers:
        provider_name = input("Input provider: ").strip()

    result = settings_manager.set_setting(setting=settings.provider_name, value=provider_name)
    if not result.ok:
        return result

    return Result()


if __name__ == "__main__":
    raise SystemExit(main())
