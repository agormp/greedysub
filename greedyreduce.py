#!/usr/bin/env python3
import argparse, sys, itertools
from collections import defaultdict
from operator import itemgetter

################################################################################################

def main():
    parser = build_parser()
    args = parse_commandline(parser)
    graph = NeighborGraph(args)

    # If input has no neighbors: do nothing, print results. Otherwise: proceed
    if graph.max_degree > 0:
        if args.keepfile:
            graph.remove_keepfile_neighbors()

        if args.frombottom:
            graph.reduce_from_bottom()
        else:
            graph.reduce_from_top()

    graph.write_results(args)

################################################################################################

def build_parser():
    parser = argparse.ArgumentParser(description = "Selects subset of items based on" +
                                    " list of pairwise similarities (or distances), such that no" +
                                    " retained items are close neighbors")

    parser.add_argument("infile", metavar='INFILE', default="-",
                        help="input file containing the similarity (option -s) or distance " +
                             "(option -d) for each pair of items: name1 name2 value")

    parser.add_argument("outfile", metavar='OUTFILE', default="-",
                        help="output file contatining reduced subset of names (one name per line).")

    distsimgroup = parser.add_mutually_exclusive_group()
    distsimgroup.add_argument('-s', action='store_true', dest="values_are_sim",
                              help="values in INFILE are similarities " +
                                    "(larger values = more similar)")
    distsimgroup.add_argument('-d', action='store_true', dest="values_are_dist",
                              help="values in INFILE are distances " +
                                    "(smaller values = more similar)")

    algorithmgroup = parser.add_mutually_exclusive_group()
    algorithmgroup.add_argument('-b', "--frombottom", action='store_true',
                              help="iteratively remove neighbors of least connected node, until no neighbors left")
    algorithmgroup.add_argument('-t', "--fromtop", action='store_true',
                              help="iteratively remove most connected node, until no neighbors left")

    parser.add_argument("-c",  action="store", type=float, dest="cutoff", metavar="CUTOFF",
                          help="cutoff for deciding which pairs are neighbors")

    parser.add_argument("-k", action="store", dest="keepfile", metavar="KEEPFILE",
                          help="(optional) file with names of items that must be kept (one name per line)")
    parser.add_argument('--check', action='store_true', dest="check",
                              help="check validity of input data: Are all pairs listed? "
                                    + "Are A B distances the same as B A?  "
                                    + "If yes: finish run and print results. "
                                    + "If no: abort run with error message")

    return parser

################################################################################################

def parse_commandline(parser):

    args = parser.parse_args()
    if ((args.values_are_sim and args.values_are_dist) or
       ((not args.values_are_sim ) and (not args.values_are_dist))):
        parser.error("Must specify either option -s (similarity) or option -d (distance)")
    if ((args.frombottom and args.fromtop) or
       ((not args.frombottom ) and (not args.fromtop))):
        parser.error("Must specify either option -b (from bottom) or option -t (from top)")
    if args.cutoff is None:
        parser.error("Must provide cutoff (option -c)")
    return(args)

################################################################################################
################################################################################################

class NeighborGraph:
    """Stores information about nodes and their connections.
    Methods for interrogating and changing graph"""

    def __init__(self, args):

        # self.neighbors: dict(node:set(node's neighbors))
        # self.neighbor_count: dict(node:count of node's neighbors)
        # Note: only nodes WITH neighbors are keys in these two dicts
        # Note 2: these dicts are changed by algorithm during iteration

        # self.nodes: set(all nodes)
        # self.origdata["orignum"]: number of nodes in graph before reducing
        # self.origdata["average_degree"]: average no. connections to a node before reducing
        # self.origdata["max/min_degree"]: max/min no. connections to a node before reducing
        # self.origdata["average_dist"]: average distance between pairs of nodes before reducing
        self.neighbors = defaultdict(set)
        self.nodes = set()
        cutoff = args.cutoff
        valuesum = 0
        with open(args.infile, "r") as infile:
            for line in infile:
                name1,name2,value = line.split()
                if name1 != name2:
                    self.nodes.update([name1,name2])
                    value = float(value)
                    valuesum += value
                    if args.values_are_sim:
                        if value > cutoff:
                            self.neighbors[name1].add(name2)
                            self.neighbors[name2].add(name1)
                    else:
                        if value < cutoff:
                            self.neighbors[name1].add(name2)
                            self.neighbors[name2].add(name1)

        # Convert to regular dict to avoid gotchas having to do with key generation on access
        # Python note: would it be faster to just use dict.setdefault() during creation?
        self.neighbors = dict(self.neighbors)

        self.neighbor_count = {}
        degreelist = []
        for name in self.neighbors:
            degree = len(self.neighbors[name])
            self.neighbor_count[name] = degree
            degreelist.append(degree)
        self.origdata = {}
        self.origdata["orignum"] = len(self.nodes)
        self.origdata["average_degree"] =  sum(degreelist) / self.origdata["orignum"]
        self.origdata["max_degree"] =  max(degreelist, default=0)
        self.origdata["min_degree"] =  min(degreelist, default=0)
        n = self.origdata["orignum"]
        self.origdata["average_dist"] = valuesum * 2 / (n * (n - 1))

        self.keepset = set()
        if args.keepfile:
            with open(args.keepfile, "r") as keepfile:
                for line in keepfile:
                    node = line.strip()
                    self.keepset.add(node)

    ############################################################################################

    def most_neighbors(self):
        """Returns tuple: (node_with_most_nb, max_num_nb)"""

        node_with_most_nb, max_num_nb = max(self.neighbor_count.items(), key=itemgetter(1), default=(None,0))
        return (node_with_most_nb, max_num_nb)

    ############################################################################################

    def fewest_neighbors(self):
        """Returns tuple: (node_with_fewest_nb, min_num_nb)"""

        node_with_fewest_nb, min_num_nb = min(self.neighbor_count.items(), key=itemgetter(1), default=(None,0))
        return (node_with_fewest_nb, min_num_nb)

    ############################################################################################

    def remove_node(self, nodename):
        """Removes node from graph"""

        if nodename in self.neighbors:
            del self.neighbor_count[nodename]
            for nb in self.neighbors[nodename]:
                self.neighbor_count[nb] -= 1
                if self.neighbor_count[nb] == 0:
                    del self.neighbor_count[nb]
                    del self.neighbors[nb]
                else:
                    self.neighbors[nb].remove(nodename)
            del self.neighbors[nodename]
        self.nodes.remove(nodename)

    ############################################################################################

    def remove_connection(self, node1, node2):
        """Removes the edge from node1 to node2 in graph"""

        try:
            self.neighbors[node1].remove(node2)
            self.neighbors[node2].remove(node1)
            self.neighbor_count[node1] -= 1
            if self.neighbor_count[node1] == 0:
                del self.neighbor_count[node1]
                del self.neighbors[node1]
            self.neighbor_count[node2] -= 1
            if self.neighbor_count[node2] == 0:
                del self.neighbor_count[node2]
                del self.neighbors[node2]
        except Exception:
            raise Exception(f"These nodes are not neighbors: {node1}, {node2}. Can't remove connection")

    ############################################################################################

    def remove_neighbors(self, nodename):
        """Removes neighbors of nodename from graph, if there are any"""

        if nodename in self.neighbors:
            for nb in self.neighbors[nodename].copy():
                self.remove_node(nb)

    ############################################################################################

    def remove_keepfile_neighbors(self):
        """Remove neighbors of nodes in keepfile.
        If any nodes in keepfile are neighbors: disconnect, and print notification to stdout"""

        # First, check if any pair of keepset members are neighbors.
        # If so, print warning on stderr and hide this fact by removing connection in graph
        for n1, n2 in itertools.combinations(self.keepset, 2):
            if (n1 in self.neighbors) and (n2 in self.neighbors[n1]):
                sys.stderr.write("# Keeplist warning: {} and {} are neighbors!\n".format(n1, n2))
                self.remove_connection(n1, n2)

        # Then, remove all neighbors of keepset members
        for keepname in self.keepset:
            self.remove_neighbors(keepname)

    ############################################################################################

    def reduce_from_top(self):
        """Iteratively remove most connected node, until no neighbors left in graph"""

        node_with_most_nb, max_num_nb = self.most_neighbors()
        while max_num_nb > 0:
            self.remove_node(node_with_most_nb)
            node_with_most_nb, max_num_nb = self.most_neighbors()

    ############################################################################################

    def reduce_from_bottom(self):
        """Iteratively remove neighbors of least connected node, until no neighbors left"""

        node_with_fewest_nb, min_num_nb = self.fewest_neighbors()
        while min_num_nb > 0:
            self.remove_neighbors(node_with_fewest_nb)
            node_with_fewest_nb, min_num_nb = self.fewest_neighbors()

    ############################################################################################

    def write_results(self, args):
        """Write results to outfile, and extra info to stdout"""

        print("\n\tNames in reduced set written to {}\n".format(args.outfile))

        print("\tNumber in original set: {:>10,}".format(self.origdata["orignum"]))
        print("\tNumber in reduced set: {:>11,}\n".format(len(self.nodes)))

        print("\tNode degree original set:")
        print("\t    min: {:>7,}".format(self.origdata["min_degree"]))
        print("\t    max: {:>7,}".format(self.origdata["max_degree"]))
        print("\t    ave: {:>10,.2f}\n".format(self.origdata["average_degree"]))

        print("\tNode distances original set:")
        print("\t    ave: {:>10,.2f}".format(self.origdata["average_dist"]))
        print("\t    cutoff: {:>7,.2f}\n".format(args.cutoff))

        with open(args.outfile, "w") as outfile:
            for name in self.nodes:
                outfile.write("{}\n".format(name))

################################################################################################

if __name__ == "__main__":
    main()
