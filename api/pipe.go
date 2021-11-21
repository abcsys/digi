package api

import (
	"context"
	"fmt"
	"strings"

	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/runtime"
	"sigs.k8s.io/controller-runtime/pkg/client"
	"sigs.k8s.io/controller-runtime/pkg/client/config"
	"sigs.k8s.io/controller-runtime/pkg/scheme"

	"digi.dev/digi/pkg/core"
	syncv1 "digi.dev/digi/space/sync/pkg/apis/digi/v1"
)

// XXX Move to core
type Piper struct {
	Source core.Auri `json:"source,omitempty"`
	Target core.Auri `json:"target,omitempty"`
}

type ChainPiper struct {
	Chain []*Piper
}

func NewPiper(s, t string) (*Piper, error) {
	si, err := ParseAuri(s)
	if err != nil {
		return nil, err
	}

	ti, err := ParseAuri(t)
	if err != nil {
		return nil, err
	}
	fmt.Println(si)
	return &Piper{
		Source: si,
		Target: ti,
	}, nil
}

func NewChainPiperFromStr(s string) (*Piper, error) {
	// XXX
	return &Piper{}, fmt.Errorf("unimplemented")
}

// Pipe creates a kind:Match sync binding between the source and target
// attributes; the source/target can be either a digivice or digilake; an
// arbitrary pair of attribute is not supported by the pipe call.
// TBD: use piper (that provides additional handling of sync binding)
func (p *Piper) Pipe() error {
	return p.createSyncBinding()
}

func (p *Piper) Unpipe() error {
	return p.deleteSyncBinding()
}

func (p *Piper) createSyncBinding() error {
	c, err := newClientForSyncBinding()
	if err != nil {
		return fmt.Errorf("unable to create sync binding: %v", err)
	}

	return c.Create(context.TODO(), p.newSyncBinding())
}

func (p *Piper) deleteSyncBinding() error {
	c, err := newClientForSyncBinding()
	if err != nil {
		return fmt.Errorf("unable to create api client for sync binding: %v", err)
	}
	return c.Delete(context.TODO(), p.newSyncBinding())
}

func (p *Piper) syncBindingName() string {
	var bdName string
	bdName = fmt.Sprintf("%s-%s-match-%s-%s", p.Source.SpacedName(), p.Source.Path, p.Target.Path, p.Target.SpacedName())
	return strings.ReplaceAll(bdName, "/", "-")
}

func (p *Piper) newSyncBinding() *syncv1.Sync {
	return &syncv1.Sync{
		ObjectMeta: metav1.ObjectMeta{
			Name: p.syncBindingName(),
			// XXX create it in meta ns
			Namespace: "default",
		},
		Spec: syncv1.SyncSpec{
			Mode:   "match",
			Source: p.Source,
			Target: p.Target,
		},
	}
}

func newClientForSyncBinding() (client.Client, error) {
	sm := runtime.NewScheme()
	SchemeBuilder := &scheme.Builder{
		GroupVersion: syncv1.SchemeGroupVersion,
	}
	SchemeBuilder.Register(&syncv1.Sync{})
	if err := SchemeBuilder.AddToScheme(sm); err != nil {
		return nil, err
	}

	// use the controller-runtime client
	options := client.Options{
		Scheme: sm,
	}

	c, err := client.New(config.GetConfigOrDie(), options)
	if err != nil {
		return nil, err
	}
	return c, nil
}
