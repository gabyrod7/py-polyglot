import os
import getpass
from huggingface_hub import list_models
from cli.config import (
    save_environment_variable,
    get_secret_environment_variable,
    save_secret_environment_variable,
)


def run_local_command(query, verbose):
    from transformers import MarianMTModel, MarianTokenizer

    try:
        hf_token = get_secret_environment_variable("HF_TOKEN")
    except RuntimeError:
        hf_token = None
    model_name = os.environ.get("MODEL_NAME")

    if not model_name:
        raise ValueError(
            "No model has been chosen. Use `run_local config --set_model_name` to set a model."
        )

    if verbose:
        from transformers.utils import logging

        logging.disable_progress_bar()
    else:
        print(f"Using model: {model_name}")

    tokenizer = MarianTokenizer.from_pretrained(model_name, token=hf_token)
    model = MarianMTModel.from_pretrained(model_name, token=hf_token)

    inputs = tokenizer(query, return_tensors="pt", padding=True)
    translated = model.generate(**inputs)

    result = tokenizer.decode(translated[0], skip_special_tokens=True)

    print(result)


def list_local_models() -> None:
    model_list = list_models(author="Helsinki-NLP")

    for model in model_list:
        if "opus-mt_tiny" in model.id:
            print(model.id)


def configure_local_model(model_name: str) -> None:
    if not model_name:
        model_name: str = input("Enter model name: ")

    if "opus-mt_tiny" not in model_name:
        raise ValueError(
            f"The model name given is '{model_name}' but only the 'opus-mt_tiny' models are supported. Use 'run_local config --list_model_names' flag to find all supported models."
        )

    model_found = False
    for model in list_models(author="Helsinki-NLP"):
        if model_name == model.id:
            model_found = True
            break

    if not model_found:
        raise ValueError(f"The model {model_name} could not be found.")

    save_environment_variable(key="MODEL_NAME", value=model_name)
    os.environ["MODEL_NAME"] = model_name
    print(f"Default model set to {model_name}")


def configure_hf_token() -> None:
    token: str = getpass.getpass("Enter HuggingFace token: ").strip()

    if not token:
        raise ValueError("The HuggingFace token cannot be empty or only white spaces.")

    save_secret_environment_variable(key="HF_TOKEN", value=token)

    # os.environ["HF_TOKEN"] = token
    print("HuggingFace token has been set.")
