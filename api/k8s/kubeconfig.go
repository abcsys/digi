package k8s

import (
	"fmt"
	"io/ioutil"
	"log"
	"os"
	"os/user"
	"path/filepath"
	"regexp"

	"k8s.io/client-go/tools/clientcmd"
	clientcmdapi "k8s.io/client-go/tools/clientcmd/api"
)

var (
	// local kube config used by kubectl
	kubeConfigFile string
)

func init() {
	usr, err := user.Current()
	if err != nil {
		log.Fatal(err)
	}

	kubeConfigFile = filepath.Join(usr.HomeDir, ".kube", "config")
}

type KubeConfig = clientcmdapi.Config

func KubeConfigFile() string {
	return kubeConfigFile
}

func LoadKubeConfig(src ...string) (*KubeConfig, error) {
	var file string

	if len(src) > 0 {
		file = src[0]
	} else {
		file = KubeConfigFile()
	}

	config, err := clientcmd.LoadFromFile(file)

	if err != nil && !os.IsNotExist(err) {
		return nil, fmt.Errorf("error loading kube config %s: %v", file, err)
	}

	if config == nil {
		config = clientcmdapi.NewConfig()
	}

	return config, nil
}

func Clusters(kc *KubeConfig) []string {
	ids := make([]string, len(kc.Clusters)-1)

	for k := range kc.Clusters {
		ids = append(ids, k)
	}

	return ids
}

func Users(kc *KubeConfig) []string {
	ids := make([]string, len(kc.AuthInfos)-1)

	for k := range kc.AuthInfos {
		ids = append(ids, k)
	}

	return ids
}

func Contexts(kc *KubeConfig) []string {
	ids := make([]string, len(kc.Contexts)-1)

	for k := range kc.Contexts {
		ids = append(ids, k)
	}

	return ids
}

func CurrentContext(kc *KubeConfig) string {
	return kc.CurrentContext
}

func ClusterToContextMap(kc *KubeConfig) map[string]string {
	cm := make(map[string]string)
	for n, c := range kc.Contexts {
		cm[n] = c.Cluster
	}
	return cm
}

func ClusterExistsLocal(id string) (bool, error) {
	localConfig, err := LoadKubeConfig(kubeConfigFile)
	return clusterExists(id, localConfig), err
}

func clusterExists(id string, config *KubeConfig) bool {
	_, ok := config.Clusters[id]
	return ok
}

func DeleteKubeConfig(kc *KubeConfig, id string) error {
	delete(kc.Clusters, id)
	delete(kc.AuthInfos, id) //XXX id may not be the same as the user name
	delete(kc.Contexts, id)

	return nil
}

// MergeKubeConfigs merges a given set of kubeconfigs, assuming they are all valid, returns the merged kubeconfig
// The precedence is taken as the argument order, e.g., MergeKubeConfigs(A, B) will merge A to B
func MergeKubeConfigs(kcs ...*KubeConfig) (*KubeConfig, error) {
	files := make([]string, len(kcs))

	for _, k := range kcs {
		err := func() error {
			f, _ := ioutil.TempFile("", "")

			if err := clientcmd.WriteToFile(*k, f.Name()); err != nil {
				return err
			}
			files = append(files, f.Name())
			return nil
		}()

		if err != nil {
			_ = DeleteFiles(files...)
			return nil, fmt.Errorf("unable to merge: %v", err)
		}
	}

	loadingRules := clientcmd.ClientConfigLoadingRules{
		Precedence: files,
	}

	return loadingRules.Load()
}

func WriteKubeConfig(c *KubeConfig, dest ...string) error {
	var file string
	if len(dest) > 0 {
		file = dest[0]
	} else {
		file = KubeConfigFile()
	}

	return clientcmd.WriteToFile(*c, file)
}

func FixKubeConfig(file, clusterID, clusterAddr string, modifiers []string) error {
	config, err := clientcmd.LoadFromFile(file)

	if err != nil {
		return err
	}

	// Fixing the cluster entries
	if err := func() error {
		// Update the cluster server (i.e., the master node)'s address to the given address; address could be a URL or an IP
		var oldName string
		var cluster *clientcmdapi.Cluster

		if !(ValidURL(clusterAddr) || ValidIP(clusterAddr)) {
			return fmt.Errorf("invalid address: %s", clusterAddr)
		}

		// here we assume there is only one master entry in the kube config; for future, we need to validate the default
		// cluster name against kubeConfigClusterIDMaster; federation api may creates multiple entries.
		// same for the context entry
		nclusters := len(config.Clusters)
		if nclusters > 1 {
			return fmt.Errorf("the master config file contains multiple clusters: %d", nclusters)
		}

		for oldName, cluster = range config.Clusters {
		}

		cluster.Server = clusterAddr

		// rename the cluster
		config.Clusters[clusterID] = cluster
		delete(config.Clusters, oldName)

		return nil
	}(); err != nil {
		return err
	}

	// Fixing the context entries
	if err := func() error {
		// Rename current context if it is the one we want to replace
		config.CurrentContext = clusterID

		// Replace the cluster ID fields from a k8s master node; update context object
		var oldName string
		var context *clientcmdapi.Context

		ncontexts := len(config.Contexts)
		if ncontexts > 1 {
			return fmt.Errorf("the master config file contains multiple contexts: %d", ncontexts)
		}

		for oldName, context = range config.Contexts {
		}

		context.Cluster = clusterID

		// rename the context
		config.Contexts[clusterID] = context
		delete(config.Contexts, oldName)

		return nil
	}(); err != nil {
		return err
	}

	// fix by the modifiers
	if err := func() error {
		re := regexp.MustCompile("(\\w+)=([\\S]+)")

		for _, m := range modifiers {
			// validate modifier
			matched := re.FindAllStringSubmatch(m, -1)
			if len(matched) == 0 {
				return fmt.Errorf("unable to parse modifier: %s", m)
			}
			kv := matched[0]

			// update; a list of supported modifiers;
			// TODO: we should allow same syntax as the kube config yaml, e.g., cluster.server
			switch kv[1] {
			case "server":
				config.Clusters[clusterID].Server = kv[2]
			default:
				return fmt.Errorf("unsupported modifier: %s", kv[0])
			}
		}

		return nil
	}(); err != nil {
		return err
	}

	// write back
	return clientcmd.WriteToFile(*config, file)
}
