package graph

const (
	ActiveStatus   = "active"
	InactiveStatus = "inactive"
)

type Edge struct {
	Start  string
	End    string
	Status string
}
