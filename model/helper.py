import sys
import yaml
import os
import json
from digi import util
import hashlib

zed_headers = {
    'Accept': 'application/json',
}


def does_branch_exist(digi_name, branch_name):
    response = os.popen(
        f"curl -s -X GET -H 'Accept: application/json' http://localhost:9867/pool/{digi_name}/branch/{branch_name}").read()
    response_json = json.loads(response)
    return "commit" in response_json.keys()


# The functions below deal with loading branches
def run_load(path_to_zson, zson_file_name, new_digi_name):
    branch_name = zson_file_name[:-5]
    os.system(f"zed branch -use {new_digi_name}@main {branch_name} >/dev/null 2>&1")
    cmd_string = f"digi lake load {new_digi_name}@{branch_name} {path_to_zson} >/dev/null 2>&1"
    os.system(cmd_string)


def load_lake_branches(args):
    workdir, dirname, name = args[2], args[3], args[4]
    records_path = f"{workdir}/{dirname}/records"

    for member in os.listdir(records_path):
        curr_path = f"{records_path}/{member}"
        if os.path.isfile(curr_path) and len(member) >= 5 and member[-5:] == ".zson":
            run_load(curr_path, member, name)


# The functions below deal with saving branches
def run_query(digi_name, branch_name, snapshot_dir_name):
    file_name = f"{branch_name}.zson"
    cmd_string = f"digi query {digi_name}@{branch_name} > {file_name}"

    os.system(cmd_string)
    os.system(f"mv {file_name} {snapshot_dir_name}/records")


def save_lake_branches(args):
    snapshot_dir_name, name = args[2], args[3]
    yaml_path = f"{snapshot_dir_name}/spec.yaml"

    branches = ["main", "model"]

    if (not does_branch_exist(name, "model")):
        branches.remove("model");

    with open(yaml_path, "r") as rf:
        spec = yaml.load(rf, yaml.FullLoader)
        if spec is not None:
            egress = spec.get("egress")
            if egress is not None:
                for e in egress.keys():
                    if does_branch_exist(name, e):
                        branches.append(e)
    rf.close()

    # run query commands and store results in zson files
    for branch in branches:
        run_query(name, branch, snapshot_dir_name)


# This function makes hierarchical commits possible
def get_namespace(yaml_dict):
    return "default"


def get_child_digi_name(key, namespace):
    return key[len(namespace) + 1:]


def check_hierachical_commit(args):
    snapshot_dir_name, name, curr_target, gen, addpath = args[2], args[3], args[4], args[5], args[6]
    yaml_path = f"{snapshot_dir_name}/spec.yaml"
    children = []

    with open(yaml_path, "r") as rf:
        spec = yaml.load(rf, yaml.FullLoader)

        if spec is not None:
            namespace = get_namespace(spec)
            mount = spec.get("mount")

            if mount is not None:
                for child_group in mount.keys():
                    child_group_dict = mount.get(child_group)
                    for child in child_group_dict.keys():
                        children.append(get_child_digi_name(child, namespace))

    new_target_dir = f"{curr_target}/{name}_snapshot_gen{gen}/children"
    relevant_path_info = addpath[1:-1]
    for child in children:
        if len(relevant_path_info) > 0:
            os.system(f"digi commit {child} -t {new_target_dir} -p {addpath[1:-1]}")
        else:
            os.system(f"digi commit {child} -t {new_target_dir}")


# This function renames a snapshot directory to use the generation
def get_generation(args):
    g, v, ns, n, r = args[2], args[3], args[4], args[5], args[6]
    res = util.get_spec(g, v, r, n, ns)
    if res is None:
        print("Error")
    else:
        print(res[2])


# This function removes mounts
def remove_mount(args):
    workdir, dirname, name = args[2], args[3], args[4]
    yaml_path = f"{workdir}/{dirname}/temp_spec.yaml"

    with open(yaml_path, "r") as rf:
        spec = yaml.load(rf, yaml.FullLoader)
        if spec is not None:
            if "mount" in spec.keys():
                spec.pop("mount")
    rf.close()

    with open(yaml_path, "w") as wf:
        yaml.dump(spec, wf)
    wf.close()
    return


# This function enables hierarchical recreation
def check_hierarchical_recreate(args):
    workdir, dirname, suffix, parent_name = args[2], args[3], args[4], args[5]
    children_path = f"{workdir}/{dirname}/children"

    if os.path.isdir(children_path):
        for item in os.scandir(children_path):
            if item.is_dir():
                basename = os.path.basename(item.path)

                if suffix != "[]":
                    child_digi_name = f"{basename[:basename.index('_')]}{suffix}"
                    run_cmd = f"digi run {dirname}/children/{basename} {child_digi_name} -c {suffix}"
                else:
                    child_digi_name = f"{basename[:basename.index('_')]}"
                    run_cmd = f"digi run {dirname}/children/{basename} {child_digi_name}"
                os.system(run_cmd)
                mount_cmd = f"digi space mount {child_digi_name} {parent_name}"
                os.system(mount_cmd)
    return


def make_spec(args):
    g, v, ns, n, r, snapshot_dir = args[2], args[3], args[4], args[5], args[6], args[7]
    res = util.get_spec(g, v, r, n, ns)
    if res is None:
        print("Error")
    else:
        yaml_path = f"{snapshot_dir}/spec.yaml"
        spec_dict = res[0]
        with open(yaml_path, "w") as wf:
            yaml.dump(spec_dict, wf)
        wf.close()
    return


def apply_spec(args):
    g, v, ns, n, r, spec_path = args[2], args[3], args[4], args[5], args[6], args[7]
    with open(spec_path, "r") as rf:
        spec = yaml.load(rf, yaml.FullLoader)
        if spec is not None:
            util.patch_spec(g, v, r, n, ns, spec)
    rf.close()


def get_group_kind(yaml_path):
    found_group, found_kind = "", ""
    with open(yaml_path, "r") as rf:
        model = yaml.load(rf, yaml.FullLoader)
        if model is not None:
            found_group = model.get("group", "")
            found_kind = model.get("kind", "")
    rf.close()
    return found_group, found_kind


def find_kind(args):
    kind, group, name, workdir, targetdir, gen, addpaths = args[2], args[3], args[4], args[5], args[6], args[7], args[8]
    relevant_paths = addpaths[1:-1]
    path_list = relevant_paths.split(",")
    path_list.append(".")

    for add_path in path_list:  # look through supplied additional paths
        curr_path = f"{workdir}/{add_path}"
        if os.path.isdir(curr_path):
            for item in os.scandir(curr_path):
                yaml_path = f"{item.path}/model.yaml"
                if os.path.exists(yaml_path):
                    found_group, found_kind = get_group_kind(yaml_path)
                    if found_group.lower() == group.lower() and found_kind.lower() == kind.lower():
                        cmd_string = f"cp -r {item.path} {workdir}/{targetdir}/{name}_snapshot_gen{gen}"
                        os.system(cmd_string)
                        return
    sys.exit(f"No Kind Found")


# The below function computes a checksum over a digi hierarchy
def hier_checksum_digi(args):
    g, v, ns, n, r = args[2], args[3], args[4], args[5], args[6]
    spec = util.get_spec(g, v, r, n, ns)
    hash_list = []
    m = hashlib.sha256()

    if spec is None:
        print("Error")
    else:
        spec_dict = list(spec)[0]
        mount = spec_dict.pop("mount", {})
        spec_dict_bytes = json.dumps(spec_dict).encode('utf-8')
        m.update(spec_dict_bytes)

        if mount is not None:
            for child_group in mount.keys():
                child_group_dict = mount.get(child_group)
                for child in child_group_dict.keys():
                    child_hash = os.popen(f"digi digest {get_child_digi_name(child, get_namespace(None))}").read()
                    hash_list.append(child_hash)

    for child_hash in sorted(hash_list):
        m.update(child_hash.encode('utf-8'))
    print(m.hexdigest())


def hier_checksum_snapshot(args):
    workdir, dirname = args[2], args[3]
    yaml_path = f"{workdir}/{dirname}/spec.yaml"
    m = hashlib.sha256()
    hash_list = []

    with open(yaml_path, "r") as rf:
        spec_dict = yaml.load(rf, yaml.FullLoader)

        if spec_dict is None:
            print("Error")
        else:
            mount = spec_dict.pop("mount", {})
            spec_dict_bytes = json.dumps(spec_dict).encode('utf-8')
            m.update(spec_dict_bytes)

            children_path = f"{workdir}/{dirname}/children"
            if os.path.exists(children_path):
                for item in os.scandir(children_path):
                    if os.path.isdir(item.path):
                        child_hash = os.popen(f"digi digest {dirname}/children/{os.path.basename(item.path)}").read()
                        hash_list.append(child_hash)
    rf.close()

    for child_hash in sorted(hash_list):
        m.update(child_hash.encode('utf-8'))
    print(m.hexdigest())


if __name__ == '__main__':
    # TBD simplify external callers to be "commit" and "recreate"
    #   and remove the intermediate methods
    if (len(sys.argv) > 2):
        if sys.argv[1] == "save-branches":
            save_lake_branches(sys.argv)
        elif sys.argv[1] == "load-branches":
            load_lake_branches(sys.argv)
        elif sys.argv[1] == "comm-hier":
            check_hierachical_commit(sys.argv)
        elif sys.argv[1] == "rec-hier":
            check_hierarchical_recreate(sys.argv)
        elif sys.argv[1] == "generation":
            get_generation(sys.argv)
        elif sys.argv[1] == "remove-mount":
            remove_mount(sys.argv)
        elif sys.argv[1] == "make-spec":
            make_spec(sys.argv)
        elif sys.argv[1] == "apply-spec":
            apply_spec(sys.argv)
        elif sys.argv[1] == "find-kind":
            find_kind(sys.argv)
        elif sys.argv[1] == "checksum-digi":
            hier_checksum_digi(sys.argv)
        elif sys.argv[1] == "checksum-snapshot":
            hier_checksum_snapshot(sys.argv)
        else:
            print(f"args[1]: {sys.argv[1]} did not match any known function")
    else:
        print("Not enough arguments")
