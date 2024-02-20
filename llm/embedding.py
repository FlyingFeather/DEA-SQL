# -*- coding: utf-8 -*-
# @Author : 
# @Email : 
# @Time : 2023/11/23 14:55
import backoff
import openai
import requests
from common.config.static_config import CONFIG


# embedding model
TEXT_EMBEDDING_ADA_002 = 'text-embedding-ada-002'


def quota_giveup(e):
    return isinstance(e, openai.error.RateLimitError) and "quota" in str(e)


@backoff.on_exception(
    backoff.constant,
    openai.error.OpenAIError,
    giveup=quota_giveup,
    raise_on_giveup=True,
    interval=20
)
def get_openai_embed(model, input):
    openai.api_key = CONFIG['emb_api_key']
    openai.api_type = "azure"
    openai.api_base = "https://gpt-jp-az.openai.azure.com/"
    openai.api_version = "2023-05-15"
    openai.debug = True
    with requests.Session() as session:
        openai.requestssession = session
        try:
            response = openai.Embedding.create(
                engine=model, input=input)
            result = [e['embedding'] for e in response['data']]
        except Exception as e:
            result = 'error:{}'.format(e)
            print(result)
    return result


if __name__ == '__main__':
    embed = get_openai_embed(TEXT_EMBEDDING_ADA_002, ['hello', 'world'])
    print(embed)
    embed = get_openai_embed(TEXT_EMBEDDING_ADA_002, ['hello world'])
    print(embed)
    embed = get_openai_embed(TEXT_EMBEDDING_ADA_002, 'hello world')
    print(embed)

