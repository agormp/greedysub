import pytest
import greedyreduce
import itertools
import collections


###################################################################################################
###################################################################################################

class Args:
    def __init__(self, infile, values_are_sim=False, cutoff=5):
        self.cutoff = cutoff
        self.infile = infile
        self.values_are_sim = values_are_sim

###################################################################################################
###################################################################################################

class Test_init:

    def test_example_with_neighbors(self, random_pairfile_50nodes):
        distfile, nodes, pairs, cutoff = random_pairfile_50nodes
        args = Args(infile=distfile, cutoff=cutoff)
        gr = greedyreduce.NeighborGraph(args)
        assert gr.nodes == set(nodes)
        for n1,n2 in itertools.combinations(nodes, 2):
            if ((n1,n2) in pairs) or ((n2,n1) in pairs):
                assert n2 in gr.neighbors[n1]
                assert n1 in gr.neighbors[n2]
            else:
                assert n2 not in gr.neighbors[n1]
                assert n1 not in gr.neighbors[n2]
        nbcountlist = []
        for node,count in gr.neighbor_count.items():
            c = 0
            for pair in pairs:
                if node in pair:
                    c += 1
            nbcountlist.append(c)
            assert c == count
        assert gr.orignum == len(nodes)
        assert gr.average_degree == sum(nbcountlist) / len(nodes)
        assert gr.max_degree == max(nbcountlist)
        assert gr.min_degree == min(nbcountlist)
        # how to check gr.average_dist from given info???

    def test_example_without_neighbors(self, pairfile_no_neighbors):
        distfile, nodes, pairs, cutoff = pairfile_no_neighbors
        args = Args(infile=distfile, cutoff=cutoff)
        gr = greedyreduce.NeighborGraph(args)
        assert gr.nodes == set(nodes)
        for n1,n2 in itertools.combinations(nodes, 2):
            assert n2 not in gr.neighbors[n1]
            assert n1 not in gr.neighbors[n2]
        for count in gr.neighbor_count.values():
            assert count == 0
        assert gr.orignum == len(nodes)
        assert gr.average_degree == 0
        assert gr.max_degree == 0
        assert gr.min_degree == 0

###################################################################################################
###################################################################################################

class Test_most_neighbors:

    def test_example_with_neighbors(self, random_pairfile_50nodes):
        distfile, nodes, pairs, cutoff = random_pairfile_50nodes
        args = Args(infile=distfile, cutoff=cutoff)
        gr = greedyreduce.NeighborGraph(args)
        node_with_most_nb, max_num_nb = gr.most_neighbors()
        pairnodes = [node for tup in pairs for node in tup]
        ncount = collections.Counter(pairnodes)
        expected_maxnode, expected_maxun = ncount.most_common(1)[0]
        assert (node_with_most_nb, max_num_nb) == (expected_maxnode, expected_maxun)

    def test_example_without_neighbors(self, pairfile_no_neighbors):
        distfile, nodes, pairs, cutoff = pairfile_no_neighbors
        args = Args(infile=distfile, cutoff=cutoff)
        gr = greedyreduce.NeighborGraph(args)
