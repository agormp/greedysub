import pytest
import greedysub as grsub
import itertools
import collections
import copy
from pathlib import Path

###################################################################################################
###################################################################################################

class Test_parse_commandline:

    def test_min_dist_keepfile_correct(self):
        commandlist = "--algo min --val dist -c 10 -k keepfile.txt infile.txt outfile.txt".split()
        args = grsub.parse_commandline(commandlist)
        assert args.algorithm == "min"
        assert args.valuetype == "dist"
        assert args.cutoff == 10.0
        assert args.infile == Path("infile.txt")
        assert args.outfile == Path("outfile.txt")
        assert args.keepfile == Path("keepfile.txt")

    def test_max_sim_nokeepfile_correct(self):
        commandlist = "--algo max --val sim -c 10 infile.txt outfile.txt".split()
        args = grsub.parse_commandline(commandlist)
        assert args.algorithm == "max"
        assert args.valuetype == "sim"
        assert args.cutoff == 10.0
        assert args.infile == Path("infile.txt")
        assert args.outfile == Path("outfile.txt")
        assert args.keepfile == None

    def test_no_valuetype(self, capsys):
        commandlist = "--algo min -c 10 infile.txt outfile.txt".split()
        with pytest.raises(SystemExit, match="2"):
            args = grsub.parse_commandline(commandlist)
        assert "Must specify whether values in INFILE are distances" in capsys.readouterr().err

    def test_wrong_algo_choice(self, capsys):
        commandlist = "--algo notoption --val dist -c 10 infile.txt outfile.txt".split()
        with pytest.raises(SystemExit, match="2"):
            args = grsub.parse_commandline(commandlist)
        assert "invalid choice" in capsys.readouterr().err

    def test_no_cutoff(self, capsys):
        commandlist = "--algo min --val dist infile.txt outfile.txt".split()
        with pytest.raises(SystemExit, match="2"):
            args = grsub.parse_commandline(commandlist)
        assert "Must provide cutoff" in capsys.readouterr().err

###################################################################################################
###################################################################################################

class Test_init:

    @pytest.mark.parametrize("initmode", ["parallel", "serial", "lowchunksize"])
    def test_example_with_neighbors(self, random_pairfile_50nodes, initmode):
        distfile, nodes, pairs, cutoff = random_pairfile_50nodes
        if initmode=="parallel":
            commandlist = f"--val dist -c {cutoff} --par {distfile} outfile.txt".split()
        else:
            commandlist = f"--val dist -c {cutoff} {distfile} outfile.txt".split()
        args = grsub.parse_commandline(commandlist)
        if initmode=="lowchunksize":
            gr = grsub.NeighborGraph(args, chunksize=20)
        else:
            gr = grsub.NeighborGraph(args)
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

    @pytest.mark.parametrize("initmode", ["parallel", "serial", "lowchunksize"])
    def test_example_with_neighbors_sim(self, random_pairfile_50nodes_sim, initmode):
        simfile, nodes, pairs, cutoff = random_pairfile_50nodes_sim
        if initmode=="parallel":
            commandlist = f"--val sim -c {cutoff} --par {simfile} outfile.txt".split()
        else:
            commandlist = f"--val sim -c {cutoff} {simfile} outfile.txt".split()
        args = grsub.parse_commandline(commandlist)
        if initmode=="lowchunksize":
            gr = grsub.NeighborGraph(args, chunksize=20)
        else:
            gr = grsub.NeighborGraph(args)
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

    @pytest.mark.parametrize("initmode", ["parallel", "serial", "lowchunksize"])
    def test_example_without_neighbors(self, random_pairfile_no_neighbors_50nodes, initmode):
        distfile, nodes, pairs, cutoff = random_pairfile_no_neighbors_50nodes
        if initmode=="parallel":
            commandlist = f"--val dist -c {cutoff} --par {distfile} outfile.txt".split()
        else:
            commandlist = f"--val dist -c {cutoff} {distfile} outfile.txt".split()
        args = grsub.parse_commandline(commandlist)
        if initmode=="lowchunksize":
            gr = grsub.NeighborGraph(args, chunksize=20)
        else:
            gr = grsub.NeighborGraph(args)
        assert gr.nodes == set(nodes)
        for node in nodes:
            assert node not in gr.neighbors
        for count in gr.neighbor_count.values():
            assert count == 0
        assert gr.origdata["orignum"] == len(nodes)
        assert gr.origdata["average_degree"] == 0
        assert gr.origdata["max_degree"] == 0
        assert gr.origdata["min_degree"] == 0

    @pytest.mark.parametrize("initmode", ["parallel", "serial", "lowchunksize"])
    def test_parse_keepset(self, random_pairfile_50nodes, keepfile_n0_to_n9, initmode):
        distfile, nodes, pairs, cutoff = random_pairfile_50nodes
        keepfile, keepset = keepfile_n0_to_n9
        if initmode=="parallel":
            commandlist = f"--val dist -c {cutoff} -k {keepfile} --par {distfile} outfile.txt".split()
        else:
            commandlist = f"--val dist -c {cutoff} -k {keepfile} {distfile} outfile.txt".split()
        args = grsub.parse_commandline(commandlist)
        if initmode=="lowchunksize":
            gr = grsub.NeighborGraph(args, chunksize=20)
        else:
            gr = grsub.NeighborGraph(args)
        assert gr.keepset == {'n0', 'n1', 'n2', 'n3', 'n4', 'n5', 'n6', 'n7', 'n8', 'n9'}

###################################################################################################
###################################################################################################

class Test_most_neighbors:

    def test_example_with_neighbors(self, random_pairfile_50nodes):
        distfile, nodes, pairs, cutoff = random_pairfile_50nodes
        commandlist = f"--val dist -c {cutoff} {distfile} outfile.txt".split()
        args = grsub.parse_commandline(commandlist)
        gr = grsub.NeighborGraph(args)
        node_with_most_nb, max_num_nb = gr.most_neighbors()
        pairnodes = [node for tup in pairs for node in tup]
        ncount = collections.Counter(pairnodes)
        expected_maxnode, expected_maxnum = ncount.most_common(1)[0]
        assert max_num_nb == expected_maxnum
        assert ncount[node_with_most_nb] == max_num_nb # There could be several with same num

    def test_example_without_neighbors(self, random_pairfile_no_neighbors_50nodes):
        distfile, nodes, pairs, cutoff = random_pairfile_no_neighbors_50nodes
        commandlist = f"--val dist -c {cutoff} {distfile} outfile.txt".split()
        args = grsub.parse_commandline(commandlist)
        gr = grsub.NeighborGraph(args)
        node_with_most_nb, max_num_nb = gr.most_neighbors()
        assert node_with_most_nb is None
        assert max_num_nb == 0

###################################################################################################
###################################################################################################

class Test_fewest_neighbors:

    def test_example_with_neighbors(self, random_pairfile_50nodes):
        distfile, nodes, pairs, cutoff = random_pairfile_50nodes
        commandlist = f"--val dist -c {cutoff} {distfile} outfile.txt".split()
        args = grsub.parse_commandline(commandlist)
        gr = grsub.NeighborGraph(args)
        node_with_fewest_nb, min_num_nb = gr.fewest_neighbors()
        pairnodes = [node for tup in pairs for node in tup]
        ncount = collections.Counter(pairnodes)
        expected_minnode, expected_minnum = ncount.most_common()[-1]
        assert min_num_nb == expected_minnum
        assert ncount[node_with_fewest_nb] == min_num_nb # there could be several with same num

    def test_example_without_neighbors(self, random_pairfile_no_neighbors_50nodes):
        distfile, nodes, pairs, cutoff = random_pairfile_no_neighbors_50nodes
        commandlist = f"--val dist -c {cutoff} {distfile} outfile.txt".split()
        args = grsub.parse_commandline(commandlist)
        gr = grsub.NeighborGraph(args)
        node_with_most_nb, max_num_nb = gr.fewest_neighbors()
        assert node_with_most_nb is None
        assert max_num_nb == 0

###################################################################################################
###################################################################################################

class Test_remove_node:

    def test_example_without_neighbors(self, random_pairfile_no_neighbors_50nodes):
        distfile, nodes, pairs, cutoff = random_pairfile_no_neighbors_50nodes
        commandlist = f"--val dist -c {cutoff} {distfile} outfile.txt".split()
        args = grsub.parse_commandline(commandlist)
        gr = grsub.NeighborGraph(args)
        n1 = nodes.pop()
        gr.remove_node(n1)
        assert gr.nodes == set(nodes)
        assert n1 not in gr.neighbor_count
        assert n1 not in gr.neighbors
        for count in gr.neighbor_count.values():
            assert count == 0

    def test_example_with_neighbors(self, graph_example_01):
        distfile, nodes, pairs, cutoff = graph_example_01
        commandlist = f"--val dist -c {cutoff} {distfile} outfile.txt".split()
        args = grsub.parse_commandline(commandlist)
        gr = grsub.NeighborGraph(args)
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
        commandlist = f"--val dist -c {cutoff} {distfile} outfile.txt".split()
        args = grsub.parse_commandline(commandlist)
        gr = grsub.NeighborGraph(args)
        n1,n2 = list(nodes)[:2]
        with pytest.raises(Exception, match=r"These nodes are not neighbors.*"):
            gr.remove_connection(n1,n2)

    def test_example_with_neighbors(self, random_pairfile_50nodes):
        distfile, nodes, pairs, cutoff = random_pairfile_50nodes
        commandlist = f"--val dist -c {cutoff} {distfile} outfile.txt".split()
        args = grsub.parse_commandline(commandlist)
        gr = grsub.NeighborGraph(args)
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
        commandlist = f"--val dist -c {cutoff} {distfile} outfile.txt".split()
        args = grsub.parse_commandline(commandlist)
        gr = grsub.NeighborGraph(args)
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
        commandlist = f"--val dist -c {cutoff} {distfile} outfile.txt".split()
        args = grsub.parse_commandline(commandlist)
        gr = grsub.NeighborGraph(args)
        nbdict_pre = copy.deepcopy(gr.neighbors)
        for node in nodes:
            gr.remove_neighbors(node)
            assert gr.neighbors == nbdict_pre

    def test_example_with_neighbors(self, random_pairfile_50nodes):
        distfile, nodes, pairs, cutoff = random_pairfile_50nodes
        commandlist = f"--val dist -c {cutoff} {distfile} outfile.txt".split()
        args = grsub.parse_commandline(commandlist)
        gr = grsub.NeighborGraph(args)
        nbdict_keys = list(gr.neighbors.keys())  # These nodes have neighbors
        for node in nbdict_keys:
            gr.remove_neighbors(node)
            assert node not in gr.neighbors

    def test_example_known_graph_1(self, graph_example_01):
        distfile, nodes, pairs, cutoff = graph_example_01
        commandlist = f"--val dist -c {cutoff} {distfile} outfile.txt".split()
        args = grsub.parse_commandline(commandlist)
        gr = grsub.NeighborGraph(args)
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
        commandlist = f"--val dist -c {cutoff} -k {keepfile} {distfile} outfile.txt".split()
        args = grsub.parse_commandline(commandlist)
        gr = grsub.NeighborGraph(args)
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
        commandlist = f"--val dist -c {cutoff} -k {keepfile} {distfile} outfile.txt".split()
        args = grsub.parse_commandline(commandlist)
        gr = grsub.NeighborGraph(args)
        gr.remove_keepfile_neighbors()
        assert set(nodes) == gr.nodes
        for node in nodes:
            assert node not in gr.neighbors
            assert node not in gr.neighbor_count

    def test_example_known_graph_1(self, graph_example_01, keepfile_n3_and_n5):
        distfile, nodes, pairs, cutoff = graph_example_01
        keepfile, keepset = keepfile_n3_and_n5
        commandlist = f"--val dist -c {cutoff} -k {keepfile} {distfile} outfile.txt".split()
        args = grsub.parse_commandline(commandlist)
        gr = grsub.NeighborGraph(args)
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
        commandlist = f"--val dist -c {cutoff} {distfile} outfile.txt".split()
        args = grsub.parse_commandline(commandlist)
        gr = grsub.NeighborGraph(args)
        gr.reduce_from_top()
        assert len(gr.nodes) == 3
        assert ("n2" in gr.nodes) or ("n5" in gr.nodes)
        assert ("n3" in gr.nodes) or ("n6" in gr.nodes)
        assert ("n4" in gr.nodes) or ("n7" in gr.nodes)
        assert gr.neighbors == {}
        assert gr.neighbor_count == {}

    def test_example_known_graph_2(self, graph_example_02):
        distfile, nodes, pairs, cutoff = graph_example_02
        commandlist = f"--val dist -c {cutoff} {distfile} outfile.txt".split()
        args = grsub.parse_commandline(commandlist)
        gr = grsub.NeighborGraph(args)
        gr.reduce_from_top()
        assert gr.nodes == {"n2", "n3", "n4"}
        assert gr.neighbors == {}
        assert gr.neighbor_count == {}

    def test_example_known_graph_3(self, graph_example_03):
        distfile, nodes, pairs, cutoff = graph_example_03
        commandlist = f"--val dist -c {cutoff} {distfile} outfile.txt".split()
        args = grsub.parse_commandline(commandlist)
        gr = grsub.NeighborGraph(args)
        gr.reduce_from_top()
        assert len(gr.nodes) == 4
        n1 = "n1" in gr.nodes; n2 = "n2" in gr.nodes; n3 = "n3" in gr.nodes; n4 = "n4" in gr.nodes
        n5 = "n5" in gr.nodes; n6 = "n6" in gr.nodes; n7 = "n7" in gr.nodes; n8 = "n8" in gr.nodes;
        n9 = "n9" in gr.nodes; n10 = "n10" in gr.nodes
        assert not n1
        assert n10
        assert sum([n2, n3, n6]) == 1  # Only one of them present
        assert (
                (n7 and (n4 or n9))
             or (n9 and (n7 or n8))
             or ((n4 or n9) and (n5 or n7))
        )
        assert gr.neighbors == {}
        assert gr.neighbor_count == {}

    def test_random_graph_unknown_result(self, random_pairfile_50nodes):
        distfile, nodes, pairs, cutoff = random_pairfile_50nodes
        paired_nodes = {node for tup in pairs for node in tup}
        unpaired_nodes = nodes - paired_nodes
        commandlist = f"--val dist -c {cutoff} {distfile} outfile.txt".split()
        args = grsub.parse_commandline(commandlist)
        gr = grsub.NeighborGraph(args)
        gr.reduce_from_top()
        assert gr.neighbors == {}
        assert gr.neighbor_count == {}
        for node in unpaired_nodes:
            assert node in gr.nodes

    def test_example_without_neighbors(self, random_pairfile_no_neighbors_50nodes):
        distfile, nodes, pairs, cutoff = random_pairfile_no_neighbors_50nodes
        commandlist = f"--val dist -c {cutoff} {distfile} outfile.txt".split()
        args = grsub.parse_commandline(commandlist)
        gr = grsub.NeighborGraph(args)
        gr.reduce_from_top()
        assert len(gr.nodes) == 50
        assert gr.neighbors == {}
        assert gr.neighbor_count == {}

###################################################################################################
###################################################################################################

class Test_reduce_from_bottom:

    def test_example_known_graph_1(self, graph_example_01):
        distfile, nodes, pairs, cutoff = graph_example_01
        commandlist = f"--val dist -c {cutoff} {distfile} outfile.txt".split()
        args = grsub.parse_commandline(commandlist)
        gr = grsub.NeighborGraph(args)
        gr.reduce_from_bottom()
        assert gr.nodes == {"n1", "n5", "n6", "n7"}
        assert gr.neighbors == {}
        assert gr.neighbor_count == {}

    def test_example_known_graph_2(self, graph_example_02):
        distfile, nodes, pairs, cutoff = graph_example_02
        commandlist = f"--val dist -c {cutoff} {distfile} outfile.txt".split()
        args = grsub.parse_commandline(commandlist)
        gr = grsub.NeighborGraph(args)
        gr.reduce_from_bottom()
        n1 = "n1" in gr.nodes; n2 = "n2" in gr.nodes; n3 = "n3" in gr.nodes; n4 = "n4" in gr.nodes
        n5 = "n5" in gr.nodes; n6 = "n6" in gr.nodes; n7 = "n7" in gr.nodes;
        assert n1
        assert sum([n5, n6, n7]) == 1  # Only one of them present
        assert not any([n2, n3, n4])
        assert gr.neighbors == {}
        assert gr.neighbor_count == {}

    def test_example_known_graph_3(self, graph_example_03):
        distfile, nodes, pairs, cutoff = graph_example_03
        commandlist = f"--val dist -c {cutoff} {distfile} outfile.txt".split()
        args = grsub.parse_commandline(commandlist)
        gr = grsub.NeighborGraph(args)
        gr.reduce_from_bottom()
        assert len(gr.nodes) == 4
        n1 = "n1" in gr.nodes; n2 = "n2" in gr.nodes; n3 = "n3" in gr.nodes; n4 = "n4" in gr.nodes
        n5 = "n5" in gr.nodes; n6 = "n6" in gr.nodes; n7 = "n7" in gr.nodes; n8 = "n8" in gr.nodes;
        n9 = "n9" in gr.nodes; n10 = "n10" in gr.nodes
        assert n9
        assert n10
        assert not n1
        assert not n4
        assert sum([n2, n3, n6]) == 1  # Only one of them present
        assert sum([n5, n7, n8]) == 1  # Only one of them present
        assert gr.neighbors == {}
        assert gr.neighbor_count == {}

    def test_random_graph_unknown_result(self, random_pairfile_50nodes):
        distfile, nodes, pairs, cutoff = random_pairfile_50nodes
        paired_nodes = {node for tup in pairs for node in tup}
        unpaired_nodes = nodes - paired_nodes
        commandlist = f"--val dist -c {cutoff} {distfile} outfile.txt".split()
        args = grsub.parse_commandline(commandlist)
        gr = grsub.NeighborGraph(args)
        gr.reduce_from_bottom()
        assert gr.neighbors == {}
        assert gr.neighbor_count == {}
        for node in unpaired_nodes:
            assert node in gr.nodes

    def test_example_without_neighbors(self, random_pairfile_no_neighbors_50nodes):
        distfile, nodes, pairs, cutoff = random_pairfile_no_neighbors_50nodes
        commandlist = f"--val dist -c {cutoff} {distfile} outfile.txt".split()
        args = grsub.parse_commandline(commandlist)
        gr = grsub.NeighborGraph(args)
        gr.reduce_from_bottom()
        assert len(gr.nodes) == 50
        assert gr.neighbors == {}
        assert gr.neighbor_count == {}

###################################################################################################
###################################################################################################

class Test_write_results:

    def test_outfile_frombottom(self, tmp_path, random_pairfile_50nodes):
        resultfile = tmp_path / "outfile.txt"
        distfile, nodes, pairs, cutoff = random_pairfile_50nodes
        commandlist = f"--val dist -c {cutoff} {distfile} {resultfile}".split()
        args = grsub.parse_commandline(commandlist)
        gr = grsub.NeighborGraph(args)
        gr.reduce_from_bottom()
        gr.write_results(args)
        outfileset = set()
        with args.outfile.open() as f:
            for line in f:
                name = line.rstrip()
                outfileset.add(name)
        assert gr.nodes == outfileset

    def test_outfile_fromtop(self, tmp_path, random_pairfile_50nodes):
        resultfile = tmp_path / "outfile.txt"
        distfile, nodes, pairs, cutoff = random_pairfile_50nodes
        commandlist = f"--val dist -c {cutoff} {distfile} {resultfile}".split()
        args = grsub.parse_commandline(commandlist)
        gr = grsub.NeighborGraph(args)
        gr.reduce_from_top()
        gr.write_results(args)
        outfileset = set()
        with args.outfile.open() as f:
            for line in f:
                name = line.rstrip()
                outfileset.add(name)
        assert gr.nodes == outfileset

    def test_stdout_frombottom(self, tmp_path, capsys, random_pairfile_50nodes):
        resultfile = tmp_path / "outfile.txt"
        distfile, nodes, pairs, cutoff = random_pairfile_50nodes
        commandlist = f"--val dist -c {cutoff} {distfile} {resultfile}".split()
        args = grsub.parse_commandline(commandlist)
        gr = grsub.NeighborGraph(args)
        gr.reduce_from_bottom()
        gr.write_results(args)
        outlines = capsys.readouterr().out.split("\n")

        out_orignum = int(outlines[3].split()[-1])
        out_reducednum = int(outlines[4].split()[-1])
        out_mindeg = int(outlines[7].split()[-1])
        out_maxdeg = int(outlines[8].split()[-1])
        out_avedeg = float(outlines[9].split()[-1])
        out_avedist = float(outlines[12].split()[-1])
        out_cutoff = float(outlines[13].split()[-1])

        assert out_orignum == 50
        assert out_reducednum == len(gr.nodes)
        assert out_mindeg == gr.origdata["min_degree"]
        assert out_maxdeg == gr.origdata["max_degree"]
        assert out_avedeg == pytest.approx(gr.origdata["average_degree"], abs=0.01)
        assert out_avedist == pytest.approx(gr.origdata["average_dist"], abs=0.01)
        assert out_cutoff == pytest.approx(cutoff, abs=0.01)

    def test_stdout_fromtop(self, tmp_path, capsys, random_pairfile_50nodes):
        resultfile = tmp_path / "outfile.txt"
        distfile, nodes, pairs, cutoff = random_pairfile_50nodes
        commandlist = f"--val dist -c {cutoff} {distfile} {resultfile}".split()
        args = grsub.parse_commandline(commandlist)
        gr = grsub.NeighborGraph(args)
        gr.reduce_from_top()
        gr.write_results(args)
        outlines = capsys.readouterr().out.split("\n")

        out_orignum = int(outlines[3].split()[-1])
        out_reducednum = int(outlines[4].split()[-1])
        out_mindeg = int(outlines[7].split()[-1])
        out_maxdeg = int(outlines[8].split()[-1])
        out_avedeg = float(outlines[9].split()[-1])
        out_avedist = float(outlines[12].split()[-1])
        out_cutoff = float(outlines[13].split()[-1])

        assert out_orignum == 50
        assert out_reducednum == len(gr.nodes)
        assert out_mindeg == gr.origdata["min_degree"]
        assert out_maxdeg == gr.origdata["max_degree"]
        assert out_avedeg == pytest.approx(gr.origdata["average_degree"], abs=0.01)
        assert out_avedist == pytest.approx(gr.origdata["average_dist"], abs=0.01)
        assert out_cutoff == pytest.approx(cutoff, abs=0.01)

###################################################################################################
###################################################################################################

class Test_main:

    # Essentially an integration test

    def test_example_known_graph_2_max(self, tmp_path, graph_example_02, capsys):
        resultfile = tmp_path / "outfile.txt"
        distfile, nodes, pairs, cutoff = graph_example_02
        commandlist = f"--algo max --val dist -c {cutoff} {distfile} {resultfile}".split()
        grsub.main(commandlist)
        outfileset = set()
        with resultfile.open() as f:
            for line in f:
                name = line.rstrip()
                outfileset.add(name)
        assert outfileset == {"n2", "n3", "n4"}

        outlines = capsys.readouterr().out.split("\n")

        out_orignum = int(outlines[3].split()[-1])
        out_reducednum = int(outlines[4].split()[-1])
        out_mindeg = int(outlines[7].split()[-1])
        out_maxdeg = int(outlines[8].split()[-1])
        out_avedeg = float(outlines[9].split()[-1])
        out_avedist = float(outlines[12].split()[-1])
        out_cutoff = float(outlines[13].split()[-1])

        assert out_orignum == 7
        assert out_reducednum == 3
        assert out_mindeg == 3
        assert out_maxdeg == 5
        assert out_avedeg == pytest.approx(30/7, abs=0.01)
        exp_avedist = (15 * 2.5 + 6 * 10) / 21
        assert out_avedist == pytest.approx(exp_avedist, abs=0.01)
        assert out_cutoff == 5

    def test_example_known_graph_2_min(self, tmp_path, graph_example_02, capsys):
        resultfile = tmp_path / "outfile.txt"
        distfile, nodes, pairs, cutoff = graph_example_02
        commandlist = f"--algo min --val dist -c {cutoff} {distfile} {resultfile}".split()
        grsub.main(commandlist)
        outfileset = set()
        with resultfile.open() as f:
            for line in f:
                name = line.rstrip()
                outfileset.add(name)
        n1 = "n1" in outfileset; n2 = "n2" in outfileset; n3 = "n3" in outfileset; n4 = "n4" in outfileset
        n5 = "n5" in outfileset; n6 = "n6" in outfileset; n7 = "n7" in outfileset;
        assert n1
        assert sum([n5, n6, n7]) == 1  # Only one of them present
        assert not any([n2, n3, n4])

        outlines = capsys.readouterr().out.split("\n")

        out_orignum = int(outlines[3].split()[-1])
        out_reducednum = int(outlines[4].split()[-1])
        out_mindeg = int(outlines[7].split()[-1])
        out_maxdeg = int(outlines[8].split()[-1])
        out_avedeg = float(outlines[9].split()[-1])
        out_avedist = float(outlines[12].split()[-1])
        out_cutoff = float(outlines[13].split()[-1])

        assert out_orignum == 7
        assert out_reducednum == 2
        assert out_mindeg == 3
        assert out_maxdeg == 5
        assert out_avedeg == pytest.approx(30/7, abs=0.01)
        exp_avedist = (15 * 2.5 + 6 * 10) / 21
        assert out_avedist == pytest.approx(exp_avedist, abs=0.01)
        assert out_cutoff == 5


    def test_example_known_graph_1_keepfile(self, graph_example_01, keepfile_n3_and_n5, tmp_path, capsys):
        resultfile = tmp_path / "outfile.txt"
        distfile, nodes, pairs, cutoff = graph_example_01
        keepfile, keepset = keepfile_n3_and_n5
        commandlist = f"--algo min --val dist -c {cutoff} -k {keepfile} {distfile} {resultfile}".split()
        grsub.main(commandlist)

        outfileset = set()
        with resultfile.open() as f:
            for line in f:
                name = line.rstrip()
                outfileset.add(name)

        assert "n3" in outfileset
        assert "n5" in outfileset
        assert sum(["n4" in outfileset, "n7" in outfileset]) == 1

        outlines = capsys.readouterr().out.split("\n")

        out_orignum = int(outlines[3].split()[-1])
        out_reducednum = int(outlines[4].split()[-1])
        out_mindeg = int(outlines[7].split()[-1])
        out_maxdeg = int(outlines[8].split()[-1])
        out_avedeg = float(outlines[9].split()[-1])
        out_avedist = float(outlines[12].split()[-1])
        out_cutoff = float(outlines[13].split()[-1])

        assert out_orignum == 7
        assert out_reducednum == 3
        assert out_mindeg == 1
        assert out_maxdeg == 3
        assert out_avedeg == pytest.approx(12/7, abs=0.01)
        exp_avedist = (6 * 2.5 + 15 * 10) / 21
        assert out_avedist == pytest.approx(exp_avedist, abs=0.01)
        assert out_cutoff == 5



