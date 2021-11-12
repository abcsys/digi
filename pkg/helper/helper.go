package helper

import (
	"fmt"
	"strings"

	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/labels"
	"k8s.io/apimachinery/pkg/types"
	"sigs.k8s.io/controller-runtime/pkg/event"
	"sigs.k8s.io/controller-runtime/pkg/handler"
	"sigs.k8s.io/controller-runtime/pkg/predicate"
	"sigs.k8s.io/controller-runtime/pkg/reconcile"
)

// Helper functions for watch message mux/demux

// MuxRequest generates transformers that add a mux tag to reconciliation requests;
// use it in a watch call, e.g.:
//
// err = c.Watch(&source.Kind{Type: &someResource}, &handler.EnqueueRequestsFromMapFunc{
//		ToRequests: muxFunc(someTag),
//	})
//
//
func MuxRequest(tag string) handler.ToRequestsFunc {
	return handler.ToRequestsFunc(func(m handler.MapObject) []reconcile.Request {
		return []reconcile.Request{
			{NamespacedName: types.NamespacedName{
				Name:      muxObjectName(tag, m.Meta.GetName()),
				Namespace: m.Meta.GetNamespace(),
			}},
		}
	})
}

func muxObjectName(tag, name string) string {
	return tag + "-" + name
}

// DemuxRequest returns the tag and original request
func DemuxRequest(r reconcile.Request) (dr reconcile.Request, tag string) {
	i := strings.Index(r.Name, "-")
	dr = reconcile.Request{
		NamespacedName: types.NamespacedName{
			Namespace: r.Namespace,
			Name:      r.Name,
		},
	}
	if i < 0 {
		tag = ""
		dr.Name = r.Name
	} else {
		tag = r.Name[:i]
		dr.Name = r.Name[i+1:]
	}
	return dr, tag
}

func NamespacedNameFromString(s string) (*types.NamespacedName, error) {
	ss := strings.Split(s, string(types.Separator))
	if len(ss) != 2 {
		return nil, fmt.Errorf("invalid namespaced name, given %s; should in form a/b", s)
	}
	return &types.NamespacedName{
		Namespace: ss[0],
		Name:      ss[1],
	}, nil
}

// XXX migrate to controller runtime 0.7
func NewPredicateFuncs(filter func(o metav1.Object) bool) predicate.Funcs {
	return predicate.Funcs{
		CreateFunc: func(e event.CreateEvent) bool {
			return filter(e.Meta)
		},
		UpdateFunc: func(e event.UpdateEvent) bool {
			return filter(e.MetaNew)
		},
		DeleteFunc: func(e event.DeleteEvent) bool {
			return filter(e.Meta)
		},
		GenericFunc: func(e event.GenericEvent) bool {
			return filter(e.Meta)
		},
	}
}

// XXX ditto
func LabelSelectorPredicate(s metav1.LabelSelector) (predicate.Predicate, error) {
	selector, err := metav1.LabelSelectorAsSelector(&s)
	if err != nil {
		return predicate.Funcs{}, err
	}

	return NewPredicateFuncs(func(o metav1.Object) bool {
		return selector.Matches(labels.Set(o.GetLabels()))
	}), nil
}
