import argparse

from .config import load_config_file

load_config_file()


def main():
    parser = argparse.ArgumentParser(prog="py-polyglot", description="", epilog="")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    translate_parser = subparsers.add_parser("translate", help="Translate text")
    translate_parser.add_argument("query", type=str, help="Word or phrase to translate")
    translate_parser.add_argument("--verbose", action="store_false", help="")

    config_parser = subparsers.add_parser("config", help="Configure translation settings")
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
        "--set_hf_token",
        action="store_true",
        help="Set HuggingFace token",
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
        help="Set remote provider API key when requested",
    )
    config_parser.add_argument(
        "--set_model",
        action="store_true",
        help="Choose a remote model from the given list.",
    )

    args = parser.parse_args()

    match args.command:
        case "translate":
            from .run_local import run_local_command

            run_local_command(args.query, args.verbose)

        case "config":
            from .config import list_models
            from .run_local import (
                configure_hf_token,
                configure_local_model,
                list_local_models,
            )
            from .run_remote import (
                configure_remote_api_key,
                configure_remote_model,
                configure_remote_provider,
            )

            if (
                not args.list_model_names
                and args.set_model_name is None
                and not args.set_hf_token
                and args.set_provider is None
                and not args.set_api_key
                and not args.set_model
            ):
                config_parser.print_help()

            if args.list_model_names:
                #list_local_models()
                list_models()
            if args.set_model_name is not None:
                configure_local_model(model_name=args.set_model_name)
            if args.set_hf_token:
                configure_hf_token()
            if args.set_provider is not None:
                configure_remote_provider(args.set_provider)
            if args.set_api_key:
                configure_remote_api_key()
            if args.set_model:
                configure_remote_model()

        case _:
            parser.print_help()


if __name__ == "__main__":
    main()
