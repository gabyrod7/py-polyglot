from dotenv import set_key
from huggingface_hub import list_models

def config_command(model_name: str, list_model_names: bool):
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
                print(model_name)
                model_found = True

        if not model_found:
            raise ValueError(f"The model {model_name} could not be found. ")

        set_key('.env', 'MODEL_NAME', model_name)
        print(f"Default model set to {model_name}")

