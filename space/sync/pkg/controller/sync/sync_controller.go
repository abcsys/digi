package sync

import (
	"context"
	"fmt"
	"log"
	"sync"

	"k8s.io/apimachinery/pkg/api/errors"
	"k8s.io/apimachinery/pkg/apis/meta/v1/unstructured"
	"k8s.io/apimachinery/pkg/runtime"
	"sigs.k8s.io/controller-runtime/pkg/client"
	"sigs.k8s.io/controller-runtime/pkg/controller"
	"sigs.k8s.io/controller-runtime/pkg/handler"
	"sigs.k8s.io/controller-runtime/pkg/manager"
	//"sigs.k8s.io/controller-runtime/pkg/predicate"
	"sigs.k8s.io/controller-runtime/pkg/reconcile"
	"sigs.k8s.io/controller-runtime/pkg/source"

	"digi.dev/digi/pkg/core"
	"digi.dev/digi/pkg/helper"
	digiv1 "digi.dev/digi/space/sync/pkg/apis/digi/v1"
)

const (
	name = "sync_controller"
	// request tag for sync model
	syncTag = "sync"
	// request tag for models under sync binding
	enforceTag = "enforce"
)

var (
	this controller.Controller
	//labelSelector = metav1.LabelSelector{
	//	MatchLabels: map[string]string{
	//		"runtime.digi.dev": "sync",
	//	},
	//}
)

type Binding struct {
	name string
	digiv1.SyncSpec
}

type Bindings map[string]*Binding

type BindingCache struct {
	// bindings by the name
	bindings Bindings

	// reverse lookup for binding name given model name
	modelToBindings map[string]Bindings

	// kinds that have been watched
	watched map[string]struct{}

	// apiserver client
	client client.Client

	mu sync.RWMutex
}

func (bc *BindingCache) Add(b *Binding) error {
	bc.mu.Lock()
	defer bc.mu.Unlock()

	// validate sync mode
	// TBD move to sync's admission webhook
	if b.Mode != digiv1.MatchMode && b.Mode != digiv1.SyncMode {
		return fmt.Errorf("unknown sync mode %s", b.Mode)
	}

	bc.bindings[b.name] = b

	var srcKind, targetKind string

	// adding new watches to the resource kind if it has not
	// been watched before
	// XXX add label selector predicate
	addWatchFunc := func(auri *core.Auri) error {
		o, err := helper.GetObj(bc.client, auri)
		if err != nil {
			return err
		}

		// validate path
		if _, err := helper.GetAttr(o, auri.Path); err != nil {
			log.Println("warning:", err)
			// XXX
			//return err
		}

		return this.Watch(&source.Kind{
			Type: o,
		}, &handler.EnqueueRequestsFromMapFunc{
			ToRequests: helper.MuxRequest(enforceTag),
		})
	}

	srcKind = b.Source.Kind.String()
	if _, ok := bc.watched[srcKind]; !ok {
		if err := addWatchFunc(&b.Source); err != nil {
			log.Println(err)
			return err
		}
		bc.watched[srcKind] = struct{}{}
	}

	targetKind = b.Target.Kind.String()
	if _, ok := bc.watched[targetKind]; !ok {
		if err := addWatchFunc(&b.Target); err != nil {
			log.Println(err)
			return err
		}
		bc.watched[targetKind] = struct{}{}
	}

	srcName, targetName := b.Source.SpacedName().String(), b.Target.SpacedName().String()

	setFunc := func(m map[string]Bindings, k1, k2 string, v *Binding) {
		_, ok := m[k1]
		if !ok {
			m[k1] = make(Bindings)
		}
		m[k1][k2] = v
	}

	m := bc.modelToBindings
	setFunc(m, srcName, b.name, b)
	setFunc(m, targetName, b.name, b)
	return nil
}

func (bc *BindingCache) Remove(name string) {
	bc.mu.Lock()
	defer bc.mu.Unlock()

	bd, ok := bc.bindings[name]
	if !ok {
		return
	}

	delete(bc.bindings, name)

	var srcName, targetName string
	srcName = bd.Source.SpacedName().String()
	targetName = bd.Target.SpacedName().String()

	srcBds, ok := bc.modelToBindings[srcName]
	if ok {
		delete(srcBds, name)
	}

	targetBds, ok := bc.modelToBindings[targetName]
	if ok {
		delete(targetBds, name)
	}
}

func (bc *BindingCache) Exist(b *Binding) bool {
	_, ok := bc.bindings[b.name]
	return ok
}

// ReconcileSync reconciles a Sync object
// The agent watches the primary resource Sync and adds additional watches
// for the binding sources and targets.
type ReconcileSync struct {
	// This client, initialized using mgr.Client() above, is a split client
	// that reads objects from the cache and writes to the apiserver
	client client.Client
	scheme *runtime.Scheme

	bindingCache *BindingCache
}

// Add creates a new Sync Controller and adds it to the Manager. The Manager will set fields on the Controller
// and Start it when the Manager is Started.
func Add(mgr manager.Manager) error {
	// Create a new reconciler
	r := newReconciler(mgr)

	// Create a new controller
	c, err := controller.New(name, mgr, controller.Options{Reconciler: r})
	if err != nil {
		return err
	}

	this = c

	// Watch for changes to primary resource Sync
	if err = c.Watch(&source.Kind{
		Type: &digiv1.Sync{},
	}, &handler.EnqueueRequestsFromMapFunc{
		ToRequests: helper.MuxRequest(syncTag),
	}); err != nil {
		return err
	}

	return nil
}

// newReconciler returns a new reconcile.Reconciler
func newReconciler(mgr manager.Manager) reconcile.Reconciler {
	c := mgr.GetClient()
	return &ReconcileSync{
		client: c,
		scheme: mgr.GetScheme(),
		bindingCache: &BindingCache{
			bindings:        make(map[string]*Binding),
			modelToBindings: make(map[string]Bindings),
			watched:         make(map[string]struct{}),
			client:          c,
		},
	}
}

func (r *ReconcileSync) Reconcile(request reconcile.Request) (reconcile.Result, error) {
	log.Println("Reconciling Sync")

	request, tag := helper.DemuxRequest(request)

	switch tag {
	case syncTag:
		return r.doSync(request)
	case enforceTag:
		return r.doEnforce(request)
	}

	return reconcile.Result{}, nil
}

func (r *ReconcileSync) doSync(request reconcile.Request) (reconcile.Result, error) {
	log.Println("do sync")

	var name string
	name = request.String()

	// fetch the Sync instance
	sc := &digiv1.Sync{}
	err := r.client.Get(context.TODO(), request.NamespacedName, sc)
	if err != nil {
		if errors.IsNotFound(err) {

			r.finalize(name)

			// prune cached binding
			r.bindingCache.Remove(name)

			log.Println(err)
			return reconcile.Result{}, nil
		}
		return reconcile.Result{}, err
	}

	log.Printf("handle sync binding %s: %v", name, sc.Spec)

	// XXX write any sync failure to the event/reasons or observations
	if err := r.bindingCache.Add(&Binding{
		name:     name,
		SyncSpec: sc.Spec,
	}); err != nil {
		return reconcile.Result{}, err
	}

	return r.doEnforce(reconcile.Request{
		NamespacedName: sc.Spec.Source.SpacedName(),
	})
}

func (r *ReconcileSync) doEnforce(request reconcile.Request) (reconcile.Result, error) {
	var bds Bindings
	bds, ok := r.bindingCache.modelToBindings[request.String()]
	if !ok {
		// skip
		return reconcile.Result{}, nil
	}

	log.Println("do Enforce")

	var err error
	for _, bd := range bds {
		log.Println("enforcing binding:", bd)
		var bdSrc, bdTarget *unstructured.Unstructured

		bdSrc, err = helper.GetObj(r.client, &bd.Source)
		if err != nil {
			// XXX log to sync reasons
			log.Println("unable to get source model:", bd.Source)
			continue
		}

		bdTarget, err = helper.GetObj(r.client, &bd.Target)
		if err != nil {
			log.Println("unable to get target model:", bd.Target)
			continue
		}

		var reqName, srcName, targetName string
		reqName = request.String()
		srcName = bd.Source.SpacedName().String()
		targetName = bd.Target.SpacedName().String()

		// enforce binding
		switch bd.Mode {
		case digiv1.SyncMode:
			switch reqName {
			case srcName:
				err = r.matchAttr(bdSrc, bd.Source.Path, bdTarget, bd.Target.Path)
			case targetName:
				err = r.matchAttr(bdTarget, bd.Target.Path, bdSrc, bd.Source.Path)
			default:
				log.Println("unmatched request:", reqName)
				continue
			}
		case digiv1.MatchMode:
			err = r.matchAttr(bdSrc, bd.Source.Path, bdTarget, bd.Target.Path)
		default:
			continue
		}

		if err != nil {
			log.Println("enforce error:", err)
			continue
		}
	}

	return reconcile.Result{}, err
}

func (r *ReconcileSync) matchAttr(src *unstructured.Unstructured, srcPath string, target *unstructured.Unstructured, targetPath string) error {
	srcAttr, err := helper.GetAttr(src, srcPath)
	//log.Println("DEBUG:", "src:", src, "srcPath:", srcPath, "srcAttr:", srcAttr)
	if err != nil {
		log.Println("unable to get source attr from:", src, "path:", srcPath)
		return err
	}

	err = unstructured.SetNestedField(target.Object, srcAttr, core.AttrPathSlice(targetPath)...)
	//log.Println("DEBUG:", "targetPath:", targetPath, "target:", target.Object)
	if err != nil {
		log.Println("unable to set target attribute")
		return err
	}

	return r.client.Update(context.TODO(), target)
}

func (r *ReconcileSync) finalize(name string) {
	bc := r.bindingCache
	bc.mu.Lock()
	defer bc.mu.Unlock()

	bd, ok := bc.bindings[name]
	if !ok {
		return
	}

	switch bd.Mode {
	case digiv1.MatchMode:
		// flush a write to the target to remove the attribute
		bdTarget, err := helper.GetObj(r.client, &bd.Target)
		if err != nil {
			log.Println("finalize: unable to get target model:", bd.Target)
			return
		}

		old := bdTarget.DeepCopy()

		var empty interface{}
		err = unstructured.SetNestedField(bdTarget.Object, empty, core.AttrPathSlice(bd.Target.Path)...)

		if err != nil {
			log.Println("finalize: unable to set target attribute", err)
			return
		}

		err = r.client.Patch(context.TODO(), bdTarget, client.MergeFrom(old))
		if err != nil {
			log.Println("finalize: unable to patch target", err)
			return
		}
	case digiv1.SyncMode:
		// do nothing
	default:
	}
	log.Println("finalized", name)
}
