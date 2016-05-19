#!/usr/bin/env python

import logging
import extlibs.vapyr

class API(extlibs.vapyr.Resource):
    def __init__(self, client, parent=None, attrs=None):
        super().__init__(client, parent, attrs)
        self.endpoint += '/api/v3'
        self.resources = {
            'projects': Project,
        }

class Project(extlibs.vapyr.Resource):
    def __init__(self, client, parent, attrs):
        super().__init__(client, parent, attrs)
        self.endpoint += '/projects/' + str(attrs['id'])
        self.resources = {
            'merge_requests': MergeRequest,
        }

class MergeRequest(extlibs.vapyr.Resource):
    def __init__(self, client, parent, attrs):
        super().__init__(client, parent, attrs)
        self.endpoint += '/merge_requests/' + str(attrs['id'])
        self.resources = {
            'commits': Commit,
            'notes': Note,
        }

class Commit(extlibs.vapyr.Resource):
    def __init__(self, client, parent, attrs):
        super().__init__(client, parent, attrs)
        self.endpoint += '/commits/' + str(attrs['id'])

class Note(extlibs.vapyr.Resource):
    def __init__(self, client, parent, attrs):
        super().__init__(client, parent, attrs)
        self.endpoint += '/notes/' + str(attrs['id'])


if __name__ == '__main__':
    # Example usage
    client = extlibs.vapyr.Client('oB1H1R2jmcyNi4zGFzsJ')
    root = extlibs.vapyr.API(client, 'http://ubuntu')
    for k, v in root.projects[1].merge_requests[11].commits.items():
        print(k, v)
    root.projects[1].merge_requests[11].notes.put({'x': 'some update'})
