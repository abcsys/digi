package k8s

import (
	"k8s.io/client-go/dynamic"
	"k8s.io/client-go/kubernetes"
	"k8s.io/client-go/rest"
	runtimecfg "sigs.k8s.io/controller-runtime/pkg/client/config"
)

type K8sClient struct {
	Config        *rest.Config
	DynamicClient dynamic.Interface
	Clientset     *kubernetes.Clientset
}

func NewClientSet() (*K8sClient, error) {
	// will use the current context in kubeconfig
	config := runtimecfg.GetConfigOrDie()

	// create dynamic client
	dc, err := dynamic.NewForConfig(config)
	if err != nil {
		return nil, err
	}

	// create the clientset
	cs, err := kubernetes.NewForConfig(config)
	if err != nil {
		return nil, err
	}

	return &K8sClient{
		Config:        config,
		DynamicClient: dc,
		Clientset:     cs,
	}, nil
}
