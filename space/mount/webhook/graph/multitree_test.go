package graph

import "testing"

func TestMultiTree(t *testing.T) {
	mt := &MultiTree{
		nodes: make(map[string]*node),
		trees: make(map[string]*tree),
	}
	nodes := []string{
		"A", "B", "U", "X", "V", "W", "Y", "Z",
	}
	edges := []Edge {
		{
			Start: "A",
			End:   "U",
		},
		{
			Start: "A",
			End:   "X",
		},
		{
			Start: "U",
			End:   "V",
		},
		{
			Start: "U",
			End:   "W",
		},
		{
			Start: "X",
			End:   "Y",
		},
		{
			Start: "X",
			End:   "Z",
		},
	}

	for _, n := range nodes {
		mt.AddNode(n)
	}

	for _, e := range edges {
		if err := mt.AddEdge(e.Start, e.End); err != nil {
			t.Errorf("error adding edge %v:%v", e, err)
		}
	}

	t.Logf("current multi-tree:\n%s", mt.String())

	// make it a multi-tree
	edges = []Edge{
		{
			Start: "B",
			End:   "V",
		},
		{
			Start: "B",
			End:   "X",
		},
	}
	for _, e := range edges {
		if err := mt.AddEdge(e.Start, e.End); err != nil {
			t.Errorf("error adding edge %v:%v", e, err)
		}
	}
	t.Logf("current multi-tree:\n%s", mt.String())

	// disallowed
	t.Logf("adding edge B-Z (should fail)..")
	err := mt.AddEdge("B", "Z")
	if err == nil {
		t.Errorf("call to AddEdge should fail")
	}
	t.Logf("call to AddEdge failed: %v", err)

	// disallowed
	t.Logf("adding edge B-U (should fail)..")
	err = mt.AddEdge("B", "U")
	if err == nil {
		t.Errorf("call to AddEdge should fail")
	}
	t.Logf("call to AddEdge failed: %v", err)

	// allowed
	t.Logf("adding edge B-W..")
	err = mt.AddEdge("B", "W")
	if err != nil {
		t.Errorf("error adding edge %v:%v", "B-W", err)
	}
	t.Logf("current multi-tree:\n%s", mt.String())

	// edge removal
	t.Logf("removing edge B-X..")
	err = mt.RemoveEdge("B", "X")
	if err != nil {
		t.Errorf("error removing edge %v:%v", "B-X", err)
	}
	t.Logf("current multi-tree:\n%s", mt.String())

	// node removal
	t.Logf("removing node A..")
	err = mt.RemoveNode("A")
	if err != nil {
		t.Errorf("error removing node %v:%v", "A", err)
	}
	t.Logf("current multi-tree:\n%s", mt.String())
}
