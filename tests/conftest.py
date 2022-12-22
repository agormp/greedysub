import pytest
import itertools
import random

############################################################################################

def pairfile_string(nodes, pairs, cutoff):
    """Input: list of nodes, list of pair tuples, and cutoff value.
       Output: string that can be written in PAIRFILE, giving each pairwise dist"""
    pairs = set(pairs)
    stringlist = []
    for n1, n2 in itertools.combinations(nodes,2):
        if ((n1,n2) in pairs) or ((n2,n1) in pairs):
            stringlist.append("{}  {}  {}\n".format(n1,n2,cutoff/2))
        else:
            stringlist.append("{}  {}  {}\n".format(n1,n2,cutoff*2))
    return "".join(stringlist)

############################################################################################

@pytest.fixture()
def random_pairfile_50nodes(tmp_path):
    nodes = [f"n{i}" for i in range(50)]
    pairs = []
    for n1,n2 in itertools.combinations(nodes,2):
        if random.random() > 0.2:
            pairs.append((n1,n2))
    cutoff = random.random() * 100
    distfile = tmp_path / "distfile.txt"
    distfile.write_text(pairfile_string(nodes, pairs, cutoff))
    return distfile, nodes, pairs, cutoff

############################################################################################

@pytest.fixture()
def pairfile_no_neighbors(tmp_path):
    nodes = [f"n{i}" for i in range(50)]
    pairs = []
    cutoff = random.random() * 100
    distfile = tmp_path / "distfile.txt"
    distfile.write_text(pairfile_string(nodes, pairs, cutoff))
    return distfile, nodes, pairs, cutoff

############################################################################################

@pytest.fixture()
def dist_example_01(tmp_path):
    nodes = ["n1", "n2", "n3", "n4", "n5", "n6", "n7"]
    pairs = [("n1", "n2"),
             ("n1", "n3"),
             ("n1", "n4"),
             ("n2", "n5"),
             ("n3", "n6"),
             ("n4", "n7")]
    cutoff = 5
    distfile = tmp_path / "distfile.txt"
    distfile.write_text(pairfile_string(nodes, pairs, cutoff))
    return distfile, nodes, pairs, cutoff


