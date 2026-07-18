from cli.config import PROVIDER_SPECS, get_setting


def run_translate_command(
    query: str,
    verbose: bool,
    source_language: str = "",
    target_language: str = "",
) -> None:
    provider = get_setting("PROVIDER")

    if source_language == "":
        source_language = (
            get_setting("SOURCE_LANGUAGE") or input("Enter source language: ").strip()
        )

    if target_language == "":
        target_language = (
            get_setting("TARGET_LANGUAGE") or input("Enter target language: ").strip()
        )

    match provider:
        case "huggingface":
            run_huggingface_model(query, verbose)
        case "openai":
            run_openai_model(query, verbose, source_language, target_language)
        case "anthropic":
            run_anthropic_model(query, verbose, source_language, target_language)
        case "gemini":
            run_gemini_model(query, verbose, source_language, target_language)
        case _:
            raise ValueError(f"The provider {provider} is not supported.")


def get_remote_model_settings(provider: str) -> tuple[str, str]:
    model_name = get_setting(PROVIDER_SPECS[provider]["model_env"])
    api_key = get_setting(PROVIDER_SPECS[provider]["api_key_env"])

    if not model_name:
        raise ValueError(
            f"No {PROVIDER_SPECS[provider]['model_env']} environment variable found."
        )
    if not api_key:
        raise ValueError(
            f"No {PROVIDER_SPECS[provider]['api_key_env']} environment variable found."
        )

    return model_name, api_key


def run_openai_model(
    query: str,
    verbose: bool,
    source_language: str,
    target_language: str,
    model_name: str | None = None,
    api_key: str | None = None,
) -> None:
    if model_name is None or api_key is None:
        model_name, api_key = get_remote_model_settings("openai")

    if verbose:
        print(
            f"Requesting translation from {source_language} to {target_language} "
            "from OpenAI for the following text:"
        )
        print(query)

    import openai
    from openai.types.responses.response import Response

    client = openai.OpenAI(api_key=api_key)

    try:
        response: Response = client.responses.create(
            model=model_name,
            instructions=(
                f"You are a {source_language} to {target_language} translator. "
                "Provide only the tranlation of the given text."
            ),
            input=query,
        )
    except openai.APITimeoutError as e:
        print_openai_error(title="OpenAI request timed out.", e=e)
        raise SystemExit(1) from e
    except openai.APIConnectionError as e:
        print_openai_error(title="Could not connect to OpenAI.", e=e)
        raise SystemExit(2) from e
    except openai.APIError as e:
        print_openai_error(title="OpenAI API error.", e=e)
        raise SystemExit(1) from e

    print(response.output_text)


def print_openai_error(title: str, e: Exception) -> None:
    import openai

    print(title)

    status_code = getattr(e, "status_code", None)
    if status_code:
        print(f"Status code: {status_code}")

    message = getattr(e, "message", None)
    if message:
        print(f"Message: {message}")

    error_type = getattr(e, "type", None)
    if error_type:
        print(f"Type: {error_type}")

    code = getattr(e, "code", None)
    if code:
        print(f"Code: {code}")

    param = getattr(e, "param", None)
    if param:
        print(f"Parameter: {param}")

    request_id = getattr(e, "request_id", None)
    if request_id:
        print(f"Request ID: {request_id}")

    cause = getattr(e, "__cause__", None)
    if cause:
        print(f"Technical details: {cause}")

    if isinstance(e, openai.APITimeoutError):
        print("Likely cause: The request took too long to complete.")
        print(
            "Try this: Wait briefly and retry. If it keeps happening, check your "
            "network connection or try a smaller request."
        )
    elif isinstance(e, openai.APIConnectionError):
        print("Likely cause: The request could not reach OpenAI.")
        print(
            "Try this: Check your internet connection, DNS, proxy/firewall settings, "
            "or OpenAI service status."
        )
    elif status_code == 400:
        print("Likely cause: The request is malformed or missing required parameters.")
        print(
            "Try this: Check the model name, input text, request parameters, and API "
            "documentation for this endpoint."
        )
    elif status_code == 401:
        print(
            "Likely cause: Your API key is invalid, expired, revoked, or belongs to "
            "the wrong project."
        )
        print(
            "Try this: Check your configured OpenAI API key, or generate a new one "
            "from your account dashboard."
        )
    elif status_code == 403:
        print(
            "Likely cause: Your API key, organization, project, model, or requested "
            "resource does not have the required access."
        )
        print(
            "Try this: Check that you are using the correct API key and that your "
            "account has access to the requested model or resource."
        )
    elif status_code == 404:
        print(
            "Likely cause: The requested model or resource does not exist or is not "
            "available to your account."
        )
        print(
            "Try this: Check your configured model name and confirm your account has "
            "access to it."
        )
    elif status_code == 409:
        print("Likely cause: The resource was updated by another request.")
        print(
            "Try this: Retry the request and make sure no other process is updating "
            "the same resource."
        )
    elif status_code == 422:
        print(
            "Likely cause: The request format was valid, but OpenAI could not process it."
        )
        print(
            "Try this: Try the request again. If it persists, review the input and "
            "model compatibility."
        )
    elif status_code == 429:
        print(
            "Likely cause: You may have sent too many requests, exceeded token limits, "
            "run out of quota, or need to update billing."
        )
        print(
            "Try this: Wait and retry, reduce the request size, try a different model, "
            "or check your OpenAI usage limits and billing status."
        )
    elif status_code == 500:
        print("Likely cause: OpenAI had an issue processing the request.")
        print(
            "Try this: Wait briefly and retry. If it persists, check "
            "https://status.openai.com/."
        )
    elif status_code == 503:
        print("Likely cause: OpenAI is temporarily overloaded or unavailable.")
        print(
            "Try this: Wait and retry with backoff. If it persists, check "
            "https://status.openai.com/."
        )
    elif status_code:
        print("Likely cause: OpenAI returned an API error.")
        print(
            "Try this: Review the status code and message, then check your API key, "
            "model name, quota, billing, and request parameters."
        )


def run_anthropic_model(
    query: str,
    verbose: bool,
    source_language: str,
    target_language: str,
    model_name: str | None = None,
    api_key: str | None = None,
) -> None:
    if model_name is None or api_key is None:
        model_name, api_key = get_remote_model_settings("anthropic")

    if verbose:
        print(
            f"Requesting translation from {source_language} to {target_language} "
            "from Anthropic for the following text:"
        )
        print(query)

    import anthropic

    client = anthropic.Anthropic(api_key=api_key)

    try:
        message = client.messages.create(
            model=model_name,
            max_tokens=1024,
            messages=[
                {
                    "role": "assistant",
                    "content": (
                        f"I am a {source_language} to {target_language} translator and "
                        "will only translate whatever word, phrase, sentence or "
                        "sentences the user requests."
                    ),
                },
                {"role": "user", "content": query},
            ],
        )
    except anthropic.APITimeoutError as e:
        print_anthropic_error(title="Anthropic request timed out.", e=e)
        raise SystemExit(1) from e
    except anthropic.APIConnectionError as e:
        print_anthropic_error(title="Could not connect to Anthropic.", e=e)
        raise SystemExit(1) from e
    except anthropic.APIStatusError as e:
        print_anthropic_error(title="Anthropic returned an API error.", e=e)
        raise SystemExit(1) from e
    except anthropic.APIError as e:
        print_anthropic_error(title="Anthropic SDK error.", e=e)
        raise SystemExit(1) from e

    print(message.content[0].text)


def print_anthropic_error(title: str, e: Exception) -> None:
    import anthropic

    print(title)

    status_code = getattr(e, "status_code", None)
    if status_code:
        print(f"Status code: {status_code}")

    message = getattr(e, "message", None)
    if message:
        print(f"Message: {message}")

    error_type = getattr(e, "type", None)
    if error_type:
        print(f"Type: {error_type}")

    request_id = getattr(e, "request_id", None)
    if request_id:
        print(f"Request ID: {request_id}")

    body = getattr(e, "body", None)
    if body:
        print(f"Details: {body}")

    cause = getattr(e, "__cause__", None)
    if cause:
        print(f"Technical details: {cause}")

    if isinstance(e, anthropic.APITimeoutError):
        print("Likely cause: The request took too long to complete.")
        print(
            "Try this: Wait briefly and retry. For long requests, reduce max tokens "
            "or consider using streaming."
        )
    elif isinstance(e, anthropic.APIConnectionError):
        print("Likely cause: The request could not reach Anthropic.")
        print(
            "Try this: Check your network settings, proxy configuration, SSL "
            "certificates, or firewall rules."
        )
    elif error_type == "invalid_request_error" or status_code == 400:
        print("Likely cause: The request format or content is invalid.")
        print(
            "Try this: Check the model name, input text, max token value, and "
            "request parameters."
        )
    elif error_type == "authentication_error" or status_code == 401:
        print("Likely cause: There is an issue with your Anthropic API key.")
        print(
            "Try this: Check that your configured Anthropic API key is correct and active."
        )
    elif error_type == "billing_error" or status_code == 402:
        print("Likely cause: There is an issue with billing or payment information.")
        print("Try this: Check your billing settings in the Claude Console.")
    elif error_type == "permission_error" or status_code == 403:
        print(
            "Likely cause: Your API key does not have permission to use the "
            "specified resource."
        )
        print(
            "Try this: Check that your key has access to the requested model or resource."
        )
    elif error_type == "not_found_error" or status_code == 404:
        print("Likely cause: The requested model or resource was not found.")
        print(
            "Try this: Check your configured model name and confirm your account has "
            "access to it."
        )
    elif error_type == "request_too_large" or status_code == 413:
        print("Likely cause: The request exceeds Anthropic's maximum request size.")
        print(
            "Try this: Reduce the input size or split the request into smaller requests."
        )
    elif error_type == "rate_limit_error" or status_code == 429:
        print("Likely cause: Your account has hit a rate limit or acceleration limit.")
        print(
            "Try this: Slow down requests, wait and retry, or check your Anthropic "
            "usage limits."
        )
    elif error_type == "api_error" or status_code == 500:
        print("Likely cause: Anthropic had an internal issue processing the request.")
        print(
            "Try this: Wait briefly and retry. If it persists, check Anthropic "
            "service status or contact support."
        )
    elif error_type == "timeout_error" or status_code == 504:
        print("Likely cause: The request timed out while Anthropic was processing it.")
        print(
            "Try this: Reduce request size, lower max tokens, or consider using "
            "streaming for long requests."
        )
    elif error_type == "overloaded_error" or status_code == 529:
        print("Likely cause: Anthropic is temporarily overloaded.")
        print("Try this: Wait and retry with backoff.")
    elif status_code or error_type:
        print("Likely cause: Anthropic returned an API error.")
        print(
            "Try this: Review the status code, type, and message, then check your "
            "API key, model name, billing, quota, and request parameters."
        )


def run_gemini_model(
    query: str,
    verbose: bool,
    source_language: str,
    target_language: str,
    model_name: str | None = None,
    api_key: str | None = None,
) -> None:
    if model_name is None or api_key is None:
        model_name, api_key = get_remote_model_settings("gemini")

    if verbose:
        print(
            f"Requesting translation from {source_language} to {target_language} "
            "from Gemini for the following text:"
        )
        print(query)

    from google import genai
    from google.genai import errors

    client = genai.Client(api_key=api_key)

    try:
        response = client.models.generate_content(
            model=model_name,
            config=genai.types.GenerateContentConfig(
                system_instruction=(
                    f"You are a {source_language} to {target_language} translator. "
                    "Provide only the tranlation of the given text."
                )
            ),
            contents=query,
        )
    except errors.ClientError as e:
        print_gemini_error("Gemini rejected the request.", e)
        raise SystemExit(1) from e
    except errors.ServerError as e:
        print_gemini_error("Gemini server error.", e)
        raise SystemExit(1) from e
    except errors.APIError as e:
        print_gemini_error("Gemini API error.", e)
        raise SystemExit(1) from e

    print(response.text)


def print_gemini_error(title: str, e: Exception) -> None:
    print(title)

    code = getattr(e, "code", None)
    if code:
        print(f"Status code: {code}")

    status = getattr(e, "status", None)
    if status:
        print(f"Status: {status}")

    message = getattr(e, "message", None)
    if message:
        print(f"Message: {message}")

    if code:
        if code == 400:
            print(
                "Likely cause: The request is malformed or contains invalid parameters."
            )
            print(
                "Try this: Check the model name, input text, request format, and "
                "generation config."
            )
        elif code == 401:
            print(
                "Likely cause: The API key is missing, invalid, expired, or from "
                "the wrong project."
            )
            print(
                "Try this: Check your configured Gemini API key and generate a new "
                "one if needed."
            )
        elif code == 403:
            print(
                "Likely cause: The API key does not have permission, the Gemini API "
                "is not enabled, or billing/project access is blocked."
            )
            print(
                "Try this: Confirm the Gemini API is enabled for the right Google "
                "Cloud project and that your key has access."
            )
        elif code == 404:
            print("Likely cause: The requested model or resource was not found.")
            print(
                "Try this: Check your configured Gemini model name and confirm it is "
                "available for your API version."
            )
        elif code == 429:
            print("Likely cause: You hit a rate limit or quota limit.")
            print(
                "Try this: Wait and retry, reduce request frequency, or check your "
                "Gemini quota and billing settings."
            )
        elif code == 500:
            print("Likely cause: Gemini had an internal server error.")
            print(
                "Try this: Wait briefly and retry. If it persists, check Gemini "
                "service status."
            )
        elif code == 503:
            print("Likely cause: Gemini is temporarily unavailable or overloaded.")
            print("Try this: Wait and retry with backoff.")
        elif code == 504:
            print("Likely cause: The request timed out while Gemini was processing it.")
            print(
                "Try this: Retry later, reduce request size, or use a shorter "
                "prompt/output."
            )
        else:
            print("Likely cause: Gemini returned an API error.")
            print(
                "Try this: Review the status code and message, then check your API "
                "key, model name, quota, billing, and request parameters."
            )

    response = getattr(e, "response", None)
    if response:
        print(f"Response: {response}")


def run_huggingface_model(
    query: str,
    verbose: bool,
) -> None:
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
