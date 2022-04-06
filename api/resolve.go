package api

// ResolveFromLocal returns local alias cache
func ResolveFromLocal(name string) error {
	return ResolveAndPrint(name)
}

// ResolveWithScope r1.lamp@energy
func ResolveWithScope(duri string) (string, error) {

	return "", nil
}

// TBD
func FetchMounts() (string, error) {
	return "", nil
}
