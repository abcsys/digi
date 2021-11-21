Syncer
==

The `sync controller` (syncer) enforces a sync binding between two attribute sets. A binding can be of `kind: Sync` or `Match`.

Each attribute set is given by a `URI`, typically in the form of `/namespace/name/[attributes]`. If the URI points to a leaf attribute, then the attribute set contains only one element (the leaf); otherwise, all the attributes in the subtree will be considered as part of the binding.

The idea of a sync binding is simple:
* Attribute sets under `Sync` binding will be eventually synced to each other, e.g., an update to one will be reflected to the other. The two attribute sets need to share identical schemas.  
* Attribute sets under `Match` binding will have the target eventually synced to the source.

A sync binding can be defined as:

```
apiVersion: ..
kind: Sync
spec:
    source: [AURI]
    target: [AURI]
    mode: [sync | match]
```

E.g.,

```
apiVersion: ..
kind: Sync
spec:
    source: /default/scene/spec/outputs/objects
    target: /default/null/spec/inputs/json
    mode: match
```

TBD: concurrent writes in a `kind: Sync` binding might with concurrent reconciliations
TBD: sync with stronger than eventual guarantee.

