import argparse

from dotenv import load_dotenv
load_dotenv()

def main():
    parser = argparse.ArgumentParser(prog='Language Translator', description='', epilog='')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    translate_parser = subparsers.add_parser('translate', help='Translates word or phrase from one languague to another')
    translate_parser.add_argument('query', type=str, help='Word or phrase to translate')
    translate_parser.add_argument('--langs', type=str, default='en_de', help='Choose the original and final langauge')
    translate_parser.add_argument('--verbose', action='store_true', help='')

    llm_parser = subparsers.add_parser('llm', help='Translates word or phrase from one languague to another')
    llm_parser.add_argument('inp', type=str, help='Language of word or phrase to be translated from')
    llm_parser.add_argument('out', type=str, help='Language of word or phrase to be translated into')
    llm_parser.add_argument('query', type=str, help='Word or phrase to be translated')

    config_parser = subparsers.add_parser('config', help='Set configuration variables')
    config_parser.add_argument('--llm_provider', type=str, default='', help="Choose LLM provider")
    config_parser.add_argument('--llm_set_model', action='store_true', help="Choose LLM model from the given list.")
    config_parser.add_argument('--llm_set_api_key', action='store_true', help="Set LLM API-key when requested")
    config_group = config_parser.add_mutually_exclusive_group()
    config_group.add_argument('--model_name', type=str, default='', help='Model name to use for translations')
    config_group.add_argument('--list_model_names', action='store_true', help='Provide list of available models.')

    args = parser.parse_args()

    match args.command:
        case 'config':
            from config import config_command
            config_command(model_name=args.model_name, list_model_names=args.list_model_names, llm_provider=args.llm_provider, llm_set_model=args.llm_set_model, llm_set_api_key=args.llm_set_api_key)

        case 'translate':
            from translator import translate_command
            translate_command(args.query, args.langs, args.verbose)

        case 'llm':
            from llm import llm_command
            llm_command(args.inp, args.out, args.query)

        case _:
            parser.print_help()


if __name__ == "__main__":
    main()
