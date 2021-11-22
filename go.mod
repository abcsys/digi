module digi.dev/digi

go 1.16

require (
	digi.dev/digi/space/sync v0.0.0
	github.com/Azure/go-autorest v13.3.2+incompatible // indirect
	github.com/DATA-DOG/go-sqlmock v1.5.0 // indirect
	github.com/HdrHistogram/hdrhistogram-go v1.0.0 // indirect
	github.com/Masterminds/sprig/v3 v3.2.2 // indirect
	github.com/Masterminds/squirrel v1.5.0 // indirect
	github.com/NYTimes/gziphandler v1.1.1 // indirect
	github.com/appscode/jsonpatch v0.0.0-20180911074601-5af499cf01c8 // indirect
	github.com/banzaicloud/k8s-objectmatcher v1.6.1
	github.com/blang/semver/v4 v4.0.0 // indirect
	github.com/brimdata/zed v0.33.0 // indirect
	github.com/cloudflare/cfssl v1.5.0 // indirect
	github.com/deislabs/oras v0.11.1 // indirect
	github.com/fatih/color v1.12.0 // indirect
	github.com/fvbommel/sortorder v1.0.1 // indirect
	github.com/go-logr/zapr v0.4.0 // indirect
	github.com/gobuffalo/flect v0.2.3 // indirect
	github.com/h2non/filetype v1.1.1 // indirect
	github.com/h2non/go-is-svg v0.0.0-20160927212452-35e8c4b0612c // indirect
	github.com/iancoleman/strcase v0.0.0-20191112232945-16388991a334 // indirect
	github.com/itchyny/gojq v0.12.5 // indirect
	github.com/jinzhu/inflection v1.0.0
	github.com/jmoiron/sqlx v1.3.1 // indirect
	github.com/joelanford/go-apidiff v0.1.0 // indirect
	github.com/joelanford/ignore v0.0.0-20210607151042-0d25dc18b62d // indirect
	github.com/lib/pq v1.10.0 // indirect
	github.com/mattn/go-shellwords v1.0.11 // indirect
	github.com/mikefarah/yq/v3 v3.0.0-20201202084205-8846255d1c37 // indirect
	github.com/mitchellh/copystructure v1.1.1 // indirect
	github.com/onsi/gomega v1.15.0 // indirect
	github.com/opentracing/opentracing-go v1.2.0 // indirect
	github.com/operator-framework/api v0.3.20 // indirect
	github.com/operator-framework/operator-lib v0.2.0 // indirect
	github.com/operator-framework/operator-registry v1.15.1 // indirect
	github.com/operator-framework/operator-sdk v0.18.0 // indirect
	github.com/slok/kubewebhook v0.10.0
	github.com/spf13/cobra v1.2.1
	github.com/spf13/viper v1.9.0
	github.com/thoas/go-funk v0.8.0 // indirect
	github.com/tidwall/sjson v1.2.3
	github.com/uber-go/atomic v1.4.0 // indirect
	github.com/uber/jaeger-client-go v2.25.0+incompatible // indirect
	github.com/uber/jaeger-lib v2.4.0+incompatible // indirect
	github.com/xlab/treeprint v1.1.0
	go.etcd.io/etcd v0.5.0-alpha.5.0.20200910180754-dd1b699fc489 // indirect
	go.etcd.io/etcd/server/v3 v3.5.0 // indirect
	go.uber.org/zap v1.19.0 // indirect
	golang.org/x/crypto v0.0.0-20210817164053-32db794688a5 // indirect
	golang.org/x/time v0.0.0-20210723032227-1f47c861a9ac // indirect
	gomodules.xyz/jsonpatch/v2 v2.2.0 // indirect
	gopkg.in/yaml.v2 v2.4.0
	helm.sh/helm/v3 v3.3.0 // indirect
	k8s.io/api v0.18.6
	k8s.io/apimachinery v0.22.3
	k8s.io/client-go v12.0.0+incompatible
	k8s.io/code-generator v0.22.2 // indirect
	k8s.io/component-base v0.22.2 // indirect
	k8s.io/component-helpers v0.20.0-alpha.2 // indirect
	k8s.io/kubectl v0.18.6 // indirect
	sigs.k8s.io/apiserver-network-proxy/konnectivity-client v0.0.22 // indirect
	sigs.k8s.io/controller-runtime v0.6.3
	sigs.k8s.io/controller-tools v0.4.1 // indirect
	sigs.k8s.io/kind v0.10.0 // indirect
	sigs.k8s.io/kubebuilder v1.0.9-0.20200805184228-f7a3b65dd250 // indirect
	sigs.k8s.io/kustomize/kustomize/v4 v4.0.5 // indirect
	sigs.k8s.io/kustomize/kyaml v0.10.21 // indirect
)

replace (
	digi.dev/digi v0.0.0 => ./
	digi.dev/digi/space/sync v0.0.0 => ./space/sync
	k8s.io/client-go => k8s.io/client-go v0.18.2
)
