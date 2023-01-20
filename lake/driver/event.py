import digi
from threading import Lock

NULL_COMMIT_ID = "0x0000000000000000000000000000000000000000"
HEADS = {}
HEADS_LOCK = Lock()

def dict_from_data_line(data_line):
    """
    This function turns zed outputs into dictionaries for more effective use. 
    
    Zed events output pairs of lines such as:
    
    event: pool-new
    data: {"pool_id": "1sMDXpVwqxm36Rc2vfrmgizc3jz"}
    (Taken from https://zed.brimdata.io/docs/lake/api#events)
        
    This function takes the "data" line or query output, passed in as bytes representing ZSON, and outputs a dictionary.
    """
    data_line_str = str(data_line)
    
    try:
        contents = data_line_str[data_line_str.index("{") : data_line_str.rindex("}") + 1] #previous end was -1
        contents = contents[1:-1]
        
        data_line_dict = {}
        
        pairs = contents.split(",")
        for pair in pairs:
            curr_pair = pair.split(":")
            if curr_pair[1][0] == "\"":
                curr_pair[1] = curr_pair[1][1:-1]
            data_line_dict[curr_pair[0]] = curr_pair[1]
            
        #remove a leading 0x if it exists because pool IDs do not necessarily need to be hexadecimal
        #as shown here: https://zed.brimdata.io/docs/lake/api#events. Additionally, Zed Client queries
        #return pool IDs without the 0x  
        if "pool_id" in data_line_dict:
            pool_id = data_line_dict["pool_id"]
            if pool_id[:2] == "0x": 
                pool_id = pool_id[2:] 
                data_line_dict["pool_id"] = pool_id
                return data_line_dict
    except:
        return None

def parse_delete_pool(data_line):
    spec = digi.model.get()
    new_spec = {}
    
    stats = spec.get("stats", None)
    if stats is not None:
        stats["num_pools"] -= 1
        new_spec["stats"] = stats
    
    pools = spec.get("pools", None)
    if pools is not None:
        data_line_str = str(data_line)
        
        data_line_dict  = dict_from_data_line(data_line)
        
        pool_id = data_line_dict["pool_id"]
        pools[pool_id] = None
        new_spec["pools"] = pools
        
        with HEADS_LOCK:
            if pool_id in HEADS:
                HEADS.pop(pool_id)
            
    digi.model.patch(view_or_path=new_spec)
    
                
def parse_new_pool(data_line):
    spec = digi.model.get()
    new_spec = {}
    
    stats = spec.get("stats", {"num_pools" : 0})
    stats["num_pools"] += 1
    new_spec["stats"] = stats
    
    pools = spec.get("pools", {})
    data_line_str = str(data_line)
    
    data_line_dict  = dict_from_data_line(data_line)
    
    pool_id = data_line_dict["pool_id"]
    
    pools[pool_id] = {}
    with HEADS_LOCK: 
        HEADS[pool_id] = NULL_COMMIT_ID
    new_spec["pools"] = pools
    
    digi.model.patch(view_or_path=new_spec)
    
def parse_commit(data_line):
    data_line_dict  = dict_from_data_line(data_line)
    pool_id = data_line_dict["pool_id"] 
    commit_id = data_line_dict["commit_id"]
    with HEADS_LOCK: 
        HEADS[pool_id] = commit_id
    
PARSE_FUNCTION_MAP = {
    "pool-new" : parse_new_pool,
    "pool-delete" : parse_delete_pool,
    "pool-commit" : parse_commit,
    "branch-commit" : parse_commit
}