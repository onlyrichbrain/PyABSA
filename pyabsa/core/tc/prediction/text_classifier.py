# -*- coding: utf-8 -*-
# file: text_classifier.py
# author: yangheng <yangheng@m.scnu.edu.cn>
# Copyright (C) 2020. All Rights Reserved.

import os
import pickle
import random

import numpy
import torch
from findfile import find_file
from termcolor import colored
from torch.utils.data import DataLoader
from transformers import BertModel, AutoTokenizer

from pyabsa.utils.dataset_utils import detect_infer_dataset

from ..models import GloVeClassificationModelList, BERTClassificationModelList
from ..classic.__glove__.dataset_utils.data_utils_for_inferring import GloVeClassificationDataset
from ..classic.__bert__.dataset_utils.data_utils_for_inferring import BERTClassificationDataset

from ..classic.__glove__.dataset_utils.data_utils_for_training import LABEL_PADDING


class TextClassifier:
    def __init__(self, model_arg=None, label_map=None):
        '''
            from_train_model: load inferring_tutorials model from trained model
        '''

        self.initializers = {
            'xavier_uniform_': torch.nn.init.xavier_uniform_,
            'xavier_normal_': torch.nn.init.xavier_normal,
            'orthogonal_': torch.nn.init.orthogonal_
        }
        # load from a training
        if not isinstance(model_arg, str):
            print('Load text classifier from training')
            self.model = model_arg[0]
            self.opt = model_arg[1]
            self.tokenizer = model_arg[2]
        else:
            # load from a model path
            try:
                print('Load text classifier from', model_arg)
                state_dict_path = find_file(model_arg, '.state_dict')
                model_path = find_file(model_arg, '.model')
                tokenizer_path = find_file(model_arg, '.tokenizer')
                config_path = find_file(model_arg, '.config')
                self.opt = pickle.load(open(config_path, 'rb'))

                if state_dict_path:
                    self.bert = BertModel.from_pretrained(self.opt.pretrained_bert_name)
                    self.model = self.opt.model(self.bert, self.opt)
                    self.model.load_state_dict(torch.load(state_dict_path))

                if model_path:
                    self.model = torch.load(model_path)

                if tokenizer_path:
                    self.tokenizer = pickle.load(open(tokenizer_path, 'rb'))
                else:
                    self.tokenizer = AutoTokenizer.from_pretrained(self.opt.pretrained_bert_name, do_lower_case=True)

                print('Config used in Training:')
                self._log_write_args()

            except Exception as e:
                print(e)
                raise KeyError('Fail to load the model from {}! the checkpoint is broken, '
                               'or maybe the checkpoint is not compatible with this version.'.format(model_arg),
                               )

            if not hasattr(GloVeClassificationModelList, self.model.__class__.__name__) \
                    and not hasattr(BERTClassificationModelList, self.model.__class__.__name__):
                raise KeyError('The checkpoint you are loading is not from classifier model.')

        if hasattr(BERTClassificationModelList, self.opt.model.__name__):
            self.dataset = BERTClassificationDataset(tokenizer=self.tokenizer, opt=self.opt)

        elif hasattr(GloVeClassificationModelList, self.opt.model.__name__):
            self.dataset = GloVeClassificationDataset(tokenizer=self.tokenizer, opt=self.opt)

        self.opt.inputs_cols = self.model.inputs

        self.infer_dataloader = None

        if self.opt.seed is not None:
            random.seed(self.opt.seed)
            numpy.random.seed(self.opt.seed)
            torch.manual_seed(self.opt.seed)
            torch.cuda.manual_seed(self.opt.seed)
            torch.backends.cudnn.deterministic = True
            torch.backends.cudnn.benchmark = False

        self.opt.initializer = self.opt.initializer

        self.label_map = None
        self.set_label_map(label_map)

    def set_label_map(self, label_map):
        if label_map and LABEL_PADDING not in label_map:
            label_map[LABEL_PADDING] = ''
        self.label_map = label_map

    def to(self, device=None):
        self.opt.device = device
        self.model.to(device)

    def cpu(self):
        self.opt.device = 'cpu'
        self.model.to('cpu')

    def cuda(self, device='cuda:0'):
        self.opt.device = device
        self.model.to(device)

    def _log_write_args(self):
        n_trainable_params, n_nontrainable_params = 0, 0
        for p in self.model.parameters():
            n_params = torch.prod(torch.tensor(p.shape))
            if p.requires_grad:
                n_trainable_params += n_params
            else:
                n_nontrainable_params += n_params
        print(
            'n_trainable_params: {0}, n_nontrainable_params: {1}'.format(n_trainable_params, n_nontrainable_params))
        for arg in vars(self.opt):
            if getattr(self.opt, arg) is not None:
                print('>>> {0}: {1}'.format(arg, getattr(self.opt, arg)))

    def batch_infer(self,
                    target_file=None,
                    print_result=True,
                    save_result=False,
                    clear_input_samples=True,
                    ignore_error=True):

        if clear_input_samples:
            self.clear_input_samples()

        save_path = os.path.join(os.getcwd(), 'inference.result.txt')

        target_file = detect_infer_dataset(target_file, task='tc')
        if not target_file:
            raise FileNotFoundError('Can not find inference dataset_utils!')

        self.dataset.prepare_infer_dataset(target_file, ignore_error=ignore_error)
        self.infer_dataloader = DataLoader(dataset=self.dataset, batch_size=1, shuffle=False)
        return self._infer(save_path=save_path if save_result else None, print_result=print_result)

    def infer(self, text: str = None,
              print_result=True,
              clear_input_samples=True):

        if clear_input_samples:
            self.clear_input_samples()
        if text:
            self.dataset.prepare_infer_sample(text)
        else:
            raise RuntimeError('Please specify your dataset_utils path!')
        self.infer_dataloader = DataLoader(dataset=self.dataset, batch_size=1, shuffle=False)
        return self._infer(print_result=print_result)

    def _infer(self, save_path=None, print_result=True):

        _params = filter(lambda p: p.requires_grad, self.model.parameters())

        if self.label_map:
            label_map = self.label_map
        elif self.opt.polarities_dim == 3:
            label_map = {0: 'Negative', 1: "Neutral", 2: 'Positive', LABEL_PADDING: ''}
        else:
            label_map = {p: p for p in range(self.opt.polarities_dim)}
            label_map[LABEL_PADDING] = ''
        correct = {True: 'Correct', False: 'Wrong'}
        results = []
        if save_path:
            fout = open(save_path, 'w', encoding='utf8')
        with torch.no_grad():
            self.model.eval()
            n_correct = 0
            n_labeled = 0
            n_total = 0
            for _, sample in enumerate(self.infer_dataloader):
                result = {}
                inputs = [sample[col].to(self.opt.device) for col in self.opt.inputs_cols]
                self.model.eval()
                outputs = self.model(inputs)
                sen_logits = outputs
                t_probs = torch.softmax(sen_logits, dim=-1).cpu().numpy()
                sent = int(t_probs.argmax(axis=-1))
                real_sent = int(sample['label'])
                text_raw = sample['text_raw'][0]

                result['text'] = sample['text_raw'][0]
                result['label'] = int(t_probs.argmax(axis=-1))
                result['ref_label'] = label_map[real_sent]
                result['infer result'] = correct[sent == real_sent]
                results.append(result)
                if real_sent == -999:
                    colored_pred_info = '{} --> {}'.format('Label', label_map[sent])
                else:
                    n_labeled += 1
                    if sent == real_sent:
                        n_correct += 1
                    pred_res = correct[sent == real_sent]
                    colored_pred_res = colored(pred_res, 'green') if pred_res == 'Correct' else colored(pred_res, 'red')
                    colored_label = colored('Label', 'magenta')
                    colored_pred_info = '{} --> {}  Real: {} ({})'.format(colored_label,
                                                                          label_map[sent],
                                                                          label_map[real_sent],
                                                                          colored_pred_res
                                                                          )
                n_total += 1
                try:
                    if save_path:
                        fout.write(text_raw + '\n')
                        pred_info = '{} --> {}  Real: {} ({})'.format('Label',
                                                                      label_map[sent],
                                                                      label_map[real_sent],
                                                                      pred_res
                                                                      )
                        fout.write(pred_info + '\n')
                except:
                    print('Can not save result: {}'.format(text_raw))
                try:
                    if print_result:
                        print(text_raw)
                        print(colored_pred_info)
                except UnicodeError as e:
                    print(colored('Encoding Error, you should use UTF8 encoding, e.g., use: os.environ["PYTHONIOENCODING"]="UTF8"'))
            print('Total samples:{}'.format(n_total))
            print('Labeled samples:{}'.format(n_labeled))
            print('Prediction Accuracy:{}%'.format(100 * n_correct / n_labeled if n_labeled else 'N.A.'))

            try:
                if save_path:
                    fout.write('Total samples:{}\n'.format(n_total))
                    fout.write('Labeled samples:{}\n'.format(n_labeled))
                    fout.write('Prediction Accuracy:{}%\n'.format(100 * n_correct / n_labeled))
                    print('inference result saved in: {}'.format(save_path))
            except:
                pass
        if save_path:
            fout.close()
        return results

    def clear_input_samples(self):
        self.dataset.all_data = []
