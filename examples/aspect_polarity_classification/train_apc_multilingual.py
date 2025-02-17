# -*- coding: utf-8 -*-
# file: train_apc_multilingual.py
# time: 2021/5/26 0026
# author: yangheng <yangheng@m.scnu.edu.cn>
# github: https://github.com/yangheng95
# Copyright (C) 2021. All Rights Reserved.

########################################################################################################################
#                    train and evaluate on your own apc_datasets (need train and test apc_datasets)                    #
#              your custom dataset_utils should have the continue polarity labels like [0,N-1] for N categories              #
########################################################################################################################


from pyabsa.functional import Trainer
from pyabsa.functional import APCConfigManager
from pyabsa.functional import ABSADatasetList
from pyabsa.functional import APCModelList

save_path = 'state_dict'
apc_config_multilingual = APCConfigManager.get_apc_config_multilingual()
apc_config_multilingual.model = APCModelList.FAST_LCF_BERT
apc_config_multilingual.evaluate_begin = 3

datasets_path = 'datasets/apc_datasets/multilingual'  # file or dir are accepted for 'datasets_path'
sent_classifier = Trainer(config=apc_config_multilingual,  # set config=None to use default model
                          dataset=datasets_path,  # train set and test set will be automatically detected
                          save_checkpoint=True,  # set model_path_to_save=None to avoid save model
                          auto_device=True  # automatic choose CUDA or CPU
                          )
