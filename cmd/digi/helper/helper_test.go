package helper

import (
	"testing"

	"github.com/stretchr/testify/assert"
)

func TestExpandArgs(t *testing.T) {
	assert.Equal(t, []string{"l1", "l2", "l3"}, ExpandArgs([]string{"l{1..3}"}))
	assert.Equal(t, []string{"l11", "l12", "l13", "l21", "l22", "l23", "l31", "l32", "l33"}, ExpandArgs([]string{"l{1..3}{1..3}"}))
	assert.Equal(t, []string{"l11", "l12", "l13", "l21", "l22", "l23", "l31", "l32", "l33", "l1", "l2", "l3"}, ExpandArgs([]string{"l{1..3}{1..3}", "l{1..3}"}))
}

func TestIsExpandSyntax(t *testing.T) {
	assert.True(t, isExpandSyntax("l{1..3}"))
	assert.True(t, isExpandSyntax("l{1..3}{1..3}"))
	assert.True(t, isExpandSyntax("l{1..3}{1..3}{1..3}"))
	assert.False(t, isExpandSyntax("l{1..2"))
	assert.False(t, isExpandSyntax("l1..2}"))
	assert.False(t, isExpandSyntax("l1..2"))
	assert.False(t, isExpandSyntax("l1"))
}
