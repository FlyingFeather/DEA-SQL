import json
import time

import backoff
import openai
from argsparser import parser
from common.config.static_config import CONFIG

args = parser.parse_args()

openai.debug = True


def quota_giveup(e):
    return isinstance(e, openai.error.RateLimitError) and "quota" in str(e)


@backoff.on_exception(
    backoff.constant,
    openai.error.OpenAIError,
    giveup=quota_giveup,
    raise_on_giveup=True,
    interval=20
)
def connect_gpt(engine, api_key, api_base, prompt, max_tokens, temperature, stop=None, task="chat"):
    openai.api_key = api_key
    openai.api_type = "azure"
    openai.api_base = api_base
    openai.api_version = "2023-05-15"
    n_repeat = 0
    while True:
        try:
            if task == "chat":
                response = openai.ChatCompletion.create(
                    engine=engine, messages=[{"role": "user", "content": f"{prompt}"}], temperature=temperature)
                result = response['choices'][0]['message']['content']

            elif task == "completion":
                response = openai.Completion.create(engine=engine, prompt=prompt,
                                                    max_tokens=max_tokens, temperature=temperature, stop=stop)
                result = response['choices'][0]['text']
            break
        except openai.error.RateLimitError:
            n_repeat += 1
            print(f"Repeat for the {n_repeat} times for RateLimitError", end="\n")
            time.sleep(1)
            if n_repeat >= 30:
                result = f"error, exception: RateLimitError"
                break
            continue
        except json.decoder.JSONDecodeError:
            n_repeat += 1
            print(f"Repeat for the {n_repeat} times for JSONDecodeError", end="\n")
            time.sleep(1)
            if n_repeat >= 10:
                result = f"error, exception: JSONDecodeError"
                break
            continue
        except Exception as e:
            n_repeat += 1
            print(f"Repeat for the {n_repeat} times for exception: {e}", end="\n")
            time.sleep(1)
            if n_repeat >= 10:
                result = f"error, exception: {e}"
                break
            continue
    return result


def ask_llm(prompt, temp=None):
    key_config = args.key_config
    key_version = args.key_version  # gpt-35-turbo, gpt-4
    api_key = CONFIG[key_config]["api_key"]
    api_base = CONFIG[key_config]["api_base"]
    engine = key_version
    model_name = key_version
    temperature = CONFIG["methods"]["temperature"]
    if temp is not None:
        temperature = temp
    max_tokens = CONFIG["max_tokens"]
    return connect_gpt(engine, api_key, api_base, prompt, max_tokens, temperature)
