from numpy.random import shuffle

from .node import GossipNode
from .malicious_node import MaliciousNode

def create_network(data_dispatcher, p2p_net, model_proto, round_len, sync, malicious_frac=0.3):
    nodes = {}
    nb_malicious = int(p2p_net.size()*malicious_frac)
    nb_honest = p2p_net.size() - nb_malicious
    for idx, _ in enumerate(range(nb_malicious)):
        node = MaliciousNode(idx=idx,
                    data=data_dispatcher[idx], 
                    round_len=round_len, 
                    model_handler=model_proto.copy(), 
                    p2p_net=p2p_net, 
                    sync=sync)
        nodes[idx] = node
    for idx, _ in enumerate(range(nb_honest), start=nb_malicious):
        node = GossipNode(idx=idx,
                    data=data_dispatcher[idx], 
                    round_len=round_len, 
                    model_handler=model_proto.copy(), 
                    p2p_net=p2p_net, 
                    sync=sync)
        nodes[idx] = node
    shuffle(nodes)
    return nodes