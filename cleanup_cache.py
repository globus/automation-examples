#!/usr/bin/env python

"""
Delete data on your shared endpoint if someone has copied it. This script
will wait for a transfer to complete before deleting data. Ensure you have
an app setup on developers.globus.org (See below for instructions).

*WARNING*: This script is greedy in how it deletes folders. If someone
cherry-picks files, it will delete the whole directory!

Confidential App [Client Credentials Grant] on developers.globus.org:
    * "Redirect URLs" -- Set to "https://example.com/oauth_callback/".
    * Scopes:
        [urn:globus:auth:scope:transfer.api.globus.org:all]
        Only transfer is required, since your bot will be using client_secret
        to authenticate. [openid profile] are required if you setup your own
        three-legged-auth server and want to allow users to login to it.
    * Uncheck "Native App".

*Notice*: A confidential app is a bot which acts on your behalf. You will
need to give it access to your shared endpoint.

Want to test with non-critical data first? Copy data from Globus Tutorial
Endpoint 1: http://bit.ly/2rzWx0Z
"""

from __future__ import print_function

import sys
import globus_sdk
from globus_sdk import (TransferClient,
                        AccessTokenAuthorizer)
from globus_sdk.exc import TransferAPIError
from datetime import datetime
from datetime import timedelta
from os.path import commonprefix, dirname

# Must add the client ID as an Access Manager to the
# shared endpoint.

# Client ID from the app you created above
CLIENT_ID = '4e6db83a-c767-4e53-ac96-d89b2cbe6577'
# the secret, loaded from wherever you store it
CLIENT_SECRET = 'MWhHZgWo+Z2u2hLB1808dos3qDKw5Q4W3cFhRMTqHYs='
# Source endpoint. *MUST* be a shared endpoint.
SOURCE_ENDPOINT_ID = '3886dc9c-3eff-11e7-bd15-22000b9a448b'


def do_client_authentication(client_id, client_secret):
    """
    Does a client authentication and returns a globus transfer token.
    """
    client = globus_sdk.ConfidentialAppAuthClient(
        client_id,
        client_secret,
    )
    token_response = client.oauth2_client_credentials_tokens()
    return (token_response.by_resource_server
            ['transfer.api.globus.org']['access_token']
            )


def task_delete_conditions_satisfied(task):
    """Returns True if the task was someone transferring data FROM this
    endpoint, false otherwise."""
    return task["type"] == "TRANSFER" and \
        task["source_endpoint_id"] == SOURCE_ENDPOINT_ID


def select_dir_to_delete(transfer_client, task):
    """Find the common directory under which all the files live. If one exists,
    it will be deleted recursively, even if not all files under it were
    transferred. If there is no common directory, each file that was
    transferred will be deleted"""
    successful_file_transfers = \
        transfer_client.endpoint_manager_task_successful_transfers(
            task["task_id"]
        )
    print("Transfer Task({}): {} -> {}\n was submitted by {}\n".
          format(task["task_id"], task["source_endpoint"],
                 task["destination_endpoint"],
                 task["owner_string"]))

    files_list = [
        globr["source_path"] for globr in successful_file_transfers]
    print("files list is ", files_list)

    common_dir = dirname(commonprefix(files_list))
    return files_list, common_dir


def delete_dir_and_acls(tc, task, files_list, common_dir):
    """Given a task, delete all files and ACLs associated with it. If a
    common directory exists between files, recursively delete that.
    Otherwise, delete each file individually. (See select_dir_to_delete above)

    Aborts deletion if an exception is thrown, either due to insufficient
    read access or if the files don't exist anymore."""
    try:
        tc.operation_ls(SOURCE_ENDPOINT_ID, path=common_dir)
    except globus_sdk.exc.TransferAPIError as tapie:
        if tapie.code == 'ClientError.NotFound':
            print('Directory {} no longer present on source endpoint, '
                  'there is nothing to delete\n'.format(common_dir))
            return
        else:
            print("Could not delete directory '{}': {}".format(
                common_dir, tapie.message)
            )
            return
    if files_list:
        if common_dir:
            ddata = globus_sdk.DeleteData(
                tc, SOURCE_ENDPOINT_ID,
                label="deletion of {}".format(task["task_id"]),
                submission_id=None, recursive=True, deadline=None)
            ddata.add_item(common_dir)
        else:
            ddata = globus_sdk.DeleteData(
                tc, SOURCE_ENDPOINT_ID,
                label="deletion of {}".format(task["task_id"]),
                submission_id=None, recursive=False, deadline=None)
            # If any of the paths are directories, recursive must be set True
            # on the top level DeleteData
            for path in files_list:
                ddata.add_item(path)
        tc.submit_delete(ddata)
        print("Job to delete data has been submitted")

        try:
            acl_list = tc.endpoint_manager_acl_list(SOURCE_ENDPOINT_ID)
        except:
            print("Couldn't get acl list for endpoint ", SOURCE_ENDPOINT_ID)
            return

        acldict = {i["path"]: i["id"] for i in acl_list}

        aclid = ""

        try:
            aclid = acldict[common_dir + "/"]
        except:
            print("No acl found for directory ",
                  common_dir + "/")
            return

        if aclid:
            try:
                tc.delete_endpoint_acl_rule(
                    SOURCE_ENDPOINT_ID, aclid)
            except:
                print("Couldn't delete acl rule ", aclid)
                return
            print("Acl deleted for directory ",
                  common_dir + "/")


def main():

    current_time = datetime.utcnow().replace(microsecond=0).isoformat()
    last_cleanup_time = datetime.utcnow().replace(microsecond=0)\
        - timedelta(hours=24)
    last_cleanup = last_cleanup_time.isoformat()
    completion_range = last_cleanup+","+current_time
    print("Cleaning up source endpoint {} \nfor outbound transfers completed "
          "in range {}\n ".format(SOURCE_ENDPOINT_ID, completion_range))

    transfer_token = do_client_authentication(CLIENT_ID, CLIENT_SECRET)

    authorizer = AccessTokenAuthorizer(access_token=transfer_token)
    tc = TransferClient(authorizer=authorizer)

    # print out a directory listing from an endpoint
    tc.endpoint_autoactivate(SOURCE_ENDPOINT_ID)
    try:
        task_fields = "task_id,source_endpoint,destination_endpoint," \
                      "source_host_path,owner_string,source_endpoint_id,type"
        tasks = tc.endpoint_manager_task_list(
                    filter_status="SUCCEEDED",
                    filter_endpoint=SOURCE_ENDPOINT_ID,
                    filter_completion_time=completion_range,
                    fields=task_fields)
    except TransferAPIError as tapie:
        if tapie.code == 'PermissionDenied':
            print(
                'Permission denied! Give your app permission by going to '
                '"globus.org/app/endpoints/{}/roles", and under '
                '"Identity/E-mail adding "{}@clients.auth.globus.org" as '
                'an "AccessManager" and "Activity Manager"'.format(
                                        SOURCE_ENDPOINT_ID, CLIENT_ID
                            )
                )
            sys.exit(1)
        # Nothing weird *should* happen here, but if so re-raise so the user
        # can deal with it.
        raise
    tasklist = tasks.data
    if not tasklist:
        print("No transfers from {} found in the last 24 hours, "
              "nothing to clean up".format(SOURCE_ENDPOINT_ID))
    else:
        print("{} total transfers found from {} in the last 24 hours, "
              "some may not be of type TRANSFER".format(len(tasklist),
                                                        SOURCE_ENDPOINT_ID))
    delete_tasks = [task.data
                    for task in tasklist
                    if task_delete_conditions_satisfied(task)
                    ]
    for task in delete_tasks:
        files_list, common_dir = select_dir_to_delete(tc, task)

        delete_dir_and_acls(tc, task, files_list, common_dir)


if __name__ == '__main__':
    main()
