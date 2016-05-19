#!/usr/bin/env python

import logging
import json
import os
import urllib.request
import extlibs.bottle as bottle
import extlibs.vapyr as vapyr

import settings
import gitlab.v3


def is_good_cr(some_cr):
    if some_cr == "#STRY10":
        return True
    return False

def parse_commit_message(commit_msg):

    errors = []

    snowTokens = []
    for word in commit_msg.split():
        if word.startswith('#'):
            snowTokens.append(word)
    if len(snowTokens) <= 0:
        errors.append("No issues were mentioned.")
    for story in snowTokens:
        if not is_good_cr(story):
            errors.append("Invalid issue: %s" % (commit_msg))
    return errors

def main():
    app = bottle.Bottle()
    logging.basicConfig(format=settings.log_format)
    logging.getLogger().setLevel(getattr(logging, settings.log_level.upper()))

    root_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'static')

    @app.hook('after_request')
    def enable_cors():
        """ You need to add some headers to each request.

        Don't use the wildcard '*' for Access-Control-Allow-Origin in production.
        """
        bottle.response.headers['Access-Control-Allow-Origin'] = '*'
        bottle.response.headers['Access-Control-Allow-Methods'] = \
            'PUT, GET, POST, DELETE, OPTIONS'
        bottle.response.headers['Access-Control-Allow-Headers'] = \
            'Origin, Accept, Content-Type, X-Requested-With, X-CSRF-Token'

    @app.route('/<filename:re:.*\.(css|js|jpg|png|gif|ico|ttf|eot|woff|woff2|svg|jsr|html)>')
    def static_files(filename):
        return bottle.static_file(filename, root=root_dir)

    @app.route('/serviceNow', method=['POST'])
    def serviceNow():
        request = bottle.request.body.read().decode(settings.default_encoding)

        try:
            json_obj = json.loads(request)
        except json.decoder.JSONDecodeError:
            return bottle.abort(400, \
                "I'm unable to parse the JSON string sent: %s" % (request))

        if not json_obj["object_kind"] == 'merge_request':
            logging.error("Only 'merge_request' notifications supported. Got (%s)" % (json_obj["object_kind"]))
            return ''

        commit_list = []
        errors = {}
        project_id = json_obj["object_attributes"]["target_project_id"]
        merge_request_id = json_obj["object_attributes"]["iid"]

        client = vapyr.Client(settings.private_token)
        api = gitlab.v3.API(client, settings.gitlab_host)
        # This is translated underneath as /projects/:id/merge_requests/:id/commits
        merge_request = api.projects[project_id].merge_requests[merge_request_id]
        commit_list = merge_request.commits.values()

        for commit in commit_list:
            author = commit["author_name"]
            if author in settings.ignored_authors:
                continue
            e = parse_commit_message(commit["message"])
            if len(e) > 0:
                errors[commit["id"]] = e

        # If there are any errors, we will leave a note stating what exactly
        # happened, how to solve it and close the merge request.
        if len(errors) > 0:

            body = []
            for k, v in errors.items():
                body.append("sha: (%s) %s" % (k, "\n\n - ".join(v)))

            note_data = {
                'id': project_id,
                'merge_request_id': merge_request_id,
                'body': '\n\n'.join(body),
            }
            merge_request.notes.post(note_data)

            mr_data = {
                'id': project_id,
                'merge_request_id': merge_request_id,
                'state_event': 'close',
            }
            merge_request.put(mr_data)

            logging.warning("Merge Request ID (%s) had errors: %s" % (merge_request_id, body))

        return ''

    bottle.run(app, host=settings.web_address, port=settings.web_port, debug=True)


if __name__ == '__main__':
    main()
