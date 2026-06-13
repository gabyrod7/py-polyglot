# Language Translator CLI

[![CI](https://github.com/gabyrod7/language_translator/actions/workflows/ci.yml/badge.svg)](https://github.com/gabyrod7/language_translator/actions/workflows/ci.yml)

A command-line tool to translate words, phrases, and sentences from one language to another using either a local model from Hugging Face or a remote LLM provider.

The CLI currently supports:

- Local translation with Helsinki-NLP `opus-mt_tiny` models
- Remote translation with OpenAI, Anthropic, or Gemini

## Requirements

- Python 3.12 or newer
- API keys for any remote provider you want to use
- A Hugging Face token if the selected local model requires one

## Installation

Install the project dependencies with:

```bash
uv sync
```
or

```bash
python -m pip install .
```
## Local Translation

Local translation uses Hugging Face models from Helsinki-NLP. Only models whose names contain `opus-mt_tiny` are supported. Before translating a word, phrase, or sentence, you must choose a model with `run_local config`:

```bash
uv run python cli/main.py run_local config --list_model_names
uv run python cli/main.py run_local config --set_model_name Helsinki-NLP/opus-mt_tiny-en-es
```

The optional `--list_model_names` flag prints the available local models. The `--set_model_name` flag saves the model name in the local configuration file. If no model name is provided, the CLI will prompt you for one.

Each local model is trained for a specific source and target language pair. That information is encoded at the end of the model name. In the example above, the model name ends with `en-es`, so the model translates from English to Spanish. Each config flag is discussed in more detail in the [Configuration](#configuration) section.

Translate text locally:

```bash
uv run python cli/main.py run_local translate "hello"
```

## Remote Translation

Remote translation uses one of the supported LLM providers: `openai`, `anthropic`, or `gemini`.

Set the remote provider. If no provider is given, the CLI will prompt you for one:

```bash
uv run python cli/main.py run_remote config --set_provider openai
```

Set the API key and a model for the configured provider:

```bash
uv run python cli/main.py run_remote config --set_api_key --set_model
```

A list of available models will be printed to screen and the user will be requested to input a model name. If a model has already been set, the CLI will ask if the user wants to update the model. 

Translate text remotely:

```bash
uv run python cli/main.py run_remote translate "English" "Spanish" "hello"
```

## Configuration

The CLI loads configuration from a local `.env` file and writes settings there when you run the config commands.

Local configuration flags:

- `run_local config --list_model_names` prints the supported Helsinki-NLP local models.
- `run_local config --set_model_name [MODEL_NAME]` stores the local model used by `run_local translate`. If `MODEL_NAME` is omitted, the CLI prompts for it.
- `run_local config --set_hf_token [TOKEN]` stores the Hugging Face token. If `TOKEN` is omitted, the CLI prompts for it.

Remote configuration flags:

- `run_remote config --set_provider [PROVIDER]` stores the remote provider. Supported providers are `openai`, `anthropic`, and `gemini`. If `PROVIDER` is omitted, the CLI prompts for it.
- `run_remote config --set_api_key` stores the API key for the configured remote provider.
- `run_remote config --set_model` lists the available models for the configured remote provider and stores the selected model.

Local translation uses:

```env
MODEL_NAME
HF_TOKEN
```

Remote translation uses:

```env
LLM_PROVIDER
OPENAI_API_KEY
OPENAI_MODEL
ANTHROPIC_API_KEY
ANTHROPIC_MODEL
GEMINI_API_KEY
GEMINI_MODEL
```

Only the variables for your selected provider are required. For example, if `LLM_PROVIDER` is set to `openai`, then `OPENAI_API_KEY` and `OPENAI_MODEL` must also be configured.

## Supported Providers

Local provider:

- Hugging Face Helsinki-NLP `opus-mt_tiny` models

Remote providers:

- `openai`
- `anthropic`
- `gemini`

## Limitations

Before running a local translation, you must configure a supported local model.

Before running a remote translation, you must configure a provider, an API key, and a model for that provider.

Local model quality, supported language pairs, and download requirements depend on the selected Hugging Face model.
