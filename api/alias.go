package api

import (
	"fmt"
	"github.com/spf13/viper"

	"digi.dev/digi/api/config"
	"digi.dev/digi/pkg/core"
)

type Alias struct {
	Name string     `json:"name"`
	Auri *core.Auri `json:"auri"`
}

func init() {
	config.Load()
}

func (a *Alias) Set() error {
	aliases := make(map[string]*core.Auri)
	if err := viper.UnmarshalKey("alias", &aliases); err != nil {
		return err
	}
	aliases[a.Name] = a.Auri

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

func ShowAll() error {
	aliases := make(map[string]*core.Auri)
	if err := viper.UnmarshalKey("alias", &aliases); err != nil {
		return err
	}

	for k, v := range aliases {
		fmt.Println(k, ":", v)
	}
	return nil
}

func ClearAlias() error {
	aliases := make(map[string]*core.Auri)
	viper.Set("alias", aliases)
	return viper.WriteConfig()
}
