# -*- coding: utf-8 -*-
# Project : DEASQL
# File    : sql.py
# Author  : 
# Email   : 
# Time    : 2023/10/23 21:50

from enum import Enum


class SqlType(Enum):
    SINGLE_TABLE = 'single'
    MULTI_TABLE = 'multi'


class DatasetType(Enum):
    BIRD = 'bird'
    SPIDER = 'spider'


class QuestionType(Enum):
    EASY = 'EASY'
    NESTED = 'NESTED'
    JOIN = 'JOIN'  # only JOIN
    JOIN_NESTED = 'JOIN-NESTED'  # JOIN and NESTED


class AggregationType(Enum):
    MAX = 'MAX'
    MIN = 'MIN'
    SUM = 'SUM'
    AVG = 'AVG'
    COUNT = 'COUNT'
    NON = 'NON'


class AggrType(Enum):
    """
        aggr type
    """
    NEEDED = 'NEEDED'
    NON_NEEDED = 'NON-NEEDED'


class FilterType(Enum):
    SIMPLE = 'simple'
    SIMPLE_V2 = 'simple_v2'
    COMPLEX = 'complex'
    NONE = 'none'  # no filter


class LLM:
    # openai LLMs
    TEXT_DAVINCI_003 = "text-davinci-003"
    CODE_DAVINCI_002 = "code-davinci-002"
    GPT_35_TURBO = "gpt-3.5-turbo"
    GPT_35_TURBO_0613 = "gpt-3.5-turbo-0613"
    GPT_35_TURBO_16K = "gpt-3.5-turbo-16k"
    GPT_35_TURBO_0301 = "gpt-3.5-turbo-0301"
    GPT_4 = "gpt-4"

    # LLMs that use openai completion api
    TASK_COMPLETIONS = [
        TEXT_DAVINCI_003,
        CODE_DAVINCI_002
    ]

    # LLMs that use openai chat api
    TASK_CHAT = [
        GPT_35_TURBO,
        GPT_35_TURBO_0613,
        GPT_35_TURBO_16K,
        GPT_35_TURBO_0301,
        GPT_4
    ]

    # LLMs that can run in batch
    BATCH_FORWARD = [
        TEXT_DAVINCI_003,
        CODE_DAVINCI_002
    ]

    costs_per_thousand = {
        TEXT_DAVINCI_003: 0.0200,
        CODE_DAVINCI_002: 0.0200,
        GPT_35_TURBO: 0.0020,
        GPT_35_TURBO_0613: 0.0020,
        GPT_35_TURBO_16K: 0.003,
        GPT_35_TURBO_0301: 0.0020,
        GPT_4: 0.03
    }

    # local LLMs
    LLAMA_7B = "llama-7b"
    ALPACA_7B = "alpaca-7b"
    TONG_YI_QIAN_WEN = "qwen-v1"
