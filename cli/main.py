import argparse

from .config import load_config_file

load_config_file()


def main():
    parser = argparse.ArgumentParser(
        prog="Language Translator", description="", epilog=""
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    run_local_parser = subparsers.add_parser(
        "run_local", help="Translate with a local model"
    )
    run_local_subparsers = run_local_parser.add_subparsers(
        dest="run_local_command", help="Available run_local commands"
    )

    run_local_translate_parser = run_local_subparsers.add_parser(
        "translate", help="Run a local translation"
    )
    run_local_translate_parser.add_argument(
        "query", type=str, help="Word or phrase to translate"
    )
    run_local_translate_parser.add_argument("--verbose", action="store_false", help="")

    run_local_config_parser = run_local_subparsers.add_parser(
        "config", help="Configure local translation settings"
    )
    run_local_config_parser.add_argument(
        "--list_model_names",
        action="store_true",
        help="Provide list of available local models.",
    )
    run_local_config_parser.add_argument(
        "--set_model_name",
        nargs="?",
        const="",
        type=str,
        default=None,
        help="Model name to use for local translations",
    )
    run_local_config_parser.add_argument(
        "--set_hf_token",
        action="store_true",
        help="Set HuggingFace token",
    )

    run_remote_parser = subparsers.add_parser(
        "run_remote", help="Translate with a remote model provider"
    )
    run_remote_subparsers = run_remote_parser.add_subparsers(
        dest="run_remote_command_name", help="Available run_remote commands"
    )

    run_remote_translate_parser = run_remote_subparsers.add_parser(
        "translate", help="Run a remote translation"
    )
    run_remote_translate_parser.add_argument(
        "source_lang", type=str, help="Language of word or phrase to be translated from"
    )
    run_remote_translate_parser.add_argument(
        "target_lang", type=str, help="Language of word or phrase to be translated into"
    )
    run_remote_translate_parser.add_argument(
        "query", type=str, help="Word or phrase to be translated"
    )

    run_remote_config_parser = run_remote_subparsers.add_parser(
        "config", help="Configure remote translation settings"
    )
    run_remote_config_parser.add_argument(
        "--set_provider",
        nargs="?",
        const="",
        type=str,
        default=None,
        help="Choose remote model provider",
    )
    run_remote_config_parser.add_argument(
        "--set_api_key",
        action="store_true",
        help="Set remote provider API key when requested",
    )
    run_remote_config_parser.add_argument(
        "--set_model",
        action="store_true",
        help="Choose a remote model from the given list.",
    )

    args = parser.parse_args()

    match args.command:
        case "run_local":
            from .run_local import (
                configure_local_model,
                list_local_models,
                run_local_command,
                configure_hf_token,
            )

            match args.run_local_command:
                case "translate":
                    run_local_command(args.query, args.verbose)
                case "config":
                    if (
                        not args.list_model_names
                        and args.set_model_name is None
                        and not args.set_hf_token
                    ):
                        run_local_parser.print_help()
                    if args.list_model_names:
                        list_local_models()
                    if args.set_model_name is not None:
                        configure_local_model(model_name=args.set_model_name)
                    if args.set_hf_token:
                        configure_hf_token()
                case _:
                    run_local_parser.print_help()

        case "run_remote":
            from .run_remote import (
                configure_remote_api_key,
                configure_remote_model,
                configure_remote_provider,
                run_remote_command,
            )

            match args.run_remote_command_name:
                case "translate":
                    run_remote_command(args.source_lang, args.target_lang, args.query)
                case "config":
                    if not (
                        args.set_provider is not None or args.set_api_key or args.set_model
                    ):
                        run_remote_parser.print_help()
                    if args.set_provider is not None:
                        configure_remote_provider(args.set_provider)
                    if args.set_api_key:
                        configure_remote_api_key()
                    if args.set_model:
                        configure_remote_model()
                case _:
                    run_remote_parser.print_help()

        case _:
            parser.print_help()


if __name__ == "__main__":
    main()
