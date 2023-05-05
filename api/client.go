package api

import (
	"context"
	"encoding/json"
	"fmt"
	"strings"
	"time"

	"github.com/silveryfu/inflection"

	"digi.dev/digi/api/k8s"
	"digi.dev/digi/pkg/core"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/apis/meta/v1/unstructured"
	"k8s.io/apimachinery/pkg/runtime/schema"
	"k8s.io/client-go/restmapper"
)

type Client struct {
	k *k8s.K8sClient
}

func NewClient() (*Client, error) {
	kc, err := k8s.NewClientSet()
	if err != nil {
		return nil, err
	}
	return &Client{
		k: kc,
	}, nil
}

// Discover returns all digis as DURIs/AURIs on the apiserver
// TODO filter the CRs by matching with the digi labels
func Discover() ([]*core.Duri, error) {
	var duris []*core.Duri
	clientSet, err := k8s.NewClientSet()
	if err != nil {
		return nil, err
	}

	dynamicClient := clientSet.DynamicClient
	if err != nil {
		return nil, err
	}

	// Retrieve the list of CRDs.
	crdList, err := dynamicClient.Resource(
		schema.GroupVersionResource{
			Group:    "apiextensions.k8s.io",
			Version:  "v1",
			Resource: "customresourcedefinitions"}).
		List(context.TODO(), metav1.ListOptions{})
	if err != nil {
		return nil, err
	}

	// Iterate through the list of CRDs and retrieve the custom resources.
	for _, crd := range crdList.Items {
		version := crd.Object["spec"].(map[string]interface{})["versions"].([]interface{})[0].(map[string]interface{})["name"].(string)
		group := crd.Object["spec"].(map[string]interface{})["group"].(string)
		kind := crd.Object["spec"].(map[string]interface{})["names"].(map[string]interface{})["kind"].(string)

		resource, err := dynamicClient.Resource(
			schema.GroupVersionResource{
				Group:    group,
				Version:  version,
				Resource: inflection.Plural(strings.ToLower(kind))}).
			Namespace("default").List(context.TODO(), metav1.ListOptions{})
		if err != nil {
			fmt.Printf("failed to list resources: %v\n; continue", err)
			continue
		}
		for _, item := range resource.Items {
			namespace := item.Object["metadata"].(map[string]interface{})["namespace"].(string)
			name := item.Object["metadata"].(map[string]interface{})["name"].(string)
			duris = append(duris, &core.Duri{
				Kind: core.Kind{
					Group:   group,
					Version: version,
					Name:    kind,
				},
				Namespace: namespace,
				Name:      name,
			})
		}
	}
	return duris, nil
}

// ParseAuri returns an Auri from a slash separated string.
// The following string formats are allowed:
//  1. /group/ver/schema_name/namespace/name.[];
//  2. /group/ver/schema_name/name.[] (use default namespace);
//  3. /namespace/name.[];
//  4. /name.[] (use alias);
//  5. name.[] (use alias);
//
// .[]: model attributes
func ParseAuri(s string) (core.Auri, error) {
	ss := strings.Split(s, fmt.Sprintf("%c", core.UriSeparator))

	splitAttr := func(s string) []string {
		return strings.Split(s, fmt.Sprintf("%c", core.AttrPathSeparator))
	}

	fromAlias := func(s string) (core.Auri, error) {
		ss := splitAttr(s)
		auri, err := Resolve(ss[0])
		if err != nil {
			return core.Auri{}, err
		}
		if len(ss) > 1 {
			auri.Path = strings.Join(ss[1:], fmt.Sprintf("%c", core.AttrPathSeparator))
		}
		return *auri, nil
	}

	var g, v, kn, ns, n, path, other string
	switch len(ss) {
	case 6:
		g, v, kn, ns, other = ss[1], ss[2], ss[3], ss[4], ss[5]
	case 5:
		g, v, kn, ns, other = ss[1], ss[2], ss[3], core.DefaultNamespace, ss[4]
	case 3:
		return core.Auri{}, fmt.Errorf("unimplemented")
	case 2:
		return fromAlias(ss[1])
	case 1:
		return fromAlias(ss[0])
	default:
		return core.Auri{}, fmt.Errorf("auri needs to have either 5, 2, or 1 fields, "+
			"given %d in %s; each field starts with a '/' except for single "+
			"name on default namespace", len(ss)-1, s)
	}

	ss = splitAttr(other)
	if len(ss) > 1 {
		n = ss[0]
		path = strings.Join(ss[1:], fmt.Sprintf("%c", core.AttrPathSeparator))
	} else {
		n = other
		path = ""
	}

	return core.Auri{
		Kind: core.Kind{
			Group:   g,
			Version: v,
			Name:    kn,
		},
		Namespace: ns,
		Name:      n,
		Path:      path,
	}, nil
}

func (c *Client) GetModelJson(ar *core.Auri) (string, error) {
	gvr := ar.Gvr()
	d, err := c.k.DynamicClient.Resource(gvr).Namespace(ar.Namespace).Get(context.TODO(), ar.Name, metav1.GetOptions{})
	if err != nil {
		return "", fmt.Errorf("unable to get digi %v: %v", gvr, err)
	}

	j, err := json.MarshalIndent(d, "", "  ")
	if err != nil {
		return "", fmt.Errorf("unable to parse digi %s: %v", j, err)
	}

	return string(j), nil
}

// UpdateFromJson updates the API resource on the apiserver specified in the given json string.
// It uses the resource discovery and dynamic client to avoid unmarshalling into a concrete type.
func (c *Client) UpdateFromJson(j string, numRetry int) error {
	var obj *unstructured.Unstructured
	var err error
	if err = json.Unmarshal([]byte(j), &obj); err != nil {
		return fmt.Errorf("unable to unmarshall %s: %v", j, err)
	}
	// update the target
	for i := 1; i <= (numRetry + 1); i++ {
		res, err := c.getResource(obj)
		if err != nil {
			// don't retry on resource fetch error
			return err
		}
		// retry in case of update conflict;
		// add a buffer to try avoiding apiserver throttling
		_, err = c.k.DynamicClient.Resource(res).Namespace(obj.GetNamespace()).Update(context.TODO(), obj, metav1.UpdateOptions{})
		if err == nil {
			break
		} else if i < numRetry {
			fmt.Printf("retrying %d time due to %v \n", i+1, err)
			time.Sleep(2 * time.Second)
		}
	}
	return err
}

func (c *Client) getResource(obj *unstructured.Unstructured) (schema.GroupVersionResource, error) {
	gvk := obj.GroupVersionKind()
	gk := schema.GroupKind{Group: gvk.Group, Kind: gvk.Kind}

	// XXX use controller-runtime's generic client to avoid the discovery? (see syncer)
	// TODO measure time spent on discovery
	groupResources, err := restmapper.GetAPIGroupResources(c.k.Clientset.Discovery())
	if err != nil {
		return schema.GroupVersionResource{}, fmt.Errorf("unable to discover resources: %v", err)
	}

	rm := restmapper.NewDiscoveryRESTMapper(groupResources)
	mapping, err := rm.RESTMapping(gk, gvk.Version)

	if err != nil {
		return schema.GroupVersionResource{}, fmt.Errorf("unable to map resource: %v", err)
	}
	return mapping.Resource, nil
}
