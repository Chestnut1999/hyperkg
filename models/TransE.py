# 
#  Copyright (c) 2018-present, the Authors of the OpenKE-PyTorch (old).
#  All rights reserved.
#
#  Link to the project: https://github.com/thunlp/OpenKE/tree/OpenKE-PyTorch(old)
#

import torch
import torch.autograd as autograd
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
import numpy as np
from .Model import Model
from torch.autograd import Variable


class TransE(Model):

	def __init__(self, config):
		super(TransE,self).__init__(config)
		self.ent_embeddings=nn.Embedding(config.entTotal,config.hidden_size)
		self.rel_embeddings=nn.Embedding(config.relTotal,config.hidden_size)
		self.init_weights()

	def init_weights(self):
		nn.init.xavier_uniform(self.ent_embeddings.weight.data)
		nn.init.xavier_uniform(self.rel_embeddings.weight.data)
	
	r'''
	TransE is the first model to introduce translation-based embedding, 
	which interprets relations as the translations operating on entities.
	'''
	def _calc(self,h,t,r):
		return torch.abs(h + r - t)

	# margin-based loss
	def loss_func(self,p_score,n_score):
		criterion = self.cuda_transform(nn.MarginRankingLoss(self.config.margin, False))
		y = self.cuda_transform(Variable(torch.Tensor([-1])))
		loss = criterion(p_score,n_score,y)
		return loss

	def forward(self):
		pos_h,pos_t,pos_r=self.get_postive_instance()
		neg_h,neg_t,neg_r=self.get_negtive_instance()
		p_h=self.ent_embeddings(pos_h)
		p_t=self.ent_embeddings(pos_t)
		p_r=self.rel_embeddings(pos_r)
		n_h=self.ent_embeddings(neg_h)
		n_t=self.ent_embeddings(neg_t)
		n_r=self.rel_embeddings(neg_r)
		_p_score = self._calc(p_h, p_t, p_r)
		_n_score = self._calc(n_h, n_t, n_r)
		_p_score = _p_score.view(-1, 1, self.config.hidden_size)
		_n_score = _n_score.view(-1, self.config.negative_ent + self.config.negative_rel, self.config.hidden_size)
		p_score=torch.sum(torch.mean(_p_score, 1),1)
		n_score=torch.sum(torch.mean(_n_score, 1),1)
		loss=self.loss_func(p_score, n_score)
		return loss

	def predict(self, predict_h, predict_t, predict_r):
		p_h=self.ent_embeddings(self.cuda_transform(Variable(torch.from_numpy(np.asarray(predict_h, dtype=np.int64)))))
		p_t=self.ent_embeddings(self.cuda_transform(Variable(torch.from_numpy(np.asarray(predict_t, dtype=np.int64)))))
		p_r=self.rel_embeddings(self.cuda_transform(Variable(torch.from_numpy(np.asarray(predict_r, dtype=np.int64)))))
		_p_score = self._calc(p_h, p_t, p_r)
		p_score=torch.sum(_p_score,1)
		return p_score.cpu()
