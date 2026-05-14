import os

from dotenv import set_key
from huggingface_hub import list_models
from constants import PROVIDER_SPECS

def config_command(model_name: str, list_model_names: bool, llm_provider: str, llm_set_model: bool, llm_set_api_key: bool):
    model_list = list_models(author="Helsinki-NLP")

    if list_model_names:
        for model in model_list:
            if "opus-mt_tiny" in model.id:
                print(model.id)

    if model_name:
        if "opus-mt_tiny" not in model_name:
            raise ValueError(f"The model name given is {model_name} but only the 'opus-mt-tiny' models are supported. Use the --list_model_names flag to find all supported models.")

        model_found = False
        for model in model_list:
            if model_name == model.id:
                model_found = True

        if not model_found:
            raise ValueError(f"The model {model_name} could not be found. ")

        set_key('.env', 'MODEL_NAME', model_name)
        print(f"Default model set to {model_name}")

    if llm_provider:
        supported_providers = tuple(PROVIDER_SPECS.keys())
        if llm_provider not in supported_providers:
            print(f"The LLM provider '{llm_provider}' is not supported. Please choose one from the list of supported providers:")
            for provider in supported_providers:
                print(provider)

            while llm_provider not in supported_providers:
                llm_provider = input('Choose provider: ')

                if llm_provider not in supported_providers:
                    print(f"The provider '{llm_provider}' is not supported. Please choose among the supported providers.")

        set_key('.env', 'LLM_PROVIDER', llm_provider)
        print('LLM_PROVIDER set to', llm_provider)

    if llm_set_api_key:
        if not llm_provider:
            llm_provider = os.environ.get('LLM_PROVIDER')

        set_llm_api_key(llm_provider)

    if llm_set_model:
        if not llm_provider:
            llm_provider = os.environ.get('LLM_PROVIDER')

        llm_api_key = os.environ.get(PROVIDER_SPECS[llm_provider]['api_key_env'])
        if not llm_api_key:
            set_llm_api_key(llm_provider)

        if llm_provider == 'openai':
            from openai import OpenAI

            client = OpenAI(api_key=llm_api_key)
            model_ids = [model.id for model in client.models.list().data]

            print('OpenAI was identified as the LLM provider.')
            print('Choose among the following models:')
            for model in model_ids:
                print(model)

            llm_model_name = ''
            while llm_model_name not in model_ids:
                llm_model_name = input('Input model name: ')
        elif llm_provider == 'anothropic':
            pass
        elif llm_provider == 'gemini':
            pass

        set_key('.env', PROVIDER_SPECS[llm_provider]['model_env'], llm_model_name)
        print(f"{PROVIDER_SPECS[llm_provider]['model_env']} has been set to {llm_model_name}")

def set_llm_api_key(llm_provider: str) -> None:
    llm_api_key = input(f'Enter API key for {llm_provider}: ').strip()

    if llm_api_key == '':
        print('API key cannot be empty or only white spaces.')
        exit(1)

    set_key('.env', PROVIDER_SPECS[llm_provider]['api_key_env'], llm_api_key)
    print(f"{PROVIDER_SPECS[llm_provider]['api_key_env']} has been set.")