package api

import (
	"fmt"

	"github.com/spf13/viper"

	"digi.dev/digi/api/config"
	"digi.dev/digi/pkg/core"
)

type Alias struct {
	Name string     `json:"name"`
	Duri *core.Auri `json:"auri"`
}

func init() {
	config.Load()
}

func (a *Alias) Set() error {
	aliases := make(map[string]*core.Auri)
	if err := viper.UnmarshalKey("alias", &aliases); err != nil {
		return err
	}
	aliases[a.Name] = a.Duri

	viper.Set("alias", aliases)
	return viper.WriteConfig()
}

func Resolve(name string) (*core.Auri, error) {
	aliases := make(map[string]*core.Auri)
	if err := viper.UnmarshalKey("alias", &aliases); err != nil {
		return nil, err
	}

	auri, ok := aliases[name]
	if !ok {
		return nil, fmt.Errorf("alias %s not found", name)
	}

	return auri, nil
}

func ResolveAndPrint(name string) error {
	auri, err := Resolve(name)
	if err != nil {
		return err
	}

	fmt.Println(auri)
	return nil
}

// ResolveFromLocal returns local alias cache
func ResolveFromLocal(name string) error {
	return ResolveAndPrint(name)
}

func ShowLocal() error {
	duris := make(map[string]*core.Duri)
	var aliases []Alias
	if err := viper.UnmarshalKey("alias", &duris); err == nil {
		for k, v := range duris {
			aliases = append(aliases, Alias{
				Name: k,
				Duri: v,
			})
		}
		Show(aliases)
		return nil
	} else {
		return err
	}
}

func Show(aliases []Alias) {
	for _, alias := range aliases {
		fmt.Println(alias.Name, ":", alias.Duri)
	}
}

func ClearAlias() error {
	aliases := make(map[string]*core.Auri)
	viper.Set("alias", aliases)
	return viper.WriteConfig()
}

// DiscoverAlias search the apiserver for all custom resources and
// generate aliases for them and set the local aliases.
func DiscoverAlias() ([]Alias, error) {
	duris, err := Discover()
	if err != nil {
		return nil, err
	}

	aliases := make([]Alias, len(duris))
	for i, duri := range duris {
		aliases[i] = Alias{
			Name: duri.Name,
			Duri: duri,
		}
	}
	return aliases, nil
}

func DiscoverAliasAndSet() error {
	aliases, err := DiscoverAlias()
	if err != nil {
		return err
	}

	for _, alias := range aliases {
		if err := alias.Set(); err != nil {
			return err
		}
	}
	return nil
}
