import argparse
from translator import translate_command
from config import config_command

def main():
    parser = argparse.ArgumentParser(prog='Language Translator', description='', epilog='')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    translate_parser = subparsers.add_parser('translate', help='Translates word or phrase from one languague to another')
    translate_parser.add_argument('query', type=str, help='Word of phrase to translate')
    translate_parser.add_argument('--langs', type=str, default='en_de', help='Choose the original and final langauge')
    translate_parser.add_argument('--verbose', action='store_true', help='')

    config_parser = subparsers.add_parser('config', help='Set configuration variables')
    config_group = config_parser.add_mutually_exclusive_group()
    config_group.add_argument('--model_name', type=str, default='', help='Model name to use for translations')
    config_group.add_argument('--list_model_names', action='store_true', help='Provide list of available models.')

    args = parser.parse_args()

    match args.command:
        case 'config':
            config_command(model_name=args.model_name, list_model_names=args.list_model_names)

        case 'translate':
            translate_command(args.query, args.langs, args.verbose)

        case _:
            parser.print_help()


if __name__ == "__main__":
    main()
