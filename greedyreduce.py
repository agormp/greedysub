#!/usr/bin/env python3
import argparse, sys, itertools
from collections import defaultdict
from operator import itemgetter

################################################################################################

def main():
    parser = build_parser()
    args = parse_commandline(parser)
    graph = NeighborGraph(args)

    if args.keepfile:
        graph.remove_keepfile_neighbors(args.keepfile)

    if args.from_bottom:
        graph.reduce_from_bottom()
    else:
        graph.reduce_from_top()

    graph.write_results()

################################################################################################

def build_parser():
    parser = argparse.ArgumentParser(description = "Selects subset of data based on" +
                                    " list of pairwise similarities (or distances), such that no" +
                                    " retained items are close neighbors")

    parser.add_argument("infile", metavar='INFILE', default="-",
                        help="file containing the similarity (option -s) or distance " +
                             "(option -d) for each pair of items: name1 name2 value")

    parser.add_argument("outfile", metavar='OUTFILE', default="-",
                        help="write subset of names to this file (one name per line)"

    distsimgroup = parser.add_mutually_exclusive_group()
    distsimgroup.add_argument('-s', action='store_true', dest="values_are_sim",
                              help="values in INFILE are similarities " +
                                    "(larger values = more similar)")
    distsimgroup.add_argument('-d', action='store_true', dest="values_are_dist",
                              help="values in INFILE are distances " +
                                    "(smaller values = more similar)")

    algorithmgroup = parser.add_mutually_exclusive_group()
    algorithmgroup.add_argument('-b', '--frombottom', action='store_true', dest="from_bottom",
                              help="Iteratively remove neighbors of least connected node, until no neighbors left"
    algorithmgroup.add_argument('-t', '--fromtop', action='store_true', dest="from_top",
                              help="Iteratively remove most connected node, until no neighbors left"

    parser.add_argument("-c",  action="store", type=float, dest="cutoff", metavar="CUTOFF",
                          help="cutoff for deciding which pairs are neighbors")

    parser.add_argument("-k", action="store", dest="keepfile", metavar="KEEPFILE",
                          help="file with names of items that must be kept (one name per line)")
    parser.add_argument('--check', action='store_true', dest="check",
                              help="Check validity of input data: Are all pairs listed? "
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
    if ((args.from_bottom and args.from_top) or
       ((not args.from_bottom ) and (not args.from_top))):
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

        # Initialize dictionary keeping track of neighbors for each node
        # Code duplication to avoid repeated tests for args.values_are_sim
        self.neighbors = defaultdict(set)
        cutoff = args.cutoff
        with open(args.infile, "r") as infile:
            if args.values_are_sim:
                for line in infile:
                    name1,name2,value = line.split()
                    if name1 != name2:
                        value = float(value)
                        if value < cutoff:
                            self.neighbors[name1].add(name2)
                            self.neighbors[name2].add(name1)
            elif args.values_are_dist:
                for line in infile:
                    name1,name2,value = line.split()
                    if name1 != name2:
                        value = float(value)
                        if value > cutoff:
                            self.neighbors[name1].add(name2)
                            self.neighbors[name2].add(name1)

        # Initialize dictionary keeping track of how many neighbors each item has
        self.neighbor_count = {}
        degree_sum = 0
        for name in self.neighbors:
            degree = len(self.neighbors[name])
            self.neighbor_count[name] = degree
            degree_sum += degree

        # Set other graph summaries
        self.orignum = len(self.neighbors)
        self.average_degree = degree_sum / self.orignum
        _,self.max_degree = self.most_neighbors()
        _,self.min_degree = self.fewest_neighbors()

    ############################################################################################

    def most_neighbors(self):
        """Returns tuple: (node_with_most_nb, max_num_nb)"""

        node_with_most_nb, max_num_nb = max(self.neighbor_count.items(), key=itemgetter(1))
        return (node_with_most_nb, max_num_nb)

    ############################################################################################

    def fewest_neighbors(self):
        """Returns tuple: (node_with_fewest_nb, min_num_nb)"""

        node_with_fewest_nb, min_num_nb = min(self.neighbor_count.items(), key=itemgetter(1))
        return (node_with_fewest_nb, min_num_nb)

    ############################################################################################

    def remove_node(self, nodename):
        """Removes node from graph"""

        del self.neighbor_count[nodename]
        del self.neighbors[nodename]
        for nb in self.neighbors[nodename]:
            self.neighbor_count[nb] -= 1
            self.neighbors[nb].remove(nodename)

    ############################################################################################

    def remove_connection(self, node1, node2):
        """Removes the edge from node1 to node2 in graph"""

        self.neighbors[node1].remove(node2)
        self.neighbors[node2].remove(node1)
        self.neighbor_count[node1] -= 1
        self.neighbor_count[node2] -= 1

    ############################################################################################

    def remove_neighbors(self, nodename):
        """Removes neighbors of nodename from graph"""

        for nb in self.neighbors[nodename]:
            self.remove_node(nb)

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

    def remove_keepfile_neighbors(self, keepfile):
        """Remove neighbors of nodes in keepfile.
        If any nodes in keepfile are neighbors: disconnect, and print notification to stdout"""

        # Read list of names to keep
        keepset = set()
        with open(keepfile, "r") as infile:
            for line in infile:
                keepset.add(line.rstrip())

        # First, check if any pair of keepset members are neighbors.
        # If so, print warning on stderr and hide this fact by removing connection in graph
        for keepname1, keepname2 in itertools.combinations(keepset, 2):
            if keepname2 in self.neighbors[keepname1]:
                sys.stderr.write("# Keeplist warning: {} and {} are neighbors!".format(keepname1, keepname2))
                self.remove_connection(keepname1, keepname2)

        # Then, remove all neighbors of keepset members
        for keepname in keepset:
            self.remove_neighbors(keepname)

    ############################################################################################

    def write_results(self):
        """Write results to outfile, and extra info to stdout"""

        print("Names in reduced set written to {}\n".format(self.keepfile))
        print("Maximum degree: {:>4,}".format(self.max_degree))
        print("Minimum degree: {:>4,}".format(self.min_degree))
        print("Average degree: {:>4,}".format(self.average_degree))
        print("Number in original set: {:>10,}".format(self.orignum))
        print("Number in reduced set: {:>10,}".format(len(self.neighbors)))
        with open(self.outfile, "w") as outfile:
            for name in self.neighbors:
                outfile.write("{}\n".format(name))

    ############################################################################################
