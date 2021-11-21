package main

import (
	"context"
	"encoding/json"
	"flag"
	"fmt"
	"log"
	"net/http"
	"os"
	"strings"
	"sync"

	"github.com/banzaicloud/k8s-objectmatcher/patch"
	adv1beta1 "k8s.io/api/admission/v1beta1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/apis/meta/v1/unstructured"
	"k8s.io/apimachinery/pkg/runtime/schema"
	"k8s.io/apimachinery/pkg/types"
	"k8s.io/client-go/dynamic"
	"k8s.io/client-go/kubernetes"
	"k8s.io/client-go/rest"
	"k8s.io/client-go/restmapper"

	"digi.dev/digi/space"
	"digi.dev/digi/space/mount/webhook/graph"
	whhttp "digi.dev/digi/space/mount/webhook/http"
	"digi.dev/digi/space/mount/webhook/util"
	vlwh "digi.dev/digi/space/mount/webhook/validating"
)

type Validator struct {
	apiGroups map[string]*schema.GroupVersion
	apiClient *apiClient
	gc        *graphCache
}

type graphCache struct {
	mt   *graph.MultiTree
	lock sync.RWMutex
}

type apiClient struct {
	dynamic dynamic.Interface
	generic kubernetes.Interface
}

type config struct {
	certFile           string
	keyFile            string
	addr               string
	apiVersionedGroups string
}

// XXX: handle mode
type mode string

type compositionRefs struct {
	mounts  map[string]mode
	// XXX remove yields
	yields  map[string]mode
}

func NewApiClient(config *rest.Config) (*apiClient, error) {
	dc, err := dynamic.NewForConfig(config)
	if err != nil {
		return nil, fmt.Errorf("failed to create dynamic client: %v", err)
	}

	kc, err := kubernetes.NewForConfig(config)
	if err != nil {
		return nil, fmt.Errorf("failed to create generic client: %v", err)
	}
	return &apiClient{
		dynamic: dc,
		generic: kc,
	}, nil
}

func (v *Validator) discoverGraph() error {
	grs, err := restmapper.GetAPIGroupResources(v.apiClient.generic.Discovery())
	if err != nil {
		return fmt.Errorf("unable to discover resources: %v", err)
	}

	var edges []*graph.Edge
	// XXX: handle connect edges

	for _, gr := range grs {

		// scan versioned api groups
		for ver, resources := range gr.VersionedResources {
			ag := &schema.GroupVersion{
				Group:   gr.Group.Name,
				Version: ver,
			}

			if _, ok := v.apiGroups[ag.String()]; !ok {
				log.Printf("skip api group: %s", ag)
				continue
			}

			// scan resources within api group
			for _, resource := range resources {
				gvr := schema.GroupVersionResource{
					Group:    gr.Group.Name,
					Version:  ver,
					Resource: resource.Name,
				}

				log.Printf("scan resource: %s", resource.Name)

				// skip sub-resources
				if strings.Contains(resource.Name, "/") {
					log.Println("skipped..")
					continue
				}

				// get unstructured objects of the resource
				dyRes := v.apiClient.dynamic.Resource(gvr)

				result, err := dyRes.List(context.TODO(), metav1.ListOptions{})
				if err != nil {
					log.Printf("unable to list resources %s: %v", gvr.String(), err)
				}

				// scan each object
				for _, obj := range result.Items {
					oid := objId(&obj, resource.Namespaced)
					log.Printf("scan object: %s", oid)

					cRefs := getCompositionRefs(&obj)
					log.Printf("composition refs: %v", cRefs)

					// mounts
					edges = append(edges, mountEdges(oid, cRefs)...)

					// XXX: connects
				}
			}
		}
	}

	v.gc.lock.Lock()
	defer v.gc.lock.Unlock()

	// construct digi-graph
	v.gc.mt = graph.NewMultiTree()

	// proc mounts
	if err := v.addMountNodeAndEdges(edges); err != nil {
		return fmt.Errorf("unable to create digi graph: %s", err)
	}

	// XXX: proc connects
	return nil
}

func objId(obj *unstructured.Unstructured, namespaced bool) string {
	name := obj.GetName()
	var path string
	if namespaced {
		path = types.NamespacedName{
			Name:      name,
			Namespace: obj.GetNamespace(),
		}.String()
	} else {
		path = name
	}
	return path
}

func mountEdges(parent string, cRefs *compositionRefs) []*graph.Edge {
	var edges []*graph.Edge
	for name := range cRefs.mounts {
		var status = graph.ActiveStatus

		if _, ok := cRefs.yields[name]; ok {
			status = graph.InactiveStatus
		}

		edges = append(edges, &graph.Edge{
			Start:  parent,
			End:    name,
			Status: status,
		})
	}
	return edges
}

func (v *Validator) addMountNodeAndEdges(edges []*graph.Edge) error {
	for _, e := range edges {
		s, e := e.Start, e.End
		v.gc.mt.AddNode(s)
		v.gc.mt.AddNode(e)
		err := v.gc.mt.AddEdge(s, e)
		if err != nil {
			return err
		}
	}

	log.Printf("multitree: %s", v.gc.mt)
	return nil
}

// getFlattenedRefs returns references without the kind information
func getFlattenRefs(prefix string, o *unstructured.Unstructured) map[string]mode {
	refs := make(map[string]mode)
	ou := o.UnstructuredContent()

	if refByKind, ok := ou[prefix]; !ok {
	} else {
		for _, v := range refByKind.(map[string]interface{}) {
			for n, m := range v.(map[string]interface{}) {
				refs[n] = mode(m.(string))
			}
		}
	}
	return refs
}

func getCompositionRefs(o *unstructured.Unstructured) *compositionRefs {
	f := getFlattenRefs
	return &compositionRefs{
		mounts:  f(space.MountAttrPath, o),
	}
}

func (v *Validator) doCreate(njson []byte) (vlwh.ValidatorResult, error) {
	var obj *unstructured.Unstructured
	if err := json.Unmarshal([]byte(njson), &obj); err != nil {
		return vlwh.ValidatorResult{}, fmt.Errorf("create: unable to parse object: %v", err)
	}

	oid := objId(obj, true)
	cRefs := getCompositionRefs(obj)

	// handle mount
	edges := mountEdges(oid, cRefs)

	v.gc.lock.Lock()
	defer v.gc.lock.Unlock()

	err := v.addMountNodeAndEdges(edges)
	if err != nil {
		return vlwh.ValidatorResult{
			Valid:   false,
			Message: fmt.Sprintf("%v", err),
		}, nil
	}

	// XXX: handle connect

	return vlwh.ValidatorResult{Valid: true}, nil
}

func (v *Validator) doUpdate(njson, ojson []byte) (vlwh.ValidatorResult, error) {
	var no, oo *unstructured.Unstructured

	// parse objects and calculate diff
	if err := json.Unmarshal([]byte(njson), &no); err != nil {
		return vlwh.ValidatorResult{}, fmt.Errorf("update: unable to parse new object: %v", err)
	}

	if err := json.Unmarshal([]byte(ojson), &oo); err != nil {
		return vlwh.ValidatorResult{}, fmt.Errorf("update: unable to parse old object: %v", err)
	}

	patchResult, err := patch.DefaultPatchMaker.Calculate(no, oo)
	if err != nil {
		return vlwh.ValidatorResult{}, fmt.Errorf("unable to get diff: %v", err)
	}

	log.Printf("diff %v", patchResult)
	// XXX: access verbs, single-writer check
	// XXX: disallow access to fields except for spec
	// TBD: check if update mount/yield/connect reference and if it is valid
	// TBD: update digi-graph
	return vlwh.ValidatorResult{Valid: true}, nil
}

func (v *Validator) Validate(_ context.Context, ar *adv1beta1.AdmissionReview) (vlwh.ValidatorResult, error) {
	log.Printf("do: %s", ar.Request.Operation)
	njson, ojson := ar.Request.Object.Raw, ar.Request.OldObject.Raw
	switch ar.Request.Operation {
	case adv1beta1.Create:
		return v.doCreate(njson)
	case adv1beta1.Update:
		return v.doUpdate(njson, ojson)
	}

	res := vlwh.ValidatorResult{
		Valid:   true,
		Message: "pass unhandled verb",
	}
	return res, nil
}

func initFlags() *config {
	cfg := &config{}

	fl := flag.NewFlagSet(os.Args[0], flag.ExitOnError)
	fl.StringVar(&cfg.certFile, "tls-cert-file", "", "TLS certificate file")
	fl.StringVar(&cfg.keyFile, "tls-key-file", "", "TLS key file")
	fl.StringVar(&cfg.addr, "listen-addr", ":8080", "The address to start the server")
	fl.StringVar(&cfg.apiVersionedGroups, "api-versioned-groups", "", "api versioned groups to handle")

	if err := fl.Parse(os.Args[1:]); err != nil {
		panic(err)
	}
	return cfg
}

func apiGroupFromStr(raw string) (map[string]*schema.GroupVersion, error) {
	ags := make(map[string]*schema.GroupVersion)
	for _, k := range strings.Split(raw, ",") {
		ag, err := schema.ParseGroupVersion(k)
		if err != nil {
			return nil, err
		}
		ags[ag.String()] = &ag
	}
	return ags, nil
}

func main() {
	cfg := initFlags()

	// parse api groups we are going to manage
	ags, err := apiGroupFromStr(cfg.apiVersionedGroups)
	if err != nil {
		log.Fatalf("failed to parse api groups: %v", err)
	}

	// create apiserver client instances
	kubeconfig, err := util.LoadRESTConfig("/etc/kubeconfig")
	if err != nil {
		log.Fatalf("failed to load kubeconfig: %v", err)
	}
	ac, err := NewApiClient(kubeconfig)
	if err != nil {
		log.Fatalf("failed to connect api clients: %v", err)
	}

	// create our validator
	vl := &Validator{
		apiGroups: ags,
		apiClient: ac,
		gc: &graphCache{
			mt: graph.NewMultiTree(),
		},
	}

	// create webhook with the validator
	wh, err := vlwh.NewWebhook(vlwh.WebhookConfig{
		Name: "dspace-mounter",
	}, vl)
	if err != nil {
		log.Fatalf("error creating webhook: %s", err)
	}

	// build digi-graph from the apiserver
	go func() {
		err := vl.discoverGraph()
		if err != nil {
			log.Fatalf("error discovering digi-graph: %s", err)
		}
	}()

	// serve the webhook.
	log.Printf("Listening on %s", cfg.addr)
	err = http.ListenAndServeTLS(cfg.addr, cfg.certFile, cfg.keyFile, whhttp.MustHandlerFor(wh))
	if err != nil {
		log.Fatalf("error serving webhook: %s", err)
	}
}

func init() {
	log.SetFlags(log.Lmicroseconds)
}
