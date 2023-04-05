import digi
from flask import Flask, request
import logging
import yaml

app = Flask(__name__)
app.logger.setLevel(logging.INFO)

registry = {}

def find_url(user, dspace):
    if user not in registry:
        return None
    if dspace not in registry[user]:
        return None
    if "url" not in registry[user][dspace]:
        return None
    return registry[user][dspace]["url"]

#ASSUMES USER AND DSPACE EXIST -- find sources with given location, kind, and egress
def find_sources(user, dspace, kind_name, branch):
    any_kind = (kind_name == "any")
    if "digis" not in registry[user][dspace]:
        return []
    sources = []
    for digi_name in registry[user][dspace]["digis"]:
        curr_digi_dict = registry[user][dspace]["digis"][digi_name]
        if "egress" in curr_digi_dict and "kind" in curr_digi_dict:
            if branch in curr_digi_dict["egress"] and (any_kind or (curr_digi_dict["kind"] == kind_name)):
                sources.append(f"{digi_name}@{branch}")
    return sources

def find_digi_source(user, dspace, digi_name, branch):
    if "digis" not in registry[user][dspace]:
        return []
    if digi_name in registry[user][dspace]["digis"]:
        curr_digi_dict = registry[user][dspace]["digis"][digi_name]
        if "egress" in curr_digi_dict and branch in curr_digi_dict["egress"]:
            return [f"{digi_name}@{branch}"]
    else:
        return []
        
def resolve_source(source_quantifier):
    valid_quantifier = True
    try:
        user, dspace, digi_info = source_quantifier.split('/')
    except:
        valid_quantifier = False
    finally:
        if not valid_quantifier:
            return None, [], "Bad Source Quantifier"
        
        #find url
        source_lake_url = find_url(user, dspace)
        if not source_lake_url:
            return source_lake_url, [], f"No lake found for {user}/{dspace}"
        
        #get digi info
        if '@' not in digi_info:
            return source_lake_url, [], "Bad pool@branch"
        
        kind, branch = digi_info.split('@')
        
        if "kind:" not in kind: #assume kind refers to a digi name
            return source_lake_url, find_digi_source(user, dspace, kind, branch), None
        
        kind_name = kind[len("kind:"):]
        sources = find_sources(user, dspace, kind_name, branch)
        return source_lake_url, sources, None

@app.route("/resolve", methods=["GET", "POST"])
def resolve():
    request_json = request.get_json(silent=True)
    response = {"source_lake_url": None, 
                "sources": [], 
                "success": False}

    if not request_json:
        return response
    
    source_quantifier = request_json["source_quantifier"]
    source_lake_url, sources, resolve_err = resolve_source(source_quantifier) 
    response["source_lake_url"] = source_lake_url
    response["sources"] = sources
    
    if resolve_err:
        app.logger.info(f"Encountered resolution error {resolve_err} for source quantifier {source_quantifier}")
        return response
    
    response["success"] = True
    return response

@digi.on.model
def h(model):
    app.logger.info(model)

if __name__ == '__main__':
    curr_spec, _, _ = digi.util.get_spec(digi.g, digi.v, digi.r, digi.n, digi.ns)
    if "meta" in curr_spec and "registry" in curr_spec["meta"]:
        registry = yaml.safe_load(curr_spec["meta"]["registry"])
    app.logger.info(registry)
    app.run(host="0.0.0.0", port=7534)
    digi.run()

