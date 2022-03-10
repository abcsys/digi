module digi.dev/digi

go 1.16

require (
	digi.dev/digi/space/sync v0.0.0
	github.com/banzaicloud/k8s-objectmatcher v1.6.1
	github.com/creack/pty v1.1.17
	github.com/silveryfu/inflection v1.1.0
	github.com/slok/kubewebhook v0.10.0
	github.com/spf13/cobra v1.2.1
	github.com/spf13/pflag v1.0.5
	github.com/spf13/viper v1.9.0
	github.com/stretchr/testify v1.7.0
	github.com/tidwall/sjson v1.2.3
	github.com/xlab/treeprint v1.1.0
	golang.org/x/term v0.0.0-20210317153231-de623e64d2a6
	gopkg.in/yaml.v2 v2.4.0
	k8s.io/api v0.19.0
	k8s.io/apimachinery v0.22.3
	k8s.io/client-go v12.0.0+incompatible
	sigs.k8s.io/controller-runtime v0.6.3
)

replace (
	digi.dev/digi v0.0.0 => ./
	digi.dev/digi/space/sync v0.0.0 => ./space/sync
	k8s.io/client-go => k8s.io/client-go v0.19.0
)
