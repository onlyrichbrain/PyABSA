# -*- coding: utf-8 -*-
# file: extract_aspects_chinese.py
# time: 2021/5/27 0027
# author: yangheng <hy345@exeter.ac.uk>
# github: https://github.com/yangheng95
# Copyright (C) 2021. All Rights Reserved.
import pandas as pd

from pyabsa import ATEPCCheckpointManager, ABSADatasetList, available_checkpoints

# checkpoint_map = available_checkpoints(from_local=False)

examples1 = [
    "照 大 尺 寸 的 照 片 的 时 候 手 机 反 映 速 度 太 慢",
    "关 键 的 时 候 需 要 表 现 持 续 影 像 的 短 片 功 能 还 是 很 有 用 的",
    "相 比 较 原 系 列 锐 度 高 了 不 少 这 一 点 好 与 不 好 大 家 有 争 议",
    "相比较原系列锐度高了不少这一点好与不好大家有争议",
    "这款手机的大小真的很薄，但是颜色不太好看， 总体上我很满意啦。",
]

# 从Google Drive下载提供的预训练模型
aspect_extractor = ATEPCCheckpointManager.get_aspect_extractor(
    checkpoint="chinese", eval_batch_size=256
)

# examples = examples1
examples = ABSADatasetList.Chinese
res = aspect_extractor.extract_aspect(
    inference_source=examples,  # list-support only, for now
    print_result=True,  # print the result
    pred_sentiment=True,  # Predict the sentiment of extracted aspect terms
)
