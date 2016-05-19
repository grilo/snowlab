#!/usr/bin/env python

import logging
import urllib.request
import json


class Client:

    def __init__(self, api_token, default_encoding="utf-8"):
        self.api_token = api_token 
        self.default_encoding = default_encoding

    def request(self, url, method='GET', data=None):
        req_url = url + "?private_token=%s" % (self.api_token)
        logging.debug("(%s) %s" % (method, url))
        logging.debug("Data: %s" % data)
        print(req_url)
        req = urllib.request.Request(req_url, data=json.dumps(data).encode(self.default_encoding), method=method, headers={'content-type': 'application/json'})
        with urllib.request.urlopen(req) as f:
            return json.loads(f.read().decode(self.default_encoding))


# A somewhat ugly hack in the name of syntatic sugar.
# Since running api.projects[project_id].messages returns a DICT and DICTs
# don't support "post" method, we wrap the standard dict class. This allows
# us to write: api.projects[project_id].messages.post({'x': 'new_message'})
# Apart from supporting POST, it behaves exactly like a normal dictionary.
class ResourceContainer(dict):

    def __init__(self, client, endpoint, *args, **kwargs):
        super().__init__(self, *args, **kwargs)
        self.client = client
        self.endpoint = endpoint

    def post(self, data=None):
        return self.client.request(self.endpoint, "POST", data)


class Resource:
    def __init__(self, client, parent='', attrs=None):
        self.client = client
        self.endpoint = parent
        self.attrs = attrs
        self.resources = {}
        self.cache = {}

    def __getattr__(self, name):
        if not name in self.resources.keys():
            raise AttributeError("Resource not implement or unavailable.")

        # If the result isn't cached already, perform the necessary requests
        # and fill the cache up.
        if not name in self.cache.keys():
            self.cache[name] = ResourceContainer(self.client, self.endpoint + '/' + name)
            # Request the generic resource (for example /users) and for each
            # result create an instance of the corresponding resource class
            for i in self.client.request(self.endpoint + '/' + name):
                resource_instance = self.resources[name](self.client, self.endpoint, i)
                # Store the retrieved result. The requirement of that specific
                # resource identifier is currently hardcoded to "id". Perhaps
                # we could make this dynamic in the future.
                self.cache[name][i["id"]] = resource_instance
        return self.cache[name]

    def __getitem__(self, key):
        return self.attrs[key]

    def get(self):
        return self.client.request(args)

    def post(self, data=None):
        raise Exception("See: ResourceContainer")

    def delete(self):
        return self.client.request(self.endpoint, "DELETE")

    def put(self, data=None):
        return self.client.request(self.endpoint, "PUT", data)

    def patch(self, data=None):
        return self.client.request(self.endpoint, "PATCH", data)

    def __str__(self):
        return json.dumps(self.attrs, indent=2)
