# -*- coding: utf-8 -*-
# file: run_test.py
# time: 2021/12/4
# author: yangheng <hy345@exeter.ac.uk>
# github: https://github.com/yangheng95
# Copyright (C) 2021. All Rights Reserved.
import shutil

from torch import cuda

from pyabsa import (
    APCModelList,
    BERTBaselineAPCModelList,
    GloVeAPCModelList,
    ATEPCModelList,
    BERTTCModelList,
    GloVeTCModelList,
)
from pyabsa import ABSADatasetList, TCDatasetList
from pyabsa import APCConfigManager
from pyabsa import ATEPCConfigManager
from pyabsa import TCConfigManager
from pyabsa.functional import Trainer

from findfile import find_cwd_dir

import warnings

warnings.filterwarnings("ignore")

#######################################################################################################
#                                  This script is used for basic test                                 #
#                         The config test are ignored due to computation limitation                   #
#######################################################################################################

atepc_examples = [
    "But the staff was so nice to us .",
    "But the staff was so horrible to us .",
    r"Not only was the food outstanding , but the little ` perks \' were great .",
    "It took half an hour to get our check , which was perfect since we could sit , have drinks and talk !",
    "It was pleasantly uncrowded , the service was delightful , the garden adorable , "
    "the food -LRB- from appetizers to entrees -RRB- was delectable .",
    "How pretentious and inappropriate for MJ Grill to claim that it provides power lunch and dinners !",
]

apc_examples = [
    "Strong build though which really adds to its [ASP]durability[ASP] .",  # !sent! Positive
    "Strong [ASP]build[ASP] though which really adds to its durability . !sent! Positive",
    "The [ASP]battery life[ASP] is excellent - 6-7 hours without charging . !sent! Positive",
    "I have had my computer for 2 weeks already and it [ASP]works[ASP] perfectly . !sent! Positive",
    "And I may be the only one but I am really liking [ASP]Windows 8[ASP] . !sent! Positive",
]

# # for dataset in ABSADatasetList():
for dataset in ABSADatasetList()[:1] + [ABSADatasetList.MAMS]:
    for model in ATEPCModelList():
        config = ATEPCConfigManager.get_atepc_config_english()
        cuda.empty_cache()
        config.model = model
        config.cache_dataset = True
        config.num_epoch = 1
        config.evaluate_begin = 0
        config.max_seq_len = 10
        config.log_step = -1
        config.ate_loss_weight = 5
        config.show_metric = -1
        aspect_extractor = Trainer(
            config=config,
            dataset=dataset,
            checkpoint_save_mode=1,
            auto_device="allcuda",
        ).load_trained_model()
        aspect_extractor.extract_aspect(
            inference_source=atepc_examples,  #
            save_result=True,
            print_result=True,  # print the result
            pred_sentiment=True,  # Predict the sentiment of extracted aspect terms
        )
        try:
            shutil.rmtree(find_cwd_dir("checkpoints"))
        except Exception as e:
            print(e)

for dataset in TCDatasetList():
    for model in BERTTCModelList():
        cuda.empty_cache()
        config = TCConfigManager.get_tc_config_english()
        config.model = model
        config.num_epoch = 1
        config.evaluate_begin = 0
        config.max_seq_len = 10
        config.log_step = -1
        text_classifier = Trainer(
            config=config,
            dataset=dataset,
            checkpoint_save_mode=1,
            auto_device="allcuda",
        ).load_trained_model()
        text_classifier.infer("I love it very much!")
        try:
            shutil.rmtree(find_cwd_dir("checkpoints"))
            del text_classifier
            cuda.empty_cache()
        except Exception as e:
            print(e)
