# Run instructions:

You have to be in the `mock` repo when running this script. Also use [this notebook](https://github.com/digi-project/notebooks/blob/main/digi_benchmarks.ipynb) to interpret the benchmark results.

### Running startup latency benchmarks.
1. `bash [PATH TO DIGI REPO]/benchmark/startup_actuation/test.sh 0 test.txt 10`
- The output will be saved in the `test.txt`
- Since we are primarily interested in benchmarking every 10th digi startup, `10` in the script will actually start 100 digis (N*10 digis started).

Note: the 0 corresponds to which command will be run.

### Running startup stage latency benchmarks.
1. You have to modify [digi Makefile](https://github.com/digi-project/digi/blob/0786b80869226793f786e60891271979e2d3b0e0/model/Makefile#L131-L140) with the following profiling code instead:
```
run: | prepare model
	gdate -u +"%Y-%m-%dT%H:%M:%S.%6NZ"
	kubectl exec `kubectl get pod --field-selector status.phase=Running -l app=lake -oname` \
    -- bash -c "zed drop -f $(NAME) >/dev/null 2>&1" || true
	gdate -u +"%Y-%m-%dT%H:%M:%S.%6NZ"
	cd $(build_dir)/deploy && mv $(CR) ./templates; \
	gdate -u +"%Y-%m-%dT%H:%M:%S.%6NZ" || true &&  \
	helm template -f values.yaml --set name=$(NAME) $(RUNFLAG) $(NAME) . > run.yaml && \
	gdate -u +"%Y-%m-%dT%H:%M:%S.%6NZ" || true && \
	kubectl delete -f run.yaml >/dev/null 2>&1 || true && \
	gdate -u +"%Y-%m-%dT%H:%M:%S.%6NZ" || true && \
	kubectl apply -f run.yaml >/dev/null || (echo "unable to run $(NAME), check $(CR)"; exit 1) && \
	gdate -u +"%Y-%m-%dT%H:%M:%S.%6NZ" || true && \
	(kubectl exec `kubectl get pod --field-selector status.phase=Running -l app=lake -oname` \
    -- bash -c "zed create $(NAME)") >/dev/null || echo "unable to create pool $(NAME)"
	gdate -u +"%Y-%m-%dT%H:%M:%S.%6NZ"
	rm -rf $(build_dir)
```
2. Make sure to reinstall digi with `make install` from the main repo.
3. `bash [PATH TO DIGI REPO]/benchmark/startup_actuation/test.sh 1 test.txt 10`
- The output will be saved in the `test.txt`
- The script will run 10 benchmarks by restarting `l1` lamp 10 times

### Running actuation latency benchmarks.
1. `bash [PATH TO DIGI REPO]/benchmark/startup_actuation/test.sh 2 tests/ 1`

- Results will be saved in the folder `tests/` which will be generated on the script run
- Similar to startup latency tests, actuation latency benchmark will first start 10 digis and run tests then wipe environment and run 20 digis... It will run tests up to `10n` where n is the last argument.