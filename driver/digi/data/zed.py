import json
import getpass
import urllib
import zed
from . import zjson


class Client(zed.Client):
    """TBD patch upstream"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def load(self, pool_name_or_id, data, branch_name='main',
             commit_author=getpass.getuser(), commit_body='', meta=''):
        pool = urllib.parse.quote(pool_name_or_id)
        branch = urllib.parse.quote(branch_name)
        url = self.base_url + '/pool/' + pool + '/branch/' + branch
        commit_message = {'author': commit_author, 'body': commit_body, 'meta': meta}
        headers = {'Zed-Commit': json.dumps(commit_message)}
        r = self.session.post(url, headers=headers, data=data)
        self.__raise_for_status(r)

    def create_branch(self, pool, name, *,
                      commit=f"0x{'0' * 40}"):
        r = self.session.post(self.base_url + f"/pool/{pool}",
                              json={
                                  "name": name,
                                  "commit": commit,
                              })
        self.__raise_for_status(r)

    def branch_exist(self, pool, name):
        records = self.query(f"from {pool}:branches")
        return name in set(r["branch"]["name"] for r in records)

    def query(self, query):
        return zjson.decode_raw(self.query_raw(query))
