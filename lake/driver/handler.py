import sys
import subprocess
import requests
from threading import Timer, Thread
import subprocess
import digi
import pyzed
from event import dict_from_data_line, HEADS, POOL_NAME_MAP, PARSE_FUNCTION_MAP, NULL_COMMIT_ID

ZED_LAKE_URL = "http://localhost:9867"
POLL_INTERVAL_SECONDS = 10.0
SPAWNED_THREADS = []
ZED_CLIENT = pyzed.Client(base_url=ZED_LAKE_URL)

BRANCHES = {}

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
    return dicts

def make_branch_query(pool_name):
    headers = {
        "Accept": "application/x-zson",
        "Content-Type": "application/json",
    }

    #branches_query_json_data = { "query": f"from {pool_name}:branches | yield branch.name" }
    #branches_query_response = requests.post(f"{ZED_LAKE_URL}/query", headers=headers, json=branches_query_json_data)
    
    branches = []
    branch_query_pyzed = ZED_CLIENT.query(f"from {pool_name}:branches | yield branch.name")
    for branch_name in branch_query_pyzed:
        branches.append(branch_name)
    
    #branches = str(branches_query_response.content).split("\\n")
    #branches = branches[:-1] #to avoid a trailing quotation mark
    #for i in range(len(branches)):
    #    first_quote_index = branches[i].index("\"")
    #    last_quote_index = branches[i].rindex("\"")
    #    branches[i] = branches[i][first_quote_index + 1 : last_quote_index]
    return branches

def get_branch_count_sum(pool_name, branches):
    count = 0
    
    headers = {
        "Accept": "application/x-zson",
        "Content-Type": "application/json",
    }

    for branch in branches:
        #count_query_json_data = { "query": f"from {pool_name}@{branch} | count()" }
        #count_query_response = requests.post(f"{ZED_LAKE_URL}/query", headers=headers, json=count_query_json_data)
        
        count_query_pyzed = ZED_CLIENT.query(f"from {pool_name}@{branch} | count()")
        for pool_count in count_query_pyzed:
            count += pool_count["count"]
        
        #try:
        #    count_response_str = str(count_query_response.content)
        #    start_index = count_response_str.index(":")
        #    end_index = count_response_str.index("(uint64)")
        #    count_response_str = count_response_str[start_index + 1 : end_index]
        #    count += int(count_response_str)
        #except:
        #    count += 0
    
    return count
    
def patch_existing_pools(new_spec):
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
    
    new_spec = {"pools" : {}}
    
    #run :pools query to get name mapping and timestamps (and write timestamps/heads to API server)
    headers = {
        "Accept": "application/x-zson",
        "Content-Type": "application/json",
    }

    pools_query_json_data = {
        "query": "from :pools",
    }

    #pools_query_response = requests.post(f"{ZED_LAKE_URL}/query", headers=headers, json=pools_query_json_data)
    
    pool_query_pyzed = ZED_CLIENT.query("from :pools")
    pool_dicts =[]
    for elem in pool_query_pyzed:
        pool_dicts.append(elem)
    
    #pool_dicts = dicts_from_pool_query(pools_query_response.content)
    for pool_dict in pool_dicts:
        ts, name, pool_id = str(pool_dict["ts"]), pool_dict["name"], str(pool_dict["id"].hex())
        
        #update POOL_NAME_MAP
        POOL_NAME_MAP[pool_id] = name
    
        #run count() on each pool branch to get numbers of records
        #get branch names
        curr_branches = make_branch_query(name)
        pool_count = get_branch_count_sum(name, curr_branches)
        
        #add count, HEADS, and timestamp to new spec
        try: #use try-except in case we don't have values for head yet (generated from event parsing)
            new_spec["pools"][pool_id] = {"head": HEADS[pool_id], "last_updated" : ts, "size": pool_count} #race on HEADS with event thread?
        except:
            new_spec["pools"][pool_id] = {"head": NULL_COMMIT_ID, "last_updated" : ts, "size": pool_count}
    
    #patch spec
    patch_existing_pools(new_spec)
    
def event_func():
    s = requests.Session()
    with s.get(f"{ZED_LAKE_URL}/events", headers=None, stream=True) as resp:
        parse_line = False
        
        for line in resp.iter_lines():
            if line:
                if parse_line:
                    if event_parse_func:
                        event_parse_func(line)
                    parse_line = False  
                else:
                    line_str = str(line)
                    event_type = line_str[line_str.index(":") + 2:-1]
                    event_parse_func = PARSE_FUNCTION_MAP.get(event_type, None)
                    
                    parse_line = True  
                    continue

@digi.on.model             
def start_processes():
    if len(SPAWNED_THREADS) < 2:
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
    