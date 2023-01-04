import pytest
import greedyreduce
import itertools
import collections
import copy


###################################################################################################
###################################################################################################

class Args:
    """Used to mock args object normally returned from argparser"""
    def __init__(self, infile, values_are_sim=False, cutoff=5, keepfile=None):
        self.cutoff = cutoff
        self.infile = infile
        self.values_are_sim = values_are_sim
        self.keepfile = keepfile

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
                assert (n1 not in gr.neighbors) or (n2 not in gr.neighbors[n1])
                assert (n2 not in gr.neighbors) or (n1 not in gr.neighbors[n2])
        nbcountlist = []
        for node,count in gr.neighbor_count.items():
            c = 0
            for pair in pairs:
                if node in pair:
                    c += 1
            nbcountlist.append(c)
            assert c == count
        assert gr.origdata["orignum"] == len(nodes)
        assert gr.origdata["average_degree"]  == sum(nbcountlist) / len(nodes)
        assert gr.origdata["max_degree"] == max(nbcountlist)
        assert gr.origdata["min_degree"] == min(nbcountlist)
        # how to check gr.average_dist from given info???

    def test_example_without_neighbors(self, random_pairfile_no_neighbors_50nodes):
        distfile, nodes, pairs, cutoff = random_pairfile_no_neighbors_50nodes
        args = Args(infile=distfile, cutoff=cutoff)
        gr = greedyreduce.NeighborGraph(args)
        assert gr.nodes == set(nodes)
        for node in nodes:
            assert node not in gr.neighbors
        for count in gr.neighbor_count.values():
            assert count == 0
        assert gr.origdata["orignum"] == len(nodes)
        assert gr.origdata["average_degree"] == 0
        assert gr.origdata["max_degree"] == 0
        assert gr.origdata["min_degree"] == 0

    def test_parse_keepset(self, random_pairfile_50nodes, keepfile_n0_to_n9):
        distfile, nodes, pairs, cutoff = random_pairfile_50nodes
        keepfile, keepset = keepfile_n0_to_n9
        args = Args(infile=distfile, cutoff=cutoff, keepfile=keepfile)
        gr = greedyreduce.NeighborGraph(args)
        assert gr.keepset == {'n0', 'n1', 'n2', 'n3', 'n4', 'n5', 'n6', 'n7', 'n8', 'n9'}

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
        expected_maxnode, expected_maxnum = ncount.most_common(1)[0]
        assert max_num_nb == expected_maxnum
        assert ncount[node_with_most_nb] == max_num_nb # There could be several with same num

    def test_example_without_neighbors(self, random_pairfile_no_neighbors_50nodes):
        distfile, nodes, pairs, cutoff = random_pairfile_no_neighbors_50nodes
        args = Args(infile=distfile, cutoff=cutoff)
        gr = greedyreduce.NeighborGraph(args)
        node_with_most_nb, max_num_nb = gr.most_neighbors()
        assert node_with_most_nb is None
        assert max_num_nb == 0

###################################################################################################
###################################################################################################

class Test_fewest_neighbors:

    def test_example_with_neighbors(self, random_pairfile_50nodes):
        distfile, nodes, pairs, cutoff = random_pairfile_50nodes
        args = Args(infile=distfile, cutoff=cutoff)
        gr = greedyreduce.NeighborGraph(args)
        node_with_fewest_nb, min_num_nb = gr.fewest_neighbors()
        pairnodes = [node for tup in pairs for node in tup]
        ncount = collections.Counter(pairnodes)
        expected_minnode, expected_minnum = ncount.most_common()[-1]
        assert min_num_nb == expected_minnum
        assert ncount[node_with_fewest_nb] == min_num_nb # there could be several with same num

    def test_example_without_neighbors(self, random_pairfile_no_neighbors_50nodes):
        distfile, nodes, pairs, cutoff = random_pairfile_no_neighbors_50nodes
        args = Args(infile=distfile, cutoff=cutoff)
        gr = greedyreduce.NeighborGraph(args)
        node_with_most_nb, max_num_nb = gr.fewest_neighbors()
        assert node_with_most_nb is None
        assert max_num_nb == 0

###################################################################################################
###################################################################################################

class Test_remove_node:

    def test_example_without_neighbors(self, random_pairfile_no_neighbors_50nodes):
        distfile, nodes, pairs, cutoff = random_pairfile_no_neighbors_50nodes
        args = Args(infile=distfile, cutoff=cutoff)
        gr = greedyreduce.NeighborGraph(args)
        n1 = nodes.pop()
        gr.remove_node(n1)
        assert gr.nodes == set(nodes)
        assert n1 not in gr.neighbor_count
        assert n1 not in gr.neighbors
        for count in gr.neighbor_count.values():
            assert count == 0

    def test_example_with_neighbors(self, graph_example_01):
        distfile, nodes, pairs, cutoff = graph_example_01
        args = Args(infile=distfile, cutoff=cutoff)
        gr = greedyreduce.NeighborGraph(args)
        gr.remove_node("n2")
        nodes.remove("n2")
        assert gr.nodes == set(nodes)
        assert "n2" not in gr.neighbor_count
        assert "n2" not in gr.neighbors
        expected_counts = {"n1":2, "n3":2, "n4":2, "n6":1, "n7":1}
        assert gr.neighbor_count == expected_counts
        expected_neighbors = {"n1":{"n3","n4"}, "n3":{"n1","n6"}, "n4":{"n1","n7"}, "n6":{"n3"}, "n7":{"n4"}}
        assert gr.neighbors == expected_neighbors

        gr.remove_node("n1")
        nodes.remove("n1")
        assert gr.nodes == set(nodes)
        assert "n1" not in gr.neighbor_count
        assert "n1" not in gr.neighbors
        expected_counts = {"n3":1, "n4":1, "n6":1, "n7":1}
        assert gr.neighbor_count == expected_counts
        expected_neighbors = {"n3":{"n6"}, "n4":{"n7"}, "n6":{"n3"}, "n7":{"n4"}}
        assert gr.neighbors == expected_neighbors

###################################################################################################
###################################################################################################

class Test_remove_connection:

    def test_example_without_neighbors(self, random_pairfile_no_neighbors_50nodes):
        distfile, nodes, pairs, cutoff = random_pairfile_no_neighbors_50nodes
        args = Args(infile=distfile, cutoff=cutoff)
        gr = greedyreduce.NeighborGraph(args)
        n1,n2 = list(nodes)[:2]
        with pytest.raises(Exception, match=r"These nodes are not neighbors.*"):
            gr.remove_connection(n1,n2)

    def test_example_with_neighbors(self, random_pairfile_50nodes):
        distfile, nodes, pairs, cutoff = random_pairfile_50nodes
        args = Args(infile=distfile, cutoff=cutoff)
        gr = greedyreduce.NeighborGraph(args)
        for n1,n2 in pairs:
            n1countpre = gr.neighbor_count[n1]
            n2countpre = gr.neighbor_count[n2]
            assert n2 in gr.neighbors[n1]
            assert n1 in gr.neighbors[n2]
            gr.remove_connection(n1,n2)
            assert (n1 not in gr.neighbor_count) or (n2 not in gr.neighbors[n1])
            assert (n2 not in gr.neighbor_count) or (n1 not in gr.neighbors[n2])
            assert (n1 not in gr.neighbor_count) or (gr.neighbor_count[n1] == n1countpre - 1)
            assert (n2 not in gr.neighbor_count) or (gr.neighbor_count[n2] == n2countpre - 1)

    def test_example_known_graph(self, graph_example_01):
        distfile, nodes, pairs, cutoff = graph_example_01
        args = Args(infile=distfile, cutoff=cutoff)
        gr = greedyreduce.NeighborGraph(args)
        gr.remove_connection("n2","n5")
        gr.remove_connection("n1","n4")
        assert gr.neighbors["n1"] == {"n2","n3"}
        assert gr.neighbors["n2"] == {"n1"}
        assert gr.neighbors["n3"] == {"n1","n6"}
        assert gr.neighbors["n4"] == {"n7"}
        assert gr.neighbors["n6"] == {"n3"}
        assert gr.neighbors["n7"] == {"n4"}
        assert "n5" not in gr.neighbors
        with pytest.raises(Exception, match=r"These nodes are not neighbors: n3, n7. Can't remove connection"):
            gr.remove_connection("n3", "n7")

###################################################################################################
###################################################################################################

class Test_remove_neighbors:

    def test_example_without_neighbors(self, random_pairfile_no_neighbors_50nodes):
        distfile, nodes, pairs, cutoff = random_pairfile_no_neighbors_50nodes
        args = Args(infile=distfile, cutoff=cutoff)
        gr = greedyreduce.NeighborGraph(args)
        nbdict_pre = copy.deepcopy(gr.neighbors)
        for node in nodes:
            gr.remove_neighbors(node)
            assert gr.neighbors == nbdict_pre

    def test_example_with_neighbors(self, random_pairfile_50nodes):
        distfile, nodes, pairs, cutoff = random_pairfile_50nodes
        args = Args(infile=distfile, cutoff=cutoff)
        gr = greedyreduce.NeighborGraph(args)
        nbdict_keys = list(gr.neighbors.keys())  # These nodes have neighbors
        for node in nbdict_keys:
            gr.remove_neighbors(node)
            assert node not in gr.neighbors

    def test_example_known_graph_1(self, graph_example_01):
        distfile, nodes, pairs, cutoff = graph_example_01
        args = Args(infile=distfile, cutoff=cutoff)
        gr = greedyreduce.NeighborGraph(args)
        gr.remove_neighbors("n1")
        assert gr.nodes == {"n1", "n5", "n6", "n7"}
        assert gr.neighbors == {}
        assert gr.neighbor_count == {}

###################################################################################################
###################################################################################################

class Test_remove_keepfile_neighbors:

    def test_example_with_neighbors(self, random_pairfile_50nodes, keepfile_n0_to_n9):
        distfile, nodes, pairs, cutoff = random_pairfile_50nodes
        keepfile, keepset = keepfile_n0_to_n9
        args = Args(infile=distfile, cutoff=cutoff, keepfile=keepfile)
        gr = greedyreduce.NeighborGraph(args)
        expected_removed = set()
        for n1,n2 in pairs:
            if (n1 in keepset) and (n2 not in keepset):
                expected_removed.add(n2)
            if (n2 in keepset) and (n1 not in keepset):
                expected_removed.add(n1)
        gr.remove_keepfile_neighbors()
        for node in expected_removed:
            assert node not in gr.nodes
            assert node not in gr.neighbors
            assert node not in gr.neighbor_count

    def test_example_without_neighbors(self,
                    random_pairfile_no_neighbors_50nodes, keepfile_n0_to_n9):
        distfile, nodes, pairs, cutoff = random_pairfile_no_neighbors_50nodes
        keepfile, keepset = keepfile_n0_to_n9
        args = Args(infile=distfile, cutoff=cutoff, keepfile=keepfile)
        gr = greedyreduce.NeighborGraph(args)
        gr.remove_keepfile_neighbors()
        assert set(nodes) == gr.nodes
        for node in nodes:
            assert node not in gr.neighbors
            assert node not in gr.neighbor_count

    def test_example_known_graph_1(self, graph_example_01, keepfile_n3_and_n5):
        distfile, nodes, pairs, cutoff = graph_example_01
        keepfile, keepset = keepfile_n3_and_n5
        args = Args(infile=distfile, cutoff=cutoff, keepfile=keepfile)
        gr = greedyreduce.NeighborGraph(args)
        gr.remove_keepfile_neighbors()
        assert gr.nodes == {"n3", "n4", "n5", "n7"}
        assert gr.neighbors["n4"] == {"n7"}
        assert gr.neighbors["n7"] == {"n4"}
        assert gr.neighbor_count["n4"] == 1
        assert gr.neighbor_count["n7"] == 1

###################################################################################################
###################################################################################################

class Test_reduce_from_top:

    def test_example_known_graph_1(self, graph_example_01):
        distfile, nodes, pairs, cutoff = graph_example_01
        args = Args(infile=distfile, cutoff=cutoff)
        gr = greedyreduce.NeighborGraph(args)
        gr.reduce_from_top()
        assert len(gr.nodes) == 3
        assert ("n2" in gr.nodes) or ("n5" in gr.nodes)
        assert ("n3" in gr.nodes) or ("n6" in gr.nodes)
        assert ("n4" in gr.nodes) or ("n7" in gr.nodes)
        assert gr.neighbors == {}
        assert gr.neighbor_count == {}

    def test_example_known_graph_2(self, graph_example_02):
        distfile, nodes, pairs, cutoff = graph_example_02
        args = Args(infile=distfile, cutoff=cutoff)
        gr = greedyreduce.NeighborGraph(args)
        gr.reduce_from_top()
        assert gr.nodes == {"n2", "n3", "n4"}
        assert gr.neighbors == {}
        assert gr.neighbor_count == {}

    def test_random_graph_unknown_result(self, random_pairfile_50nodes):
        distfile, nodes, pairs, cutoff = random_pairfile_50nodes
        paired_nodes = {node for tup in pairs for node in tup}
        unpaired_nodes = nodes - paired_nodes
        args = Args(infile=distfile, cutoff=cutoff)
        gr = greedyreduce.NeighborGraph(args)
        gr.reduce_from_top()
        assert gr.neighbors == {}
        assert gr.neighbor_count == {}
        for node in unpaired_nodes:
            assert node in gr.nodes



