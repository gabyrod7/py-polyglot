from openai.types.responses.response import Response
import os

#from dotenv import set_key
from cli.config import save_environment_variable

PROVIDER_SPECS: dict[str, dict[str, str]] = {
    "openai": {"model_env": "OPENAI_MODEL", "api_key_env": "OPENAI_API_KEY"},
    "anthropic": {"model_env": "ANTHROPIC_MODEL", "api_key_env": "ANTHROPIC_API_KEY"},
    "gemini": {"model_env": "GEMINI_MODEL", "api_key_env": "GEMINI_API_KEY"},
}


def run_remote_command(source_lang: str, target_lang: str, text: str) -> None:
    remote_provider: str = get_configured_remote_provider()

    remote_model_name: str | None = os.environ.get(key=PROVIDER_SPECS[remote_provider]["model_env"])
    remote_api_key: str | None = os.environ.get(key=PROVIDER_SPECS[remote_provider]["api_key_env"])

    if not remote_model_name:
        raise ValueError(
            f"No {PROVIDER_SPECS[remote_provider]['model_env']} environment variable found."
        )
    if not remote_api_key:
        raise ValueError(
            f"No {PROVIDER_SPECS[remote_provider]['api_key_env']} environment variable found."
        )

    run_remote_translation(
        remote_provider,
        remote_model_name,
        remote_api_key,
        source_lang,
        target_lang,
        text,
    )


def run_remote_translation(
    remote_provider: str,
    remote_model_name: str,
    remote_api_key: str,
    source_lang: str,
    target_lang: str,
    text: str,
) -> None:
    if remote_provider == "openai":
        run_with_openai(
            remote_model_name, remote_api_key, source_lang, target_lang, text
        )
    elif remote_provider == "anthropic":
        run_with_anthropic(
            remote_model_name, remote_api_key, source_lang, target_lang, text
        )
    elif remote_provider == "gemini":
        run_with_gemini(
            remote_model_name, remote_api_key, source_lang, target_lang, text
        )
    else:
        raise ValueError(
            f"The remote provider {remote_provider} is not supported inside this function!"
        )


def run_with_openai(
    remote_model_name: str,
    remote_api_key: str,
    source_lang: str,
    target_lang: str,
    text: str,
) -> None:
    print(
        f"Requesting translation from {source_lang} to {target_lang} from OpenAI for the following text:"
    )
    print(text)

    import openai

    client = openai.OpenAI(api_key=remote_api_key)

    try:
        response: Response = client.responses.create(
            model=remote_model_name,
            instructions=f"You are a {source_lang} to {target_lang} translator. Provide only the tranlation of the given text.",
            input=text,
        )
    except openai.APITimeoutError as e:
        print_openai_error(title="OpenAI request timed out.", e=e)
        raise SystemExit(1)
    except openai.APIConnectionError as e:
        print_openai_error(title="Could not connect to OpenAI.", e=e)
        raise SystemExit(1)
    except openai.APIError as e:
        print_openai_error(title="OpenAI API error.", e=e)
        raise SystemExit(1)

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
            "Try this: Wait briefly and retry. If it keeps happening, check your network connection or try a smaller request."
        )
    elif isinstance(e, openai.APIConnectionError):
        print("Likely cause: The request could not reach OpenAI.")
        print(
            "Try this: Check your internet connection, DNS, proxy/firewall settings, or OpenAI service status."
        )
    elif status_code == 400:
        print("Likely cause: The request is malformed or missing required parameters.")
        print(
            "Try this: Check the model name, input text, request parameters, and API documentation for this endpoint."
        )
    elif status_code == 401:
        print(
            "Likely cause: Your API key is invalid, expired, revoked, or belongs to the wrong project."
        )
        print(
            "Try this: Check your configured OpenAI API key, or generate a new one from your account dashboard."
        )
    elif status_code == 403:
        print(
            "Likely cause: Your API key, organization, project, model, or requested resource does not have the required access."
        )
        print(
            "Try this: Check that you are using the correct API key and that your account has access to the requested model or resource."
        )
    elif status_code == 404:
        print(
            "Likely cause: The requested model or resource does not exist or is not available to your account."
        )
        print(
            "Try this: Check your configured model name and confirm your account has access to it."
        )
    elif status_code == 409:
        print("Likely cause: The resource was updated by another request.")
        print(
            "Try this: Retry the request and make sure no other process is updating the same resource."
        )
    elif status_code == 422:
        print(
            "Likely cause: The request format was valid, but OpenAI could not process it."
        )
        print(
            "Try this: Try the request again. If it persists, review the input and model compatibility."
        )
    elif status_code == 429:
        print(
            "Likely cause: You may have sent too many requests, exceeded token limits, run out of quota, or need to update billing."
        )
        print(
            "Try this: Wait and retry, reduce the request size, try a different model, or check your OpenAI usage limits and billing status."
        )
    elif status_code == 500:
        print("Likely cause: OpenAI had an issue processing the request.")
        print(
            "Try this: Wait briefly and retry. If it persists, check https://status.openai.com/."
        )
    elif status_code == 503:
        print("Likely cause: OpenAI is temporarily overloaded or unavailable.")
        print(
            "Try this: Wait and retry with backoff. If it persists, check https://status.openai.com/."
        )
    elif status_code:
        print("Likely cause: OpenAI returned an API error.")
        print(
            "Try this: Review the status code and message, then check your API key, model name, quota, billing, and request parameters."
        )


def run_with_anthropic(
    remote_model_name: str,
    remote_api_key: str,
    source_lang: str,
    target_lang: str,
    text: str,
) -> None:
    print(
        f"Requesting translation from {source_lang} to {target_lang} from Anthropic for the following text:"
    )
    print(text)

    import anthropic

    client = anthropic.Anthropic(api_key=remote_api_key)

    try:
        message = client.messages.create(
            model=remote_model_name,
            max_tokens=1024,
            messages=[
                {
                    "role": "assistant",
                    "content": f"I am a {source_lang} to {target_lang} translator and will only translate whatever word, phrase, sentence or sentences the user requests.",
                },
                {"role": "user", "content": text},
            ],
        )
    except anthropic.APITimeoutError as e:
        print_anthropic_error(title="Anthropic request timed out.", e=e)
        raise SystemExit(1)
    except anthropic.APIConnectionError as e:
        print_anthropic_error(title="Could not connect to Anthropic.", e=e)
        raise SystemExit(1)
    except anthropic.APIStatusError as e:
        print_anthropic_error(title="Anthropic returned an API error.", e=e)
        raise SystemExit(1)
    except anthropic.APIError as e:
        print_anthropic_error(title="Anthropic SDK error.", e=e)
        raise SystemExit(1)

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
            "Try this: Wait briefly and retry. For long requests, reduce max tokens or consider using streaming."
        )
    elif isinstance(e, anthropic.APIConnectionError):
        print("Likely cause: The request could not reach Anthropic.")
        print(
            "Try this: Check your network settings, proxy configuration, SSL certificates, or firewall rules."
        )
    elif error_type == "invalid_request_error" or status_code == 400:
        print("Likely cause: The request format or content is invalid.")
        print(
            "Try this: Check the model name, input text, max token value, and request parameters."
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
            "Likely cause: Your API key does not have permission to use the specified resource."
        )
        print(
            "Try this: Check that your key has access to the requested model or resource."
        )
    elif error_type == "not_found_error" or status_code == 404:
        print("Likely cause: The requested model or resource was not found.")
        print(
            "Try this: Check your configured model name and confirm your account has access to it."
        )
    elif error_type == "request_too_large" or status_code == 413:
        print("Likely cause: The request exceeds Anthropic's maximum request size.")
        print(
            "Try this: Reduce the input size or split the request into smaller requests."
        )
    elif error_type == "rate_limit_error" or status_code == 429:
        print("Likely cause: Your account has hit a rate limit or acceleration limit.")
        print(
            "Try this: Slow down requests, wait and retry, or check your Anthropic usage limits."
        )
    elif error_type == "api_error" or status_code == 500:
        print("Likely cause: Anthropic had an internal issue processing the request.")
        print(
            "Try this: Wait briefly and retry. If it persists, check Anthropic service status or contact support."
        )
    elif error_type == "timeout_error" or status_code == 504:
        print("Likely cause: The request timed out while Anthropic was processing it.")
        print(
            "Try this: Reduce request size, lower max tokens, or consider using streaming for long requests."
        )
    elif error_type == "overloaded_error" or status_code == 529:
        print("Likely cause: Anthropic is temporarily overloaded.")
        print("Try this: Wait and retry with backoff.")
    elif status_code or error_type:
        print("Likely cause: Anthropic returned an API error.")
        print(
            "Try this: Review the status code, type, and message, then check your API key, model name, billing, quota, and request parameters."
        )


def run_with_gemini(
    remote_model_name: str,
    remote_api_key: str,
    source_lang: str,
    target_lang: str,
    text: str,
) -> None:
    print(
        f"Requesting translation from {source_lang} to {target_lang} from Gemini for the following text:"
    )
    print(text)

    from google import genai
    from google.genai import errors

    client = genai.Client(api_key=remote_api_key)

    try:
        response = client.models.generate_content(
            model=remote_model_name,
            config=genai.types.GenerateContentConfig(
                system_instruction=f"You are a {source_lang} to {target_lang} translator. Provide only the tranlation of the given text."
            ),
            contents=text,
        )
    except errors.ClientError as e:
        print_gemini_error("Gemini rejected the request.", e)
        raise SystemExit(1)
    except errors.ServerError as e:
        print_gemini_error("Gemini server error.", e)
        raise SystemExit(1)
    except errors.APIError as e:
        print_gemini_error("Gemini API error.", e)
        raise SystemExit(1)

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
                "Try this: Check the model name, input text, request format, and generation config."
            )
        elif code == 401:
            print(
                "Likely cause: The API key is missing, invalid, expired, or from the wrong project."
            )
            print(
                "Try this: Check your configured Gemini API key and generate a new one if needed."
            )
        elif code == 403:
            print(
                "Likely cause: The API key does not have permission, the Gemini API is not enabled, or billing/project access is blocked."
            )
            print(
                "Try this: Confirm the Gemini API is enabled for the right Google Cloud project and that your key has access."
            )
        elif code == 404:
            print("Likely cause: The requested model or resource was not found.")
            print(
                "Try this: Check your configured Gemini model name and confirm it is available for your API version."
            )
        elif code == 429:
            print("Likely cause: You hit a rate limit or quota limit.")
            print(
                "Try this: Wait and retry, reduce request frequency, or check your Gemini quota and billing settings."
            )
        elif code == 500:
            print("Likely cause: Gemini had an internal server error.")
            print(
                "Try this: Wait briefly and retry. If it persists, check Gemini service status."
            )
        elif code == 503:
            print("Likely cause: Gemini is temporarily unavailable or overloaded.")
            print("Try this: Wait and retry with backoff.")
        elif code == 504:
            print("Likely cause: The request timed out while Gemini was processing it.")
            print(
                "Try this: Retry later, reduce request size, or use a shorter prompt/output."
            )
        else:
            print("Likely cause: Gemini returned an API error.")
            print(
                "Try this: Review the status code and message, then check your API key, model name, quota, billing, and request parameters."
            )

    response = getattr(e, "response", None)
    if response:
        print(f"Response: {response}")


def configure_remote_provider(remote_provider: str) -> None:
    supported_providers = tuple(PROVIDER_SPECS.keys())

    if not remote_provider:
        print("Supported providers are:")
        for provider in supported_providers:
            print(provider)

        remote_provider = input("Enter provider: ")

    if remote_provider not in supported_providers:
        raise ValueError(
            f"The remote provider '{remote_provider}' is not supported. Choose one of: {', '.join(supported_providers)}"
        )

    #set_key(".env", "LLM_PROVIDER", remote_provider)
    save_environment_variable(key="LLM_PROVIDER", value=remote_provider)
    os.environ["LLM_PROVIDER"] = remote_provider
    print(f"LLM_PROVIDER set to {remote_provider}")


def configure_remote_api_key() -> None:
    remote_provider = get_configured_remote_provider()

    api_key_env = PROVIDER_SPECS[remote_provider]["api_key_env"]
    remote_api_key = os.environ.get(api_key_env)

    if remote_api_key:
        print(f"Configuring API key for {remote_provider}")
        print(f"The environment variable {api_key_env} already has a value.")
        print(
            "Confirm you want to change it by entering 1. Anything else will skip configuring the API key."
        )
        flag = input("Enter: ").strip()

        if flag != "1":
            return

    remote_api_key = input(f"Enter API key for {remote_provider}: ").strip()

    if not remote_api_key:
        raise ValueError("API key cannot be empty or only white spaces.")

    #set_key(".env", api_key_env, remote_api_key)
    save_environment_variable(key=api_key_env, value=remote_api_key)
    os.environ[api_key_env] = remote_api_key
    print(f"{api_key_env} has been set.")


def configure_remote_model() -> None:
    remote_provider = get_configured_remote_provider()
    remote_api_key = os.environ.get(PROVIDER_SPECS[remote_provider]["api_key_env"])
    remote_model_name = os.environ.get(PROVIDER_SPECS[remote_provider]["model_env"])

    if not remote_api_key:
        configure_remote_api_key()
        remote_api_key = os.environ.get(PROVIDER_SPECS[remote_provider]["api_key_env"])

    if remote_model_name:
        print(
            f"The current model for the provider {remote_provider} is currently {remote_model_name}"
        )
        print("Confirm you want to change it by entering 1, otherwise press enter.")
        flag = input("Enter: ").strip()

        if flag != "1":
            return

    if remote_provider == "openai":
        from openai import OpenAI

        client = OpenAI(api_key=remote_api_key)
        model_ids = [model.id for model in client.models.list().data]

        print("OpenAI was identified as the LLM provider.")
        print("Choose among the following models:")
        for model_id in model_ids:
            print(model_id)

        remote_model_name = ""
        while remote_model_name not in model_ids:
            remote_model_name = input("Input model name: ").strip()

        model_env = PROVIDER_SPECS[remote_provider]["model_env"]
        #set_key(".env", model_env, remote_model_name)
        save_environment_variable(key=model_env, value=remote_model_name)
        os.environ[model_env] = remote_model_name
        print(f"{model_env} has been set to {remote_model_name}")

        return
    elif remote_provider == "anthropic":
        from anthropic import Anthropic

        client = Anthropic(api_key=remote_api_key)
        model_ids = [model.id for model in client.models.list().data]

        print("Anthropic was identified as the LLM provider.")
        print("Choose among the following models:")
        for model in model_ids:
            print(model)

        remote_model_name = ""
        while remote_model_name not in model_ids:
            remote_model_name = input("Input model name: ").strip()

        model_env = PROVIDER_SPECS[remote_provider]["model_env"]
        #set_key(".env", model_env, remote_model_name)
        save_environment_variable(key=model_env, value=remote_model_name)
        os.environ[model_env] = remote_model_name
        print(f"{model_env} has been set to {remote_model_name}")

        return
    elif remote_provider == "gemini":
        from google import genai

        client = genai.Client(api_key=remote_api_key)
        model_ids = [
            model.name
            for model in client.models.list()
            if "generateContent" in model.supported_actions
        ]

        print("Gemini was identified as the LLM provider.")
        print("Choose among the following models:")
        for model in model_ids:
            print(model)

        remote_model_name = ""
        while remote_model_name not in model_ids:
            remote_model_name = input("Input model name: ").strip()

        model_env = PROVIDER_SPECS[remote_provider]["model_env"]
        #set_key(".env", model_env, remote_model_name)
        save_environment_variable(key=model_env, value=remote_model_name)
        os.environ[model_env] = remote_model_name
        print(f"{model_env} has been set to {remote_model_name}")

        return

    raise NotImplementedError(
        f"Model configuration for provider {remote_provider} is not implemented yet."
    )


def get_configured_remote_provider() -> str:
    supported_providers = tuple(PROVIDER_SPECS.keys())
    remote_provider = os.environ.get("LLM_PROVIDER")

    if remote_provider not in supported_providers:
        raise ValueError(
            f"The remote provider '{remote_provider}' is not supported. Use `run_remote config --set_provider` to configure one of: {', '.join(supported_providers)}"
        )

    return remote_provider
