from cli.config import get_setting

def run_translate_command(query: str, verbose: bool) -> None:
    provider = get_setting("PROVIDER")
    
    match provider:
        case "huggingface":
            run_huggingface_model(query, verbose)
        case "openai":
            print("not implemented")
            pass
        case "anthropic":
            print("not implemented")
            pass
        case "gemini":
            print("not implemented")
            pass

def run_huggingface_model(query: str, verbose: bool) -> None:
    from transformers import MarianMTModel, MarianTokenizer

    hf_token = get_setting("HF_TOKEN")
    model_name = get_setting("HF_MODEL")

    if not model_name:
        raise ValueError(
            "No model has been chosen. Use `config --set_model_name` options to set a model."
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

