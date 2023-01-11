#!/usr/bin/env python3

import argparse, sys, itertools
import pandas as pd
from collections import defaultdict
from operator import itemgetter
from pathlib import Path

################################################################################################

# Python note: "commandlist" is to enable unit testing of argparse code
# https://jugmac00.github.io/blog/testing-argparse-applications-the-better-way/

def main(commandlist=None):
    args = parse_commandline(commandlist)
    graph = NeighborGraph(args)

    # If input has no neighbors: do nothing, print results. Otherwise: proceed
    if graph.origdata["max_degree"] > 0:
        if args.keepfile:
            graph.remove_keepfile_neighbors()

        if args.algorithm == "min":
            graph.reduce_from_bottom()
        else:
            graph.reduce_from_top()

    graph.write_results(args)

################################################################################################

# Python note: "commandlist" is to enable unit testing of argparse code
# Will be "None" when run in script mode, and argparse will then automatically take values from sys.argv[1:]


def parse_commandline(commandlist):
    parser = build_parser()
    args = parser.parse_args(commandlist)
    if args.valuetype is None:
        parser.error("Must specify whether values in INFILE are distances (--val dist) or similarities (--val sim)")
    if args.cutoff is None:
        parser.error("Must provide cutoff (option -c)")
    return args

################################################################################################


def build_parser():

    parser = argparse.ArgumentParser(description = "Selects subset of items, based on" +
                                    " list of pairwise similarities (or distances), such that no" +
                                    " retained items are close neighbors")

    parser.add_argument("infile", metavar='INFILE', type=Path,
                        help="input file containing similarity or distance " +
                             "for each pair of items: name1 name2 value")

    parser.add_argument("outfile", metavar='OUTFILE', type=Path,
                        help="output file contatining neighborless subset of items (one name per line)")

    #########################################################################################

    parser.add_argument("--algo", action='store', dest="algorithm", metavar="ALGORITHM",
                      choices=["min", "max"], default="min",
                      help="algorithm: %(choices)s [default: %(default)s]")

    parser.add_argument("--val", action='store', dest="valuetype", metavar="VALUETYPE",
                      choices=["dist", "sim"],
                      help="specify whether values in INFILE are distances (--val dist) or similarities (--val sim)")

    parser.add_argument("-c",  action="store", type=float, dest="cutoff", metavar="CUTOFF",
                          help="cutoff value for deciding which pairs are neighbors")

    parser.add_argument("-k", action="store", dest="keepfile", metavar="KEEPFILE", type=Path,
                          help="(optional) file with names of items that must be kept (one name per line)")

    return parser

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
        nreadlines = 1000000
        nodes = set()
        neighbors = defaultdict(set)
        valuesum = 0
        reader = pd.read_csv(args.infile, engine="c", delim_whitespace=True, chunksize=nreadlines,
                             names=["name1", "name2", "val"], dtype={"name1":str, "name2":str, "val":float})

        for df in reader:
            nodes.update(df["name1"].values)
            nodes.update(df["name2"].values)
            valuesum += df["val"].values.sum()

            if args.valuetype == "sim":
                df = df.loc[df["val"].values > args.cutoff]
            else:
                df = df.loc[df["val"].values < args.cutoff]
            df = df.loc[df["name1"].values != df["name2"].values]
            for name1, name2 in zip(df["name1"].values, df["name2"].values):
                neighbors[name1].add(name2)
                neighbors[name2].add(name1)

        # Convert to regular dict (not defaultdict) to avoid gotchas with key generation on access
        # Python note: would it be faster to just use dict.setdefault() during creation?
        self.neighbors = dict(neighbors)
        self.nodes = nodes
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
        #self.df = df

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

    #@profile
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

    #@profile
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

        print(f"\n\tNames in reduced set written to {args.outfile}\n")

        print(f"\tNumber in original set: {self.origdata['orignum']:>10,}")
        print(f"\tNumber in reduced set: {len(self.nodes):>11,}\n")

        print("\tNode degree original set:")
        print(f"\t    min: {self.origdata['min_degree']:>7,}")
        print(f"\t    max: {self.origdata['max_degree']:>7,}")
        print(f"\t    ave: {self.origdata['average_degree']:>10,.2f}\n")

        if args.valuetype == "sim":
            print("\tNode similarities original set:")
        else:
            print("\tNode distances original set:")
        print(f"\t    ave: {self.origdata['average_dist']:>10,.2f}")
        print(f"\t    cutoff: {args.cutoff:>7,.2f}\n")

        with open(args.outfile, "w") as outfile:
            for name in self.nodes:
                outfile.write("{}\n".format(name))

################################################################################################

if __name__ == "__main__":
    main()
