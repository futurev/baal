from copy import deepcopy
from typing import Dict, List

import torch
from torch import nn

from baal import ModelWrapper
from baal.modelwrapper import _stack_preds
from baal.utils.cuda_utils import to_cuda


class EnsembleModelWrapper(ModelWrapper):
    """
    Wrapper that support ensembles with the same architecture.

    Args:
        model (nn.Module): A Model.
        criterion (Callable): Loss function
    """

    def __init__(self, model, criterion):
        super().__init__(model, criterion)
        self._weights = []

    def add_checkpoint(self):
        """
        Add a checkpoint to the list of weights used for inference.
        """
        self._weights.append(deepcopy(self.model.state_dict()))

    def predict_on_batch(self, data, iterations=1, cuda=False):
        """
        Get the model's prediction on a batch.

        Args:
            data (Tensor): The model input.
            iterations (int): NOT USED
            cuda (bool): Use CUDA or not.

        Returns:
            Tensor, the loss computed from the criterion.
                    shape = {batch_size, nclass, n_iteration}.

        Raises:
            Raises RuntimeError if CUDA rans out of memory during data replication.
        """
        return ensemble_prediction(model=self.model, data=data, weigths=self._weights, cuda=cuda)


def ensemble_prediction(data: torch.Tensor, model: nn.Module, weigths: List[Dict], cuda: bool):
    """
        Get the model's prediction on a batch.

        Args:
            data (Tensor): The model input.
            model (nn.Module): The model to use.
            weigths (List[Dict]): List of all weights to use.
            cuda (bool): Use CUDA or not.

        Returns:
            Tensor, the loss computed from the criterion.
                    shape = {batch_size, nclass, n_iteration}.
    """
    with torch.no_grad():
        if cuda:
            data = to_cuda(data)
        res = []
        for w in weigths:
            model.load_state_dict(w)
            res.append(model(data))
        out = _stack_preds(res)

        return out
