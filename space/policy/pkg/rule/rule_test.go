package rule

import (
	"fmt"
	"log"
	"testing"

	"github.com/itchyny/gojq"
)

func TestQueryRun_NumericTypes(t *testing.T) {
	query, err := gojq.Parse("if (.foo[0] == 2) then true else false end")
	if err != nil {
		log.Fatalln(err)
	}
	input := map[string]interface{}{"foo": []interface{}{1, 2, 3}}
	iter := query.Run(input) // or query.RunWithContext
	for {
		v, ok := iter.Next()
		if !ok {
			break
		}
		if err, ok := v.(error); ok {
			log.Fatalln(err)
		}
		fmt.Printf("%#v\n", v)
	}
}