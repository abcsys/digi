import sys
import yaml
import os

def edit_yaml(args):
    workdir, dirname, name = args[2], args[3], args[4]
    yaml_path = f"{workdir}/{dirname}/temp.yaml"

    with open(yaml_path, "r") as rf:
        res = yaml.load(rf, yaml.FullLoader)
        res["metadata"]["name"] = name
    rf.close()

    with open(yaml_path, "w") as wf:
        res = yaml.dump(res, wf)
    wf.close()

#The functions below deal with loading branches      
def run_load(path_to_zson, zson_file_name, new_digi_name):
    branch_name = zson_file_name[:-5]
    os.system(f"zed branch -use {new_digi_name}@main {branch_name}")
    cmd_string = f"digi lake load {new_digi_name}@{branch_name} {path_to_zson}"
    os.system(cmd_string)

def load_lake_branches(args):
    workdir, dirname, name = args[2], args[3], args[4]
    records_path = f"{workdir}/{dirname}/records"
    
    for member in os.listdir(records_path):
        curr_path = f"{records_path}/{member}"
        if os.path.isfile(curr_path) and len(member) >= 5 and member[-5:] == ".zson":
            run_load(curr_path, member, name)

#The functions below deal with saving branches      
def run_query(digi_name, branch_name, snapshot_dir_name):
    file_name = f"{branch_name}.zson"
    cmd_string = f"digi query {digi_name}@{branch_name} > {file_name}"
    
    os.system(cmd_string)
    os.system(f"mv {file_name} {snapshot_dir_name}/records")

def save_lake_branches(args):
    snapshot_dir_name, name = args[2], args[3]
    yaml_path = f"{snapshot_dir_name}/curr_branches.yaml"
    
    branches = ["main", "model"]

    with open(yaml_path, "r") as rf:
        res = yaml.load(rf, yaml.FullLoader)
        spec = res.get("spec")
        
        if spec is not None:
            egress = spec.get("egress")
            if egress is not None:
                for e in egress.keys():
                    branches.append(e)
    rf.close()
    
    #run query commands and store results in zson files
    for branch in branches:
        run_query(name, branch, snapshot_dir_name)

if __name__ == '__main__':
    if (len(sys.argv) > 2):
        if sys.argv[1] == "edit":
            edit_yaml(sys.argv)
        elif sys.argv[1] == "save":
            save_lake_branches(sys.argv)
        elif sys.argv[1] == "load":
            load_lake_branches(sys.argv)
        else:
            print("args[1] did not match any known function")
    else:
        print("Not enough arguments")
