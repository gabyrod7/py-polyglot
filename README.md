# py-polyglot

[![CI](https://github.com/gabyrod7/py-polyglot/actions/workflows/ci.yml/badge.svg)](https://github.com/gabyrod7/py-polyglot/actions/workflows/ci.yml)

py-polyglot translates words, phrases, and sentences with either a local Hugging Face model or a remote LLM provider. It includes both a command-line interface and a PySide6 desktop interface.

Supported providers:

- Hugging Face with Helsinki-NLP translation models
- OpenAI
- Anthropic
- Gemini

## Requirements

- Python 3.12 or newer
- `uv` or `pip`
- A functioning system keyring backend
- An API key for each remote provider you use
- A Hugging Face token when required by the selected model

py-polyglot treats keyring read and write errors as fatal. It does not fall back to storing API keys in the plaintext configuration file. This requirement also applies when using local models.

## Installation

For local development, clone the repository and install the project and its dependencies:

```bash
uv sync
```

Run the CLI from the repository:

```bash
uv run py-polyglot --help
```

Run the desktop interface:

```bash
uv run py-polyglot-gui
```

To install the commands as user-level tools from the repository:

```bash
uv tool install .
```

You can then run them directly:

```bash
py-polyglot --help
py-polyglot-gui
```

Alternatively, install with pip:

```bash
python -m pip install .
```

## Quick Start

The defaults use Hugging Face to translate from German to English with `Helsinki-NLP/opus-mt_tiny_deu_eng`:

```bash
uv run py-polyglot translate "laufen"
```

Override the languages for one translation with `-s`/`--source_language` and `-t`/`--target_language`:

```bash
uv run py-polyglot translate "hello" \
  --source_language English \
  --target_language Spanish
```

Use `--verbose` to enable additional translation details:

```bash
uv run py-polyglot translate "hello" --verbose
```

## Configuration

Use the `config` command to change persistent settings. The supported configured languages are English, German, and Spanish.

Choose a provider:

```bash
uv run py-polyglot config --set_provider openai
```

For a remote provider, save its API key before requesting its model list:

```bash
uv run py-polyglot config --set_api_key
```

The API key is entered without echoing and stored in the system keyring. List the models available from the selected provider:

```bash
uv run py-polyglot config --list_model_names
```

Select a model:

```bash
uv run py-polyglot config --set_model_name gpt-4.1-mini
```

Set the default languages:

```bash
uv run py-polyglot config \
  --set_source_language English \
  --set_target_language Spanish
```

Configuration options can be combined. They are applied in dependency order: provider, API key, model listing or selection, and then languages. Their textual order on the command line does not affect execution.

### Configuration storage

Non-secret settings are stored in `config.env` under the user configuration directory, normally `~/.config/py-polyglot/config.env` on Linux. Print the active path with:

```bash
uv run py-polyglot config --print_config_file_path
```

Secrets are stored under the `py-polyglot` service name in the system keyring. Environment variables with matching names take precedence over values loaded from the configuration file or keyring.

Only credentials for the selected provider need values. For example, OpenAI translation requires `OPENAI_API_KEY`, while a public Hugging Face model may not require `HF_TOKEN`. A functioning keyring backend is still required.

Display all supported environment variables and their descriptions with:

```bash
uv run py-polyglot info
```

## Local Hugging Face Translation

Select Hugging Face as the provider:

```bash
uv run py-polyglot config --set_provider huggingface
```

List the supported Helsinki-NLP models:

```bash
uv run py-polyglot config --list_model_names
```

Select one of the returned model IDs:

```bash
uv run py-polyglot config \
  --set_model_name Helsinki-NLP/opus-mt_tiny_eng_spa
```

Each local model is trained for a particular language pair. The pair is encoded in the model name; for example, `eng_spa` translates from English to Spanish. For local translation, the selected model determines the effective language pair.

A model is downloaded the first time it is used. Download size, speed, translation quality, and token requirements depend on the selected model.

## Remote Translation

Remote translation is available through OpenAI, Anthropic, and Gemini. Configure a provider in this order:

```bash
uv run py-polyglot config --set_provider openai
uv run py-polyglot config --set_api_key
uv run py-polyglot config --list_model_names
uv run py-polyglot config --set_model_name gpt-4.1-mini
```

Then translate text:

```bash
uv run py-polyglot translate "hello" \
  --source_language English \
  --target_language Spanish
```

## Desktop Interface

Start the GUI with:

```bash
uv run py-polyglot-gui
```

The interface provides:

- Source and target language selectors
- Provider and model selectors
- Background model loading and translation
- Automatic source/target swapping when the same language is selected
- `Ctrl+T` to translate and `Ctrl+Q` to quit

Configure remote API keys through the CLI before selecting remote models in the GUI. Provider, model, and language selections made in the GUI apply to the current session.

## Development

Run the unit tests:

```bash
uv run python -m unittest discover -s tests -v
```

Run linting and formatting checks:

```bash
uv run ruff check .
uv run ruff format --check .
```

Build the source distribution and wheel:

```bash
uv build
```

## Limitations

- A usable system keyring backend is required.
- Remote translation requires a valid API key and model access for the selected provider.
- Available remote models depend on the provider account and API.
- Local model support, quality, and resource requirements depend on the selected Hugging Face model.
