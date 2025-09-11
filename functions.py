from CheckLabs import *
from Sentences import *
import ntnx_networking_py_client.models.networking.v4.config 
import ntnx_iam_py_client
import ntnx_networking_py_client
import ntnx_vmm_py_client
import ntnx_prism_py_client
import ntnx_lifecycle_py_client
import ntnx_clustermgmt_py_client
import ntnx_microseg_py_client
import requests
import json
from jsonpath_ng.ext import parse
import time


# ========================================================================
# = configSdkClient
# ========================================================================
def confSDKClient(host, user, password, ssl=False):
    
    # Configure the client
    sdkConfig = ntnx_networking_py_client.Configuration()
    sdkConfig.host = host
    sdkConfig.port = 9440
    sdkConfig.maxRetryAttempts = 3
    sdkConfig.backoffFactor = 3
    sdkConfig.username = user
    sdkConfig.password = password
    sdkConfig.verify_ssl = ssl

    return sdkConfig

# ========================================================================
# = retrieveUserId
# ========================================================================
def retrieveUserId(userName, variables):

    # Configure the client
    sdkConfig = ntnx_networking_py_client.Configuration()
    sdkConfig.host = variables['PC']
    sdkConfig.port = 9440
    sdkConfig.maxRetryAttempts = 3
    sdkConfig.backoffFactor = 3
    sdkConfig.username = variables['PCUser']
    sdkConfig.password = variables['PCPassword']
    sdkConfig.verify_ssl = False

    client = ntnx_iam_py_client.ApiClient(configuration=sdkConfig)
    usersApi = ntnx_iam_py_client.UsersApi(api_client=client)

    response = usersApi.list_users(_filter="username eq '" + str(userName) + "'")
    myData = response.to_dict()

    if myData['data']:
        return myData['data'][0]['ext_id']
    else:
        return None
    
# ========================================================================
# = retrieveRoleId
# ========================================================================
def retrieveRoleId(roleName, variables):

    # Configure the client
    sdkConfig = ntnx_networking_py_client.Configuration()
    sdkConfig.host = variables['PC']
    sdkConfig.port = 9440
    sdkConfig.maxRetryAttempts = 3
    sdkConfig.backoffFactor = 3
    sdkConfig.username = variables['PCUser']
    sdkConfig.password = variables['PCPassword']
    sdkConfig.verify_ssl = False

    client = ntnx_iam_py_client.ApiClient(configuration=sdkConfig)
    roleApi = ntnx_iam_py_client.RolesApi(api_client=client)

    response = roleApi.list_roles(_filter="displayName eq '" + str(roleName) + "'")
    myData = response.to_dict()

    if myData['data']:
        return myData['data'][0]['ext_id']
    else:
        return None
    
# ========================================================================
# = retrieveAuthorizationPolicyId
# ========================================================================
# Function to retrieve the extId of a specific authorization policy
def retrieveAuthorizationPolicyId(policyName, variables):

    # Configure the client
    sdkConfig = ntnx_networking_py_client.Configuration()
    sdkConfig.host = variables['PC']
    sdkConfig.port = 9440
    sdkConfig.maxRetryAttempts = 3
    sdkConfig.backoffFactor = 3
    sdkConfig.username = variables['PCUser']
    sdkConfig.password = variables['PCPassword']
    sdkConfig.verify_ssl = False

    client = ntnx_iam_py_client.ApiClient(configuration=sdkConfig)
    authorizationPoliciesApi = ntnx_iam_py_client.AuthorizationPoliciesApi(api_client=client)

    response = authorizationPoliciesApi.list_authorization_policies(_filter="displayName eq '" + str(policyName) + "'")
    myData = response.to_dict()

    if myData['data']:
        return myData['data'][0]['ext_id']
    else:
        return None
    

# ========================================================================
# = checkAuthorizationPolicyAssignement
# ========================================================================
# Function to check if the assignment is correct
def checkAuthorizationPolicyAssignement(authorizationPolicyId, roleId, userId, variables):

    # Configure the client
    sdkConfig = ntnx_networking_py_client.Configuration()
    sdkConfig.host = variables['PC']
    sdkConfig.port = 9440
    sdkConfig.maxRetryAttempts = 3
    sdkConfig.backoffFactor = 3
    sdkConfig.username = variables['PCUser']
    sdkConfig.password = variables['PCPassword']
    sdkConfig.verify_ssl = False

    client = ntnx_iam_py_client.ApiClient(configuration=sdkConfig)
    authorizationPoliciesApi = ntnx_iam_py_client.AuthorizationPoliciesApi(api_client=client)

    response = authorizationPoliciesApi.get_authorization_policy_by_id(extId=authorizationPolicyId)
    myData = response.to_dict()

    # Check if the correct role is assigned
    if myData['data']['role'] != roleId:
        return False
    
    # Check if the correct user is assigned in any of the identities
    user_assigned = any(identity['_reserved']['user']['uuid']['anyof'][0] == userId for identity in myData['data']['identities'])
    if not user_assigned:
        return False
    
    # If everything is correct, return True
    return True

# ========================================================================
# = retrieveProjectInfo
# ========================================================================
# Function that is returning the extId of a project
def retrieveProjectInfo(projectName, variables):

    url = "https://%s:9440/api/nutanix/v3/projects/list" % variables['PC']
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    payload={
        "kind": "project",
        "length": 100
    }

    response = requests.post(url, json=payload, headers=headers, verify=False, auth=(variables['PCUser'], variables['PCPassword']))
    response_data = response.json()

    if len(response_data['entities']) != 0:
        for project in response_data['entities']:
            if project['status']['name'] == projectName:
                return project
    
    return None


# ========================================================================
# = retrieveSubnetID
# ========================================================================
# Function that is returning the extId of a subnet
def retrieveSubnetID(subnet_name, variables):

    # Configure the client
    sdkConfig = confSDKClient(variables['PC'], variables['PCUser'], variables['PCPassword'])

    client = ntnx_networking_py_client.ApiClient(configuration=sdkConfig)
    subnets_api = ntnx_networking_py_client.SubnetsApi(api_client=client)

    response=subnets_api.list_subnets(_filter="name eq '" + subnet_name + "'")
    myData = response.to_dict()

    # Check if we got an id
    if myData['data']==None or len(myData['data']) != 1:
        return None
        
    # If everything is correct, return True
    return  myData['data'][0]['ext_id']


# ========================================================================
# = checkSubnetAdvanced
# ========================================================================
def checkSubnetAdvanced( subnetID, variables):
    
    # Configure the client
    sdkConfig = confSDKClient(variables['PC'], variables['PCUser'], variables['PCPassword'])

    client = ntnx_networking_py_client.ApiClient(configuration=sdkConfig)
    subnets_api = ntnx_networking_py_client.SubnetsApi(api_client=client)

    response=subnets_api.get_subnet_by_id(subnetID)
    myData = response.to_dict()

    return myData['data']['is_advanced_networking']
    

# ========================================================================
# = retrieveImageID
# ========================================================================
# Function that is returning the extId of an image
# Note : developped in v3 API because Python SDK seems to be broken (list_images URL is not found, 404 error)
# SDK Ref : https://developers.nutanix.com/sdk-reference?namespace=vmm&version=v4.0.b1&language=python
def retrieveImageID(image_name, variables):

    url = "https://%s:9440/api/nutanix/v3/images/list" % variables['PC']
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    payload={
        "kind": "image",
        "length": 100
        }

    response = requests.post(url, json=payload, headers=headers, verify=False, auth=(variables['PCUser'], variables['PCPassword']))
    response_data = response.json()

    for image in response_data['entities']:
        if image['status']['name'] == image_name:
            return image['metadata']['uuid']
        
    return None

# ========================================================================
# = retrieveVMInfo
# ========================================================================
def retrieveVMInfo(vm_name, variables):

    # Configure the client
    sdkConfig = confSDKClient(variables['PC'], variables['PCUser'], variables['PCPassword'])

    client = ntnx_vmm_py_client.ApiClient(configuration=sdkConfig)
    vms_api = ntnx_vmm_py_client.VmApi(api_client=client)

    response=vms_api.list_vms(_filter="name eq '" + vm_name + "'")
    myData = response.to_dict()
    # Check if we got an id
    if myData['data']==None or len(myData['data']) != 1:
        return False, {}
    
    vmUUID=myData['data'][0]['ext_id']
    
    response=vms_api.get_vm_by_id(vmUUID)
    myData=response.to_dict()

    # If everything is correct, return True
    return True, myData['data']

# ========================================================================
# = getVMProjectUUID
# ========================================================================
# GL Todo : write with SDK when available
def getVMProjectUUID(vmuuid, pc, user, password):
    url = "https://%s:9440/api/nutanix/v3/vms/%s"% (pc,vmuuid)
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    response = requests.get(url, headers=headers, verify=False, auth=(user, password))
    response_data = response.json()

    return response_data['metadata']['project_reference']['uuid']

# ========================================================================
# = hasVMCloudinit
# ========================================================================
# GL Todo : write with SDK when available
def hasVMCloudinit(vmuuid, pc, user, password):
    url = "https://%s:9440/api/nutanix/v3/vms/%s"% (pc,vmuuid)
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    response = requests.get(url, headers=headers, verify=False, auth=(user, password))
    response_data = response.json()

    try:
        if response_data['spec']['resources']['guest_customization'] == None:
            return False
    except:
        return False
    
    return True

# ========================================================================
# = retrieveCatID
# ========================================================================
def retrieveCatID( key, value, variables):
    
    sdkConfig = confSDKClient(variables['PC'], variables['PCUser'], variables['PCPassword'])
    page = 0
    limit = 50

    client = ntnx_prism_py_client.ApiClient(configuration=sdkConfig)
    categories_api = ntnx_prism_py_client.CategoriesApi(api_client=client)

    if value == None:
        try:
            api_response = categories_api.list_categories(_page=page, _limit=limit,_filter="key eq '" + key + "'")
            myData=api_response.to_dict()

            if myData['data'] == None:
                return False, None
            else:
                return True, myData['data'][0]['ext_id']

        except ntnx_prism_py_client.rest.ApiException as e:
            print(e)
    else:
        try:
            api_response = categories_api.list_categories(_page=page, _limit=limit,_filter="key eq '" + key + "' and value eq '" + value + "'")
            myData=api_response.to_dict()
            
            if myData['data'] == None:
                return False, None
            else:
                return True, myData['data'][0]['ext_id']

        except ntnx_prism_py_client.rest.ApiException as e:
            print(e)            


# ========================================================================
# = retrieveStoragePolicyID
# ========================================================================
# Function that is returning the extId of a storage policy
# GL Todo : write with SDK when available

def retrieveStoragePolicyID(policy_name, variables):

    url = "https://%s:9440/api/nutanix/v3/storage_policies/list" % variables['PC']
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    payload = {
        "kind": "storage_policy",
        "length": 100
    }

    response = requests.post(url, json=payload, headers=headers, verify=False, auth=(variables['PCUser'], variables['PCPassword']))
    response_data = response.json()

    for policy in response_data['entities']:
        if policy['status']['name'] == policy_name:
            return policy['metadata']['uuid']

    return None

# ========================================================================
# = retrieveFlowServiceID
# ========================================================================
# Function that is returning the extId of a seccurity service
def retrieveFlowServiceID(service_name, variables):
    
    sdkConfig = confSDKClient(variables['PC'], variables['PCUser'], variables['PCPassword'])
    page = 0
    limit = 50

    client = ntnx_microseg_py_client.ApiClient(configuration=sdkConfig)
    service_groups_api = ntnx_microseg_py_client.ServiceGroupsApi(api_client=client)

    try:
        api_response = service_groups_api.list_service_groups(_page=page, _limit=limit, _filter="name eq '" + service_name + "'")
        info = api_response.to_dict()

        return info['data'][0]['ext_id']
    except ntnx_microseg_py_client.rest.ApiException as e:
        print(e)

    return None

# ========================================================================
# = retrieveSecurityPolicyInfo
# ========================================================================
# Function that is returning the extId of a security policy
def retrieveSecurityPolicyInfo(policy_name, variables):

    sdkConfig = confSDKClient(variables['PC'], variables['PCUser'], variables['PCPassword'])
    page = 0
    limit = 50

    client = ntnx_microseg_py_client.ApiClient(configuration=sdkConfig)
    network_security_policies_api = ntnx_microseg_py_client.NetworkSecurityPoliciesApi(api_client=client)

    try:
        api_response = network_security_policies_api.list_network_security_policies(
            _page=page, _limit=limit, _filter="name eq '" + policy_name + "'"
        )

        if not getattr(api_response, "data", None):
            return None

        api_response2 = network_security_policies_api.get_network_security_policy_by_id(
            extId=api_response.data[0].ext_id
        )

    except (ntnx_microseg_py_client.rest.ApiException, AttributeError, IndexError) as e:
        print(e)
        return None

    return api_response2.data.to_dict()

# ========================================================================
# = retrieveProtectionPolicyInfo
# ========================================================================
# Function that is returning the info of a protection policy
def retrieveProtectionPolicyInfo(policy_name, variables):

    url = "https://%s:9440/api/nutanix/v3/protection_rules/list" % variables['PC']
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    payload = {
        "kind": "protection_rule",
        "length": 100
    }

    response = requests.post(url, json=payload, headers=headers, verify=False, auth=(variables['PCUser'], variables['PCPassword']))
    response_data = response.json()

    for policy in response_data['entities']:
        if policy['status']['name'] == policy_name:
            
            # We found the policy, let's return the details
            poluuid=policy['metadata']['uuid']

            url = "https://%s:9440/api/nutanix/v3/protection_rules/%s" % (variables['PC'], poluuid)

            response2 = requests.get(url, json=payload, headers=headers, verify=False, auth=(variables['PCUser'], variables['PCPassword']))

            return response2.json()

    return None

# ========================================================================
# = retrieveApprovalPolicyInfo
# ========================================================================
# Function that is returning the info of a Approval policy
# GL ToDo : write with SDK when available
def retrieveApprovalPolicyInfo( policy_name, variables):
    # IMPORTANT : Due to several issues during labs, with bad names/typoes/etc., and because we can only have
    # one approval policy, we will return the first one if no name is provided

    url = "https://%s:9440/api/security/v4.0.a1/management/approval-policies" % variables['PC']
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    payload = {}

    response = requests.get(url, json=payload, headers=headers, verify=False, auth=(variables['PCUser'], variables['PCPassword']))
    response_data = json.loads(response.text)

    try:
        if len(response_data['data']):
            return response_data['data'][0]
        else:
            return None
    except:
        return None


# ========================================================================
# = retrieveReportInfo
# ========================================================================
# Function that is returning the info of a report
# GL ToDo : write with SDK when available
def retrieveReportInfo( reportName, variables):
    
    url="https://%s:9440/api/nutanix/v3/report_configs/list" % variables['PC']
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    payload = {
        "kind": "report_config",
        "length": 100
    }

    response = requests.post(url, json=payload, headers=headers, verify=False, auth=(variables['PCUser'], variables['PCPassword']))
    response_data = json.loads(response.text)

    for reports in response_data['entities']:
        if reports['status']['name'] == reportName:
            return True, reports
        
    return False, None

# ========================================================================
# = getNumberOfUpdates
# ========================================================================
# This function is returning the number of updates avaialble
# GL ToDo : write with SDK when available (return was not relevent)
def getNumberOfUpdates( variables):
    nbupdates=0
     
    url="https://%s:9440/api/lcm/v4.0.a1/resources/entities" % variables['PC']
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    response = requests.get(url, headers=headers, verify=False, auth=(variables['PCUser'], variables['PCPassword']))
    response_data = json.loads(response.text)

    for elt in response_data['data']:
        if "availableVersions" in elt.keys():
            nbupdates+=1
            
    return nbupdates

# ========================================================================
# = GetNewNodeInfo
# ========================================================================
# This function is returning the info about nodes available for expansion
# ToDo : rewrite with SDK when available (seems broken because of authentication)
def getNewNodeSerial(variables):
    
    clusterUUID=getClusterUUID(variables) 
    
    url="https://%s:9440/api/clustermgmt/v4.0.b2/config/clusters/%s/rackable-units" % (variables['PC'],clusterUUID)
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    response = requests.get(url , headers=headers, verify=False, auth=(variables['PCUser'], variables['PCPassword']))
    response_data = json.loads(response.text)

    if len(response_data['data']):
        return response_data['data'][0]['serial']
    else:
        return None

# ========================================================================
# = getClusterUUID
# ========================================================================
# ToDo : rewrite with SDK when available (seems broken)
def getClusterUUID(variables):

    url="https://%s:9440/api/clustermgmt/v4.0.b2/config/clusters" % variables['PC']
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    response = requests.get(url, headers=headers, verify=False, auth=(variables['PCUser'], variables['PCPassword']))
    response_data = json.loads(response.text)

    json_expr = parse('data[?(@.nodes.numberOfNodes==3)].extId')

    for match in json_expr.find(response_data):
        return match.value

    return None    

# ========================================================================
# = getRunwayForCluster
# ========================================================================
# ToDo : rewrite with SDK when available
def getRunwayForCluster( variables):

    url="https://%s:9440/api/nutanix/v3/groups" % variables['OldPC']
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    payload = {
    "entity_type": "cluster",
    "group_member_attributes": [
        {
            "attribute": "capacity.runway"
        }
    ],
    "query_name": "prism:RunwayInfoQueryModel",
    "interval_start_ms": int((time.time()-3*86400)*1000),
    "interval_end_ms": int(time.time()*1000),
    "downsampling_interval": 86400
    }
    
    response = requests.post(url, data=json.dumps(payload), headers=headers, verify=False, auth=(variables['OldPCUsername'], variables['OldPCPassword']))
    response_data = json.loads(response.text)    

    json_expr = parse("$.group_results[0].entity_results[0].data[?(@.name=='capacity.runway')].values[*].values")

    for match in json_expr.find(response_data):
        return match.value[0]

    return 0

# ========================================================================
# = retrievePlaybookInfo
# ========================================================================
# ToDo : Redevelop with v4 API/sdk when available
def retrievePlaybookInfo( name, variables):
    playbookID=None

    url="https://%s:9440//api/nutanix/v3/groups" % variables['PC']
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    payload = {
        "length": 100,
        "entity_type": "action_rule",    
        "grouping_attribute": " ",
        "group_count": 3,
        "group_offset": 0,
        "group_attributes": [],
        "group_member_count": 40,
        "group_member_offset": 0,
        "group_member_attributes": [
            {
                "attribute": "name"
            }
        ]
    }

    response = requests.post(url, data=json.dumps(payload), headers=headers, verify=False, auth=(variables['PCUser'], variables['PCPassword']))
    response_data = json.loads(response.text)

    json_expr=parse("$.group_results[*].entity_results[?(@.data[0].values[0].values[0]=='"+name+"')].entity_id")

    for match in json_expr.find(response_data):
        playbookID=match.value

    if playbookID == None:
        return False, None
    else:
        url = "https://%s:9440/api/nutanix/v3/action_rules/%s" % (variables['PC'], playbookID)

        response = requests.get(url, headers=headers, verify=False, auth=(variables['PCUser'], variables['PCPassword']))
        response_data = json.loads(response.text)    
        return True, response_data

# ========================================================================
# = retrieveAppId
# ========================================================================
# ToDo : Redevelop with v4 API/sdk when available
def retrieveAppId( name, variables):
    url="https://%s:9440/api/nutanix/v3/apps/list" % variables['PC']
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    payload = { 
               "kind": "app",
               "length": 100
               }

    response = requests.post(url, data=json.dumps(payload), headers=headers, verify=False, auth=(variables['PCUser'], variables['PCPassword']))
    response_data = json.loads(response.text)

    json_expr=parse("$.entities[?(@.status.name=='"+name+"')].status.uuid")

    # Only 1 ap can match
    for match in json_expr.find(response_data):
        variables['AppUUID']=match.value
        return match.value

    return None

# ========================================================================
# = retireveVpcId
# ========================================================================
def retireveVpcId( name, variables):

    sdkConfig = confSDKClient(variables['PC'], variables['PCUser'], variables['PCPassword'])
    client = ntnx_networking_py_client.ApiClient(configuration=sdkConfig)
    vpcs_api = ntnx_networking_py_client.VpcsApi(api_client=client)
    page = 0
    limit = 50

    try:
        response = vpcs_api.list_vpcs(_filter="name eq '" + name + "'")
        response_data = response.to_dict()
        
        if response_data['data'] == None:
            return None
        
        return response_data['data'][0]['ext_id']
    except ntnx_networking_py_client.rest.ApiException as e:
        print(e)

    return None

# ========================================================================
# = retrieveScheduleInfo
# ========================================================================
# ToDo : Redevelop with v4 API/sdk when available
def retrieveScheduleInfo( name, variables):
    url="https://%s:9440/api/nutanix/v3/jobs/list" % variables['PC']
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    payload = { 
               "kind": "job",
               "length": 100
               }

    response = requests.post(url, data=json.dumps(payload), headers=headers, verify=False, auth=(variables['PCUser'], variables['PCPassword']))
    response_data = json.loads(response.text)

    json_expr=parse("$.entities[?(@.metadata.name=='"+name+"')].resources")

    # Only 1 ap can match
    for match in json_expr.find(response_data):
        return match.value

    return None

# ========================================================================
# = CheckBpTask
# ========================================================================
# ToDo : Redevelop with v4 API/sdk when available
def getBpContent(bpName, variables):
    
    # We get the ID
    url="https://%s:9440/api/nutanix/v3/blueprints/list" % variables['PC']
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    payload={
        "kind": "blueprint",
        "filter": "name=="+bpName
    }
    
    response = requests.post(url, json=payload, headers=headers, auth=(variables['PCUser'], variables['PCPassword']), verify=False)
    response_data=json.loads(response.text)
    
    if len(response_data['entities']) == 0:
        return None, None
    else:
        bpUuid = response_data['entities'][0]['metadata']['uuid']
    
    # WE get bp
    url="https://%s:9440/api/nutanix/v3/blueprints/%s" % (variables['PC'], bpUuid)
    
    response = requests.get(url, headers=headers, auth=(variables['PCUser'], variables['PCPassword']), verify=False)
    response_data=json.loads(response.text)
    
    jsonpath_expr = parse("$.status.resources.service_definition_list[*].action_list[?(@.name=='action_create')].runbook.task_definition_list")
    task=jsonpath_expr.find(response_data)
    
    return True, task
