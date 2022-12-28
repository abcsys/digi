import sys
import subprocess
from multiprocessing import Process
import requests
import threading
from threading import Timer, Thread
from enum import Enum
import json
import subprocess

import digi

ZED_LAKE_URL = "http://localhost:9867"
POLL_INTERVAL_SECONDS = 10.0
SPAWNED_THREADS = []

POOL_NAME_MAP = {}
HEADS = {}
BRANCHES = {}

def dict_from_data_line(data_line):
    data_line_str = str(data_line)
    
    try:
        contents = data_line_str[data_line_str.index("{") : data_line_str.rindex("}") + 1] #previous end was -1
        contents = contents[1:-1]
        #digi.logger.info("STUFF")
        #digi.logger.info(contents)
        
        data_line_dict = {}
        
        pairs = contents.split(",")
        for pair in pairs:
            curr_pair = pair.split(":")
            if curr_pair[1][0] == "\"":
                curr_pair[1] = curr_pair[1][1:-1]
            data_line_dict[curr_pair[0]] = curr_pair[1]
        #digi.logger.info(data_line_dict)
        return data_line_dict
    except:
        return None
    
def parse_delete_pool(data_line):
    spec = digi.util.get_spec("digi.dev", "v1", "lakes", "lake", "default")[0]
    new_spec = {}
    
    agg = spec.get("aggStats", None)
    if agg is not None:
        agg["num_pools"] -= 1
        new_spec["aggStats"] = agg
    
    pools = spec.get("pools", None)
    if pools is not None:
        data_line_str = str(data_line)
        
        data_line_dict  = dict_from_data_line(data_line)
        
        pool_id = data_line_dict["pool_id"]
        pools[pool_id] = None
        new_spec["pools"] = pools
        
        HEADS.pop(pool_id)
        POOL_NAME_MAP.pop(pool_id)
        
    #digi.logger.info(new_spec)
    
    res, err = digi.util.patch_spec("digi.dev", "v1", "lakes", "lake", "default", new_spec)
    
                
def parse_new_pool(data_line):
    spec = digi.util.get_spec("digi.dev", "v1", "lakes", "lake", "default")[0]
    new_spec = {}
    
    agg = spec.get("aggStats", {"num_pools" : 0})
    agg["num_pools"] += 1
    new_spec["aggStats"] = agg
    
    pools = spec.get("pools", {})
    data_line_str = str(data_line)
    
    data_line_dict  = dict_from_data_line(data_line)
    
    pool_id = data_line_dict["pool_id"]   
    
    pools[pool_id] = {} 
    POOL_NAME_MAP[pool_id] = ""
    HEADS[pool_id] = "0x0000000000000000000000000000000000000000"
    new_spec["pools"] = pools
    
    res, err = digi.util.patch_spec("digi.dev", "v1", "lakes", "lake", "default", new_spec)
    
def parse_commit(data_line):
    data_line_dict  = dict_from_data_line(data_line)
    pool_id = data_line_dict["pool_id"] 
    commit_id = data_line_dict["commit_id"]    
    HEADS[pool_id] = commit_id
            
PARSE_FUNCTION_MAP = {
    "pool-new" : parse_new_pool,
    "pool-delete" : parse_delete_pool,
    "pool-commit" : parse_commit,
    "branch-commit" : parse_commit
}

@digi.on.model("pools")
def h(pools):
    digi.logger.info(pools)
    
def dicts_from_pool_query(dict_line):
    dict_line_str = str(dict_line)
    dicts = []
    lines = dict_line_str.split("(=pools.Config)")
    for line in lines[:-1]: #there will be a \n at the end
        if line:
            curr_dict = dict_from_data_line(line)
            dicts.append(curr_dict)
            #digi.logger.info(f"Parsing Dict from line {line}")
            #digi.logger.info(curr_dict)
    return dicts

def make_branch_query(pool_name):
    headers = {
        "Accept": "application/x-zson",
        "Content-Type": "application/json",
    }

    branches_query_json_data = { "query": f"from {pool_name}:branches | yield branch.name" }
    branches_query_response = requests.post(f"{ZED_LAKE_URL}/query", headers=headers, json=branches_query_json_data)
    
    branches = str(branches_query_response.content).split("\\n")
    branches = branches[:-1] #to avoid a trailing quotation mark
    for i in range(len(branches)):
        first_quote_index = branches[i].index("\"")
        last_quote_index = branches[i].rindex("\"")
        branches[i] = branches[i][first_quote_index + 1 : last_quote_index]
    #digi.logger.info(f"BRANCHES: {branches}")
    return branches

def get_branch_count_sum(pool_name, branches):
    count = 0
    
    headers = {
        "Accept": "application/x-zson",
        "Content-Type": "application/json",
    }

    for branch in branches:
        count_query_json_data = { "query": f"from {pool_name}@{branch} | count()" }
        count_query_response = requests.post(f"{ZED_LAKE_URL}/query", headers=headers, json=count_query_json_data)
        
        try:
            count_response_str = str(count_query_response.content)
            #digi.logger.info(count_response_str)
            start_index = count_response_str.index(":")
            end_index = count_response_str.index("(uint64)")
            count_response_str = count_response_str[start_index + 1 : end_index]
            count += int(count_response_str)
        except:
            count += 0
    
    #digi.logger.info(f"found count: {count}")
    return count
    
def check_attr_gen_patch_spec(new_spec):
    new_spec_pools = new_spec.get("pools", {})
    while True:
        curr_spec, _, start_gen = digi.util.get_spec("digi.dev", "v1", "lakes", "lake", "default")
        curr_pools = curr_spec.get("pools", {})
        
        keys_to_remove = []
        for k in new_spec_pools.keys():
            if k not in curr_pools: #get rid of keys that don't exist in the current spec
                keys_to_remove.append(k)
        
        for pop_key in keys_to_remove:
            new_spec_pools.pop(pop_key)
                
        _, rv, curr_gen = digi.util.get_spec("digi.dev", "v1", "lakes", "lake", "default")
        if start_gen < curr_gen:
            continue
        else:        
            res, err = digi.util.patch_spec("digi.dev", "v1", "lakes", "lake", "default", new_spec, rv=rv)
            return
        

def poll_func():
    Timer(POLL_INTERVAL_SECONDS, poll_func).start()
    digi.logger.info("size")
    
    new_spec = {"pools" : {}}
    
    #run :pools query to get name mapping and timestamps (and write timestamps/heads to API server)
    headers = {
        "Accept": "application/x-zson",
        "Content-Type": "application/json",
    }

    pools_query_json_data = {
        "query": "from :pools",
    }

    pools_query_response = requests.post(f"{ZED_LAKE_URL}/query", headers=headers, json=pools_query_json_data)
    
    #digi.logger.info(f"RESPONSE: {pools_query_response.content}")
    pool_dicts = dicts_from_pool_query(pools_query_response.content)
    for pool_dict in pool_dicts:
        ts, name, pool_id = pool_dict["ts"], pool_dict["name"], pool_dict["id"]
        
        #update POOL_NAME_MAP
        POOL_NAME_MAP[pool_id] = name
    
        #run count() on each pool branch to get numbers of records
        #get branch names
        curr_branches = make_branch_query(name)
        pool_count = get_branch_count_sum(name, curr_branches)
        
        #add count, HEADS, and timestamp to new spec
        pool_id_clean = pool_id[:pool_id.index("(")] #gets rid of trailing (=ksuid.KSUID)
        new_spec["pools"][pool_id_clean] = {"head": HEADS[pool_id_clean], "last_updated" : ts, "size": pool_count} #race on HEADS with event thread?
    
    #patch spec
    check_attr_gen_patch_spec(new_spec)
    
def event_func():
    digi.logger.info("events")
    s = requests.Session()
    with s.get(f"{ZED_LAKE_URL}/events", headers=None, stream=True) as resp:
        parse_line = False
        
        for line in resp.iter_lines():
            if line:
                digi.logger.info(line)
                if parse_line:
                    if event_parse_func:
                        #digi.logger.info(f"LINE: {str(line)}")
                        event_parse_func(line)
                    parse_line = False  
                else:
                    #digi.logger.info(f"LINE: {str(line)}")
                    line_str = str(line)
                    event_type = line_str[line_str.index(":") + 2:-1]
                    event_parse_func = PARSE_FUNCTION_MAP.get(event_type, None)
                    
                    #digi.logger.info(f"parsing {event_type} from line {line_str}")
                    parse_line = True  
                    continue

@digi.on.model             
def start_processes():
    if len(SPAWNED_THREADS) < 2:
        digi.logger.info("spawning")
        poll_thread = Thread(target=poll_func)
        event_thread = Thread(target=event_func)
        SPAWNED_THREADS.append(poll_thread)
        SPAWNED_THREADS.append(event_thread)
        poll_thread.start()
        event_thread.start()

if __name__ == '__main__':
    try:
        subprocess.check_call("zed serve -lake /mnt/lake >/dev/null 2>&1 &",
                              shell=True)
    except subprocess.CalledProcessError:
        digi.logger.fatal("unable to start zed lake")
        sys.exit(1)

    digi.logger.info("started zed lake")
    digi.run()
    