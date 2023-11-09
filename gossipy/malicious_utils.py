import random

from numpy.random import shuffle

from .node import GossipNode
from .malicious_node import MaliciousNode

def create_network(data_dispatcher, p2p_net, model_proto, round_len, sync, malicious_frac=0.3):
## TODO
## Allow to select type of Malicious
## Allow to select type of Gossip node

    nodes = {}

    nb_malicious = int(p2p_net.size()*malicious_frac)
    nb_honest = p2p_net.size() - nb_malicious
    for idx in range(p2p_net.size()):
        if nb_malicious > 0 and nb_honest > 0:
            choix = random.choice([GossipNode, MaliciousNode])
            if choix == MaliciousNode:
                nb_malicious-=1
            elif choix == GossipNode:
                nb_honest-=1
            else:
                raise Exception("Node can only either Gossip or Malicious")
        elif nb_malicious > 0 and nb_honest <= 0:
            choix = MaliciousNode
            nb_malicious-=1
        elif nb_malicious <= 0 and nb_honest > 0:
            choix = GossipNode
            nb_honest-=1
        else:
            raise Exception("Problem in the number of nodes")

        node = choix(idx=idx,
                    data=data_dispatcher[idx], 
                    round_len=round_len, 
                    model_handler=model_proto.copy(), 
                    p2p_net=p2p_net, 
                    sync=sync)
        nodes[idx] = node
    # shuffle(nodes)
    return nodes