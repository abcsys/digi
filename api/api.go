package api

import (
	"context"
)

type Interface interface {
	run(ctx context.Context, kind string, name ...string) error
	stop(ctx context.Context, name ...string) error
	test(ctx context.Context, kind string) error
	init(ctx context.Context, kind, group, version string) error
	gen(ctx context.Context, kind string) error
	build(ctx context.Context, kind string) error
	push(ctx context.Context, kind string) error
	pull(ctx context.Context, kind string) error
	rmk(ctx context.Context, kind string) error
	commit(ctx context.Context, name ...string) error
	list(ctx context.Context) error
	check(ctx context.Context, name ...string) error
	watch(ctx context.Context, name ...string) error
	log(ctx context.Context, name string) error
	attach(ctx context.Context, name string) error
	edit(ctx context.Context, name string) error
	query(ctx context.Context, name string) error
	visualize(ctx context.Context, name string) error
	connect(ctx context.Context, name string, local string, remote string) error
	expose(ctx context.Context, name string, port string) error
}
