from transformers import MarianMTModel, MarianTokenizer
import os

def translate_command(query, langs, verbose):
    hf_token = os.environ.get('HF_TOKEN')
    model_name = os.environ.get('MODEL_NAME')

    if not model_name:
        raise ValueError('No model has been chosen. Use the config option to set a model.')

    if not verbose:
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

