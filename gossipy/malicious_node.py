from typing import Optional, Union, Tuple
from torch import Tensor
from torch.nn import Parameter
from numpy import ndarray

from . import CACHE
from .core import AntiEntropyProtocol, MessageType, Message, P2PNetwork
from .model.handler import ModelHandler
from .node import GossipNode

# AUTHORSHIP
__version__ = "0.0.1"
__author__ = "Mohamed Amine LEGHERABA"
__copyright__ = "Copyright 2023, gossipy"
__license__ = "Apache License, Version 2.0"
__maintainer__ = "Mohamed Amine LEGHERABA, PhD candidate"
__email__ = "mlegheraba@protonmail.com"
__status__ = "Development"
#

__all__ = ["MaliciousNode"]

class MaliciousNode(GossipNode):
    def __init__(self,
                 idx: int, #node's id
                 data: Union[Tuple[Tensor, Optional[Tensor]],
                             Tuple[ndarray, Optional[ndarray]]], #node's data
                 round_len: int, #round length
                 model_handler: ModelHandler, #object that handles the model learning/inference
                 p2p_net: P2PNetwork,
                 sync=True):
        r"""Malicious node.
        
        """
        super(MaliciousNode, self).__init__(idx,
                                              data,
                                              round_len,
                                              model_handler,
                                              p2p_net,
                                              sync)

    # docstr-coverage:inherited
    def send(self,
             t: int,
             peer: int,
             protocol: AntiEntropyProtocol) -> Union[Message, None]:
        if protocol == AntiEntropyProtocol.PUSH:
            self.true_model = self.model_handler.model.model
            self.model_handler.model.model = Parameter(0 * self.model_handler.model.model, requires_grad=False)
            key = self.model_handler.caching(self.idx)
            return Message(t, self.idx, peer, MessageType.PUSH, (key,))
        elif protocol == AntiEntropyProtocol.PULL:
            return Message(t, self.idx, peer, MessageType.PULL, None)
        elif protocol == AntiEntropyProtocol.PUSH_PULL:
            self.true_model = self.model_handler.model.model
            self.model_handler.model.model = Parameter(0 * self.model_handler.model.model, requires_grad=False)
            key = self.model_handler.caching(self.idx)
            return Message(t, self.idx, peer, MessageType.PUSH_PULL, (key,))
        else:
            raise ValueError("Unknown protocol %s." %protocol)

    def receive(self, t: int, msg: Message) -> Union[Message, None]:
        msg_type: MessageType
        recv_model: Any 
        msg_type, recv_model = msg.type, msg.value[0] if msg.value else None
        if msg_type == MessageType.PUSH or \
           msg_type == MessageType.REPLY or \
           msg_type == MessageType.PUSH_PULL:
            recv_model = CACHE.pop(recv_model)
            self.model_handler.model.model = self.true_model
            self.model_handler(recv_model, self.data[0])

        if msg_type == MessageType.PULL or \
           msg_type == MessageType.PUSH_PULL:
            self.true_model = self.model_handler.model.model
            self.model_handler.model.model = Parameter(0 * self.model_handler.model.model, requires_grad=False)
            key = self.model_handler.caching(self.idx)
            return Message(t, self.idx, msg.sender, MessageType.REPLY, (key,))
        return None
        
    # def evaluate(self, ext_data: Optional[Any]=None) -> Dict[str, float]:
    #     """Evaluates the local model.

    #     Parameters
    #     ----------
    #     ext_data : Any, default=None
    #         The data to be used for evaluation. If `None`, the local test data will be used.
        
    #     Returns
    #     -------
    #     dict[str, float]
    #         The evaluation results. The keys are the names of the metrics and the values are
    #         the corresponding values.
    #     """

    #     if ext_data is None:
    #         return self.model_handler.evaluate(self.data[1])
    #     else:
    #         return self.model_handler.evaluate(ext_data)