#!/bin/bash       

# This script file is used to collect raw data for the startup and actuation of lamp digis.
# The accompanying jupyter notebook is used to analyze and vizualize the data.

# latency test args
TEST_STARTUP_LATENCY=$1
STARTUP_LATENCY_FILE=$2 
NUMBER_LAMPS=$3
STARTUP_LATENCY_SLEEP=10 

# latency test args
TEST_STARTUP_STAGES_LATENCY=$1 
STARTUP_STAGES_LATENCY_FILE=$2 
STARTUP_STAGES_LATENCY_TESTS=$3
STARTUP_STAGES_LATENCY_SLEEP=5 

# actuation test args
TEST_ACTUATION_LATENCY=$1 
ACTUATION_LATENCY_FOLDER=$2 
ACTUATION_LATENCY_LAMPS=$3 
ACTUATION_SLEEP=5
ACTUATION_SETUP_SLEEP=10

TMP_FILE=/tmp/latency_test.yml
NUMBER_LAMPS=$3

function test_startup_latency() {
    # 
    # Digi startup latency benchmark. 
    # 
    # Args: 
    #   STARTUP_LATENCY_FILE - Output file for startup latency tests
    #   NUMBER_LAMPS - Number of lamps to test
    #   STARTUP_LATENCY_SLEEP - Time to wait before starting and testing Nth lamp

    echo "Testing startup latency..."
    echo "" > $STARTUP_LATENCY_FILE

    for (( i=0; i<$NUMBER_LAMPS; i++ ))
    do
        cur_lamp=$((i*10+1))
        next_lamp=$((10*(i+1))) # Next 10th lamp. Ex. if i=1, next_lamp=20
        echo "Testing lamp $next_lamp"

        for (( j=$cur_lamp; j<$next_lamp; j++ ))
        do
            digi run lamp l$j
        done
        sleep $STARTUP_LATENCY_SLEEP 
        echo "--------------------" >> $STARTUP_LATENCY_FILE
        echo "$next_lamp" >> $STARTUP_LATENCY_FILE
        { time digi run lamp l$next_lamp > /dev/null 2>&1 ; } 2>> $STARTUP_LATENCY_FILE
        echo "--------------------" >> $STARTUP_LATENCY_FILE
    done
}

function test_startup_stages_latency() {
    # 
    # Benchmark digi startup stages latency.
    # 
    # Args: 
    #   STARTUP_STAGES_LATENCY_FILE - Output file for startup latency tests
    #   STARTUP_STAGES_LATENCY_TESTS - Number of tests to run on lamp l1
    #   STARTUP_STAGES_LATENCY_SLEEP - Time to wait between tests

    echo "Testing startup stages latency... $STARTUP_STAGES_LATENCY_FILE $NUMBER_LAMPS"
    echo "" > $STARTUP_STAGES_LATENCY_FILE
    for (( i=0; i<$cl; i++ ))
    do
    echo "Test $i"
    echo "--------------------" >> $STARTUP_STAGES_LATENCY_FILE
    digi run lamp l1 >> $STARTUP_STAGES_LATENCY_FILE
    echo "--------------------" >> $STARTUP_STAGES_LATENCY_FILE
    sleep $STARTUP_STAGES_LATENCY_SLEEP 
    done
}

function actuate_lamp() {
    # 
    # Execute an actuation query on a single lamp.
    # 
    # Args: 
    #   $1 - Number of the lamp to actuate
    #   $2 - Intent change yaml query. Ex. '.spec.control.power.intent = "on"'
    #   TMP_FILE - file which temporary stores the digi k8s model
    #   ACTUATION_LATENCY_FILE - File to store benchmark results into

    # Actuate the lamp $1 with command specified at $2
    lamp=l$1
    #get lamp's config
    (kubectl get lamps $lamp -oyaml 2>/dev/null \
        || kubectl get lamps.v1.mock.digi.dev $lamp -oyaml) > $TMP_FILE
    yq -i "$2" $TMP_FILE # update fetched config value with yq
    kubectl apply -f $TMP_FILE > /dev/null 2>&1
    gdate -u +"%Y-%m-%dT%H:%M:%S.%6NZ" >> $ACTUATION_LATENCY_FILE
    rm $TMP_FILE
}

function test_lamp_actuation() {
    # 
    # Run actuation latency benchmark on all currently running lamps.
    # 
    # Args: 
    #   ACTUATION_LATENCY_FILE - file with actuation benchmark results
    

    echo "Testing actuation latency..."
    echo "" > $ACTUATION_LATENCY_FILE

    # match all running lamps
    num_lamps_running=$(kubectl get deployments | grep -E 'l[0-9]{1,2}' | wc -l)
    # to_test=$((num_lamps_running/5)) # sample 20% of the lamps
    to_test=30 # test 30 digi actuations for all N
    echo "Currently there are $num_lamps_running lamps running."
     
    # shuf below is used to randomly sample lamps to benchmark
    for i in $(shuf -i "1-$num_lamps_running" -n $to_test -r)
    do
        echo "Testing actuation of lamp $i"
        echo "--------------------" >> $ACTUATION_LATENCY_FILE
        echo "$i" >> $ACTUATION_LATENCY_FILE

        cur_time=$(gdate -u +"%Y-%m-%dT%H:%M:%S.%6NZ")
        echo $cur_time >> $ACTUATION_LATENCY_FILE

        echo "---" >> $ACTUATION_LATENCY_FILE 
        actuate_lamp $i '.spec.control.power.intent = "on"'
        echo "on" >> $ACTUATION_LATENCY_FILE
        sleep $ACTUATION_SLEEP
        actuate_lamp $i '.spec.control.power.intent = "off"'
        echo "off" >> $ACTUATION_LATENCY_FILE
        sleep $ACTUATION_SLEEP
            
        echo "*** digi output" >> $ACTUATION_LATENCY_FILE
        digi query l$i@model "event_ts>=$cur_time | sort -r event_ts" | zq -f json - >> $ACTUATION_LATENCY_FILE
        echo "*** docker stats output" >> $ACTUATION_LATENCY_FILE
        docker stats --no-stream | grep minikube >> $ACTUATION_LATENCY_FILE
        echo "--------------------" >> $ACTUATION_LATENCY_FILE
        echo ''
    done
}

function setup_and_test_actuate_lamp() {
    # 
    # Setup and run actuation latency benchmarks. Refreshes space and redeploys all digis on every run.
    # 
    # Args: 
    #   ACTUATION_LATENCY_LAMPS - Number of lamps to test in tens.
    #   ACTUATION_LATENCY_FOLDER - folder for the actuation benchmark results
    #   ACTUATION_SETUP_SLEEP - Time to wait after the setup to stabilize the system
    #   ACTUATION_LATENCY_LAMPS - Number of lamps to test in tens.

    mkdir -p $ACTUATION_LATENCY_FOLDER 

    for (( i=1; i<=$ACTUATION_LATENCY_LAMPS; i++ ))
    do
        digis_to_test="$((i))0"
        echo "Deleteting deployments for iteration $digis_to_test digis"
        digi space start
        kubectl delete deployments/l{,0,1,2,3,4,5,6,7,8,9,10}{0,1,2,3,4,5,6,7,8,9} --ignore-not-found
        sleep $ACTUATION_SETUP_SLEEP
        for (( z=1; z<=$digis_to_test; z++ ))
        do
            digi run lamp l$z
        done
        echo "Created $digis_to_test digis"
        sleep $ACTUATION_SETUP_SLEEP
        echo "Testing actuation latency for $digis_to_test digis"
        ACTUATION_LATENCY_FILE="$ACTUATION_LATENCY_FOLDER/actuation_latency_test_$digis_to_test.txt"
        test_lamp_actuation
    done
}

function clean_up() {
    k delete deployments/l{,0,1,2,3,4,5,6,7,8,9}{0,1,2,3,4,5,6,7,8,9} --ignore-not-found  
    sleep 10
# k delete deployments/l{,0,1,2,3,4,5,6,7,8,9}{0,1,2,3,4,5,6,7,8,9} --ignore-not-found  
}

if [ $TEST_STARTUP_LATENCY -eq 0 ]; then
    test_startup_latency
fi

if [ $TEST_STARTUP_STAGES_LATENCY -eq 1 ]; then
    test_startup_stages_latency
fi

if [ $TEST_ACTUATION_LATENCY -eq 2 ]; then
    setup_and_test_actuate_lamp
fi
