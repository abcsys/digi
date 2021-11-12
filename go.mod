module digi.dev/digi

go 1.16

require (
	github.com/jinzhu/inflection v1.0.0
	github.com/spf13/cobra v1.2.1
	github.com/spf13/viper v1.9.0
	gopkg.in/yaml.v2 v2.4.0
	k8s.io/apimachinery v0.22.3
	k8s.io/client-go v0.22.3
	sigs.k8s.io/controller-runtime v0.6.3
)

replace k8s.io/client-go => k8s.io/client-go v0.18.2
