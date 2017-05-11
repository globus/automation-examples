#!/usr/bin/env python

import globus_sdk
from globus_sdk import (NativeAppAuthClient, TransferClient,
                        AccessTokenAuthorizer)
from datetime import datetime
from datetime import tzinfo
from datetime import timedelta
from os.path import commonprefix, dirname

# you must have a client ID
CLIENT_ID = '4e6db83a-c767-4e53-ac96-d89b2cbe6577'
# the secret, loaded from wherever you store it
CLIENT_SECRET = 'MWhHZgWo+Z2u2hLB1808dos3qDKw5Q4W3cFhRMTqHYs='
SCOPES = ('openid email profile '
          'urn:globus:auth:scope:transfer.api.globus.org:all')
SOURCE_ENDPOINT_ID = '8ce232ee-35b5-11e7-bcd1-22000b9a448b'


def do_client_authentication(client_id, client_secret,
                             requested_scopes=None):
    """
    Does a client authentication and returns a
    globus transfer token.
    """
    # return a set of tokens, organized by resource server name
    client = globus_sdk.ConfidentialAppAuthClient(CLIENT_ID, CLIENT_SECRET)
    token_response = client.oauth2_client_credentials_tokens()

    # the useful values that you want at the end of this
    globus_auth_data = token_response.by_resource_server['auth.globus.org']
    globus_transfer_data = token_response.by_resource_server['transfer.api.globus.org']
    globus_auth_token = globus_auth_data['access_token']
    globus_transfer_token = globus_transfer_data['access_token']

    return globus_transfer_token


def main():
    # start the Native App authentication process

    current_time = datetime.utcnow().replace(microsecond=0).isoformat()
    last_cleanup_time = datetime.utcnow().replace(microsecond=0) - timedelta(hours=24)
    last_cleanup = last_cleanup_time.isoformat()
    completion_range = last_cleanup+","+current_time
    print completion_range

    transfer_token = do_client_authentication(CLIENT_ID, CLIENT_SECRET)

    authorizer = AccessTokenAuthorizer(access_token=transfer_token)
    tc = TransferClient(authorizer=authorizer)

    # print out a directory listing from an endpoint
    tc.endpoint_autoactivate(SOURCE_ENDPOINT_ID)

    try:
        tasklist = tc.endpoint_manager_task_list(filter_status="SUCCEEDED", filter_endpoint=SOURCE_ENDPOINT_ID, filter_completion_time=completion_range, fields="task_id,source_endpoint,destination_endpoint,source_host_path,owner_string,source_endpoint_id,type")
        print tasklist
    except:
        print "Couldn't get tasklist"

    for task in tasklist:
        if (task["type"] == "TRANSFER"):
            if (task["source_endpoint_id"] == SOURCE_ENDPOINT_ID):
                successful_task=tc.endpoint_manager_task_successful_transfers(task["task_id"])
                print("Task({}): {} -> {}\n was submitted by {}\n{}".  format(task["task_id"], task["source_endpoint"],task["destination_endpoint"], task["owner_string"],task["source_endpoint_id"]))
                print( "task id is {}",task["task_id"])

                files_list = [globr["source_path"] for globr in successful_task]
                print "files list is {}".format(files_list)

                #Find the common directory under which all the files live
                #If one exists, it will be deleted recursively, even if not all
                #files under it were transferred.
                #If there is no common directory, each file that was transferred will be deleted
                commondir=dirname(commonprefix(files_list))
                try:
                    files_on_endpoint = tc.operation_ls(SOURCE_ENDPOINT_ID, path=commondir)
                except globus_sdk.exc.TransferAPIError:
                    print "Directory {} no longer present on source endpoint".format(commondir)
                    continue

                if files_list:
                    if commondir:    
                        ddata=globus_sdk.DeleteData(tc, SOURCE_ENDPOINT_ID, label="deletion of {}".format(task["task_id"]), submission_id=None, recursive=True, deadline=None)
                        ddata.add_item(commondir)
                    else:
                        ddata=globus_sdk.DeleteData(tc, SOURCE_ENDPOINT_ID, label="deletion of {}".format(task["task_id"]), submission_id=None, recursive=False, deadline=None)
# If any of the paths are directories, recursive must be set True on the top level DeleteData
                        for path in files_list:
                            ddata.add_item(path)
                    print ddata
                    delete_result = tc.submit_delete(ddata)
                    print delete_result

                    try:
                        acl_list=tc.endpoint_manager_acl_list(SOURCE_ENDPOINT_ID)
                    except:
                        print "Couldn't get acl list for endpoint {}".format(SOURCE_ENDPOINT_ID)
                        continue
                    print acl_list

                    acldict = {i["path"]:i["id"] for i in acl_list}

                    aclid=""

                    if acldict[commondir+"/"]:
                        aclid=acldict[commondir+"/"]
                        print aclid

                    if aclid:
                        try:
                            tc.delete_endpoint_acl_rule(SOURCE_ENDPOINT_ID, aclid)
                        except:
                            print "Couldn't delete acl rule {}".format(aclid)

if __name__ == '__main__':
    main()
