# py-polyglot

[![CI](https://github.com/gabyrod7/py-polyglot/actions/workflows/ci.yml/badge.svg)](https://github.com/gabyrod7/py-polyglot/actions/workflows/ci.yml)

A Python command-line tool to translate words, phrases, and sentences using either a local Hugging Face model or a remote LLM provider.

The CLI currently supports:

- Local translation with Helsinki-NLP `opus-mt_tiny` models through Hugging Face
- Remote translation with OpenAI, Anthropic, or Gemini

## Requirements

- Python 3.12 or newer
- `uv` or `pip`
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

You will be prompted to enter your API key or token without echoing. Set default languages:

```bash
uv run py-polyglot config --set_source_language English --set_target_language Spanish
```

Translate text:

```bash
uv run py-polyglot translate "hello"
```

You can also provide languages per translation:

```bash
uv run py-polyglot translate "hello" --source_language English --target_language Spanish
```

## Local Translation

Local translation uses Hugging Face models from Helsinki-NLP. Only models whose names contain `opus-mt_tiny` are supported.

Configure Hugging Face as the provider:

```bash
uv run py-polyglot config --set_provider huggingface
```

List Hugging Face models for the configured provider, then choose an `opus-mt_tiny` model:

```bash
uv run py-polyglot config --list_model_names
```

Set a local model:

```bash
uv run py-polyglot config --set_model_name Helsinki-NLP/opus-mt_tiny-en-es
```

Each local model is trained for a specific source and target language pair. That information is encoded at the end of the model name. In the example above, the model name ends with `en-es`, so the model translates from English to Spanish. For Hugging Face translations, the model determines the language pair.

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

Non-secret settings are written to `config.env` under the user's config directory, usually `~/.config/py-polyglot/config.env` on Linux/macOS. The config file path can be obtained by running:

```bash
uv run py-polyglot config --print_config_file_path
```

Secrets are stored with the service name `py-polyglot` in the system keyring. Environment variables with the same names can still be used and take precedence over config file and keyring values.

Only the values for your selected provider are required. For example, if `PROVIDER` is set to `openai`, then `OPENAI_API_KEY` and `OPENAI_MODEL` must also be configured.

## Environment variables

Information on all supported environment variables can be obtained by using the `info` command:

```bash
uv run py-polyglot info
```

## Supported Providers

- `huggingface`
- `openai`
- `anthropic`
- `gemini`

## Limitations

Before translating, you must configure a provider and model.

For remote providers, you must also configure an API key.

Local model quality, supported language pairs, and download requirements depend on the selected Hugging Face model.
