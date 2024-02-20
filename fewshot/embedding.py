# -*- coding: utf-8 -*-
# @Author : 
# @Email : 
# @Time : 2023/11/23 14:19
from typing import List, Union
from transformers import AutoModel, AutoTokenizer

from llm.embedding import get_openai_embed
from llm.embedding import TEXT_EMBEDDING_ADA_002


def embed_by_openai(text: Union[List, str]):
    return get_openai_embed(TEXT_EMBEDDING_ADA_002, text)


def embed_by_transformers(text: Union[List, str]):
    model_name = "bert-base-uncased"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModel.from_pretrained(model_name)

    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True, max_length=128)
    output = model(**inputs)
    embed = output.last_hidden_state.mean(dim=1).detach()

    return embed.numpy()


if __name__ == '__main__':
    # test openai embedding
    print(embed_by_openai('hello word'))
    print(embed_by_openai(['hello word']))

    # test transformers embedding
    print(embed_by_transformers('hello word'))
    print(embed_by_transformers(['hello word']))
