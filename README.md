# py-polyglot

[![CI](https://github.com/gabyrod7/py-polyglot/actions/workflows/ci.yml/badge.svg)](https://github.com/gabyrod7/py-polyglot/actions/workflows/ci.yml)

A Python command-line tool to translate words, phrases, and sentences using either a local Hugging Face model or a remote LLM provider.

The CLI currently supports:

- Local translation with Helsinki-NLP `opus-mt_tiny` models through Hugging Face
- Remote translation with OpenAI, Anthropic, or Gemini

## Requirements

- Python 3.12 or newer
- API keys for any remote provider you want to use
- A Hugging Face token if the selected local model requires one

## Installation

For local development from the cloned repository, install the project and dependencies with:

```bash
uv sync
```

Then run the CLI with:

```bash
uv run py-polyglot --help
```

To install the CLI as a user-level tool from the repository, run:

```bash
uv tool install .
```

Then run it directly:

```bash
py-polyglot --help
```

You can also install it with pip:

```bash
python -m pip install .
```

## Quick Start

Choose a provider:

```bash
uv run py-polyglot config --set_provider openai
```

Set the model and API key/token for that provider:

```bash
uv run py-polyglot config --set_model_name gpt-4.1-mini
uv run py-polyglot config --set_api_key
```

Set default languages:

```bash
uv run py-polyglot config --set_source_language English
uv run py-polyglot config --set_target_language Spanish
```

Translate text:

```bash
uv run py-polyglot translate "hello"
```

You can also provide languages per translation:

```bash
uv run py-polyglot translate "hello" --source_language English --target_language Spanish
```

If source or target language is not provided on the command line, `translate` checks the saved `SOURCE_LANGUAGE` and `TARGET_LANGUAGE` settings. If either setting is missing, the CLI prompts for it.

## Local Translation

Local translation uses Hugging Face models from Helsinki-NLP. Only models whose names contain `opus-mt_tiny` are supported.

Configure Hugging Face as the provider:

```bash
uv run py-polyglot config --set_provider huggingface
```

List available local models:

```bash
uv run py-polyglot config --list_model_names
```

Set a local model:

```bash
uv run py-polyglot config --set_model_name Helsinki-NLP/opus-mt_tiny-en-es
```

Each local model is trained for a specific source and target language pair. That information is encoded at the end of the model name. In the example above, the model name ends with `en-es`, so the model translates from English to Spanish.

Translate text locally:

```bash
uv run py-polyglot translate "hello"
```

## Remote Translation

Remote translation uses one of the supported LLM providers: `openai`, `anthropic`, or `gemini`.

Configure a remote provider:

```bash
uv run py-polyglot config --set_provider openai
```

Set the API key for the configured provider:

```bash
uv run py-polyglot config --set_api_key
```

List available models:

```bash
uv run py-polyglot config --list_model_names
```

Set the model:

```bash
uv run py-polyglot config --set_model_name gpt-4.1-mini
```

Translate text remotely:

```bash
uv run py-polyglot translate "hello" --source_language English --target_language Spanish
```

## Configuration

The CLI stores non-secret settings in a local config file and stores secrets in the system keyring.

Non-secret settings are written to `config.env` under the user's config directory, usually `~/.config/py-polyglot/config.env` on Linux/macOS.

Secrets are stored with the service name `py-polyglot` in the system keyring. Environment variables with the same names can still be used and take precedence over keyring values.

Print the config file path:

```bash
uv run py-polyglot config --print_config_file_path
```

Configuration flags:

- `config --set_provider [PROVIDER]` stores the provider. Supported providers are `huggingface`, `openai`, `anthropic`, and `gemini`. If `PROVIDER` is omitted or unsupported, the CLI prompts for it.
- `config --list_model_names` prints models available for the configured provider.
- `config --set_model_name [MODEL_NAME]` stores the model used by `translate`. If `MODEL_NAME` is omitted, the CLI prompts for it.
- `config --set_api_key` prompts for the API key/token for the configured provider and stores it in the system keyring when possible.
- `config --set_source_language [LANGUAGE]` stores the default source language as `SOURCE_LANGUAGE`. If `LANGUAGE` is omitted, the CLI prompts for it.
- `config --set_target_language [LANGUAGE]` stores the default target language as `TARGET_LANGUAGE`. If `LANGUAGE` is omitted, the CLI prompts for it.
- `config --print_config_file_path` prints the path to the config file.

Translate flags:

- `translate QUERY` translates the provided text.
- `translate QUERY --source_language LANGUAGE` sets the source language for that translation.
- `translate QUERY --target_language LANGUAGE` sets the target language for that translation.
- `translate QUERY --verbose` controls extra output/progress behavior.

Non-secret settings:

```env
PROVIDER
HF_MODEL
OPENAI_MODEL
ANTHROPIC_MODEL
GEMINI_MODEL
SOURCE_LANGUAGE
TARGET_LANGUAGE
```

Secrets:

```env
HF_TOKEN
OPENAI_API_KEY
ANTHROPIC_API_KEY
GEMINI_API_KEY
```

Only the values for your selected provider are required. For example, if `PROVIDER` is set to `openai`, then `OPENAI_API_KEY` and `OPENAI_MODEL` must also be configured.

## Supported Providers

- `huggingface`
- `openai`
- `anthropic`
- `gemini`

## Limitations

Before translating, you must configure a provider and model.

For remote providers, you must also configure an API key.

Local model quality, supported language pairs, and download requirements depend on the selected Hugging Face model.
