import numpy as np
from numpy.random import shuffle, random, choice
from typing import DefaultDict, Dict, List
from rich.progress import track

from . import LOG
from .core import AntiEntropyProtocol, Message, ConstantDelay, Delay
from .data import DataDispatcher
from .node import GossipNode

from .simul import GossipSimulator

# AUTHORSHIP
__version__ = "0.0.1"
__author__ = "Mohamed Amine LEGHERABA"
__copyright__ = "Copyright 2023, gossipy"
__license__ = "Apache License, Version 2.0"
__maintainer__ = "Mohamed Amine LEGHERABA, PhD candidate"
__email__ = "mlegheraba@protonmail.com"
__status__ = "Development"
#

__all__ = ["GossipSimulatorMalicious"]

class GossipSimulatorMalicious(GossipSimulator):
    def __init__(self,
                 nodes: Dict[int, GossipNode],
                 data_dispatcher: DataDispatcher,
                 delta: int,
                 protocol: AntiEntropyProtocol,
                 drop_prob: float=0., # [0,1] - probability of a message being dropped
                 online_prob: float=1., # [0,1] - probability of a node to be online
                 delay: Delay=ConstantDelay(0),
                 sampling_eval: float=0., # [0, 1] - percentage of nodes to evaluate
                ):
        super(GossipSimulatorMalicious, self).__init__(nodes,
                                                       data_dispatcher,
                                                       delta,
                                                       protocol,
                                                       drop_prob,
                                                       online_prob,
                                                       delay,
                                                       sampling_eval)

    def start(self, n_rounds: int=100) -> None:
        """Starts the simulation.

        The simulation handles the messages exchange between the nodes for ``n_rounds`` rounds.
        If attached to a :class:`SimulationReport`, the report is updated at each time step, 
        sent/fail message and evaluation.

        Parameters
        ----------
        n_rounds : int, default=100
            The number of rounds of the simulation.
        """

        assert self.initialized, \
               "The simulator is not inizialized. Please, call the method 'init_nodes'."
        LOG.info("Simulation started.")
        node_ids = np.arange(self.n_nodes)
        
        pbar = track(range(n_rounds * self.delta), description="Simulating...")
        msg_queues = DefaultDict(list)
        rep_queues = DefaultDict(list)

        try:
            for t in pbar:
                if t % self.delta == 0: 
                    shuffle(node_ids)
                    
                for i in node_ids:
                    node = self.nodes[i]
                    if node.timed_out(t):

                        peer = node.get_peer()
                        if peer is None:
                            break
                        msg = node.send(t, peer, self.protocol)
                        self.notify_message(False, msg)
                        if msg:
                            if random() >= self.drop_prob:
                                d = self.delay.get(msg)
                                msg_queues[t + d].append(msg)
                            else:
                                self.notify_message(True)
                
                is_online = random(self.n_nodes) <= self.online_prob
                for msg in msg_queues[t]:
                    if is_online[msg.receiver]:
                        reply = self.nodes[msg.receiver].receive(t, msg)
                        if reply:
                            if random() > self.drop_prob:
                                d = self.delay.get(reply)
                                rep_queues[t + d].append(reply)
                            else:
                                self.notify_message(True)
                    else:
                        self.notify_message(True)
                del msg_queues[t]

                for reply in rep_queues[t]:
                    if is_online[reply.receiver]:
                        self.notify_message(False, reply)
                        self.nodes[reply.receiver].receive(t, reply)
                    else:
                        self.notify_message(True)
                    
                del rep_queues[t]

                if (t+1) % self.delta == 0:
                    nodes_report = {k: v for k, v in self.nodes.items() if type(v) == GossipNode}
                    nodes_report_nb = len(nodes_report)
                    if self.sampling_eval > 0:
                        sample = choice(list(nodes_report.keys()),
                                        max(int(nodes_report_nb * self.sampling_eval), 1))
                        ev = [nodes_report[i].evaluate() for i in sample if nodes_report[i].has_test()]
                    else:
                        ev = [n.evaluate() for _, n in nodes_report.items() if n.has_test()]
                    if ev:
                        self.notify_evaluation(t, True, ev)
                    
                    if self.data_dispatcher.has_test():
                        if self.sampling_eval > 0:
                            ev = [nodes_report[i].evaluate(self.data_dispatcher.get_eval_set())
                                for i in sample]
                        else:
                            ev = [n.evaluate(self.data_dispatcher.get_eval_set())
                                for _, n in nodes_report.items()]
                        if ev:
                            self.notify_evaluation(t, False, ev)
                self.notify_timestep(t)

        except KeyboardInterrupt:
            LOG.warning("Simulation interrupted by user.")
        
        pbar.close()
        self.notify_end()
        return
    
