from functions import *
from jsonpath_ng.ext import parse
from main import contentJsonFile, scoreFolder
import os

# Here are all the functions called by the game content to check labs
# Each function returns a tuple (result, messageNumber, variable name)
# - result is a boolean (True if the check is OK, False otherwise)
# - mesageNumber is an int that give the message number to pickup in labAnswers.json for this script if test is not ok (start at 0)
# - variable name is the name of the dictionary key containing the value we check to validate the exercise. This value will be reasked by the engine if check is false


def CheckTrigram(variables,recoveryMode):
    # We check trigram info...     
    if len(variables['Trigram']) != 3:
        # If trigram is not 3 characters, we return False
        return False, 0, 'Trigram'

    return True, -1, None

# =============================================================================
# NeedRecovery - Done
# =============================================================================
def NeedRecovery(variables,recoveryMode):

    # Good moment to lower the trigram and language
    variables['Trigram']=variables['Trigram'].lower()
    variables['Language']=variables['Language'].lower()
    
    # Good moment to force language
    with open(contentJsonFile, 'r') as file:
        data = json.load(file)
    
    if not (variables['Language'] in data['supportedLanguages']):
        variables['Language']='en'
          
    # We check if the score file exists for this trigram
    scoreFile=scoreFolder+"/"+variables['Trigram']+".json"

    if os.path.exists(scoreFile) and os.path.getsize(scoreFile) == 0:
        data={}
    else:
        # We try to load the score file
        try:
            with open(scoreFolder+"/"+variables['Trigram']+".json", 'r') as fileScore:
                data = json.load(fileScore)
            
            if data and "username" in data:
                variables["Username"] = data["username"]
        except:
            data={}
        
    if data!={} and data['value'] > 2:
        variables['RecoveryUntilStage']=data['value']
        print("\n\nSpecial event : Entering in recovery mode ( Recovery Code :",variables['RecoveryUntilStage'],")...\n\n")

    return True, -1, None


# =============================================================================
# CheckUSer - Done
# =============================================================================
def CheckUser(variables,recoveryMode):
    
    #retrieve the user by filtering by name
    userId = retrieveUserId(userName=variables['Trigram'] + "-adm", variables=variables) #non existing user
    
    if userId is None:
        return False, 0, None
    
    # Store UserUUID in the variables
    variables['UserUUID'] = userId
        
    return True ,-1, None

# =============================================================================
# CheckAuthPolicy - Done
# =============================================================================
def CheckAuthPolicy(variables,recoveryMode):
    
    # Store UserUUID in the variables
    userId = variables['UserUUID']

    #retrieve the Super Admin role ID
    roleId = retrieveRoleId(roleName="Super Admin", variables=variables)

    #retrieve the authorization policy ID
    authorizationPolicyId = retrieveAuthorizationPolicyId(policyName=variables['Trigram'] + "-auth", variables=variables)

    if authorizationPolicyId is None:
        return False, 0, None
    
    #check if the authorization policy is associated to the correct role and user
    response = checkAuthorizationPolicyAssignement(authorizationPolicyId=authorizationPolicyId, roleId=roleId, userId=userId, variables=variables)

    if response is False:  
        return False, 1, None
        
    return True ,-1, None

# =============================================================================
# CheckProject - Done
# =============================================================================
def CheckProject(variables,recoveryMode):

    response = retrieveProjectInfo(projectName=variables['Trigram'] + "-proj", variables=variables)

    if response is None:      
        return False , 0, None
    else:
        # We check if infrastructure is correctly set
        if not ("account_reference_list" in response['spec']['resources'].keys()) or len(response['spec']['resources']['account_reference_list']) == 0:       
            return False , 1, None
        
        # We check users
        if len(response['spec']['resources']['external_user_group_reference_list']) + len(response['spec']['resources']['account_reference_list']) == 0:
            return False , 2, None

        # We store ProjectUUID in the variables to be used later
        variables['ProjectUUID'] = response['metadata']['uuid']
        
    return True , -1 , None
    
# =============================================================================
# CheckNetwork - Done
# =============================================================================
# Notes : We only verify if subnet, we do not really care of the configuration, as
# it is not used later in the game
def CheckNetwork(variables,recoveryMode):

    response = retrieveSubnetID(subnet_name=variables['Trigram'] + "-subnet", variables=variables)

    if response is None: 
        return False , 0, None
    
    # We store networkUUID in the variables to be used later
    variables['NetworkUUID'] = response    
    
    response = checkSubnetAdvanced(variables['NetworkUUID'], variables)
    
    if response is False:
        return False , 1, None
    

    return True, -1 , None

# =============================================================================
# CheckImage - Done
# =============================================================================
def CheckImage(variables,recoveryMode):

    response = retrieveImageID(image_name=variables['Trigram'] + "-ubuntu", variables=variables)

    if response is None: 
        return False , 0, None

    # We store ImageUUID in the variables to be used later
    variables['ImageUUID'] = response

    return True , -1 , None

# =============================================================================
# CheckImage - Done
# =============================================================================
def CheckVM(variables,recoveryMode):

    found,response = retrieveVMInfo(vm_name=variables['Trigram'] + "-vm", variables=variables)


    if found == False:
        return False, 0 , None
    elif recoveryMode == False:
        # We check VM details
        
        # Number of NICS
        try:
            if len(response['nics']) != 2:
                return False, 1, None
        except:
            return False, 1, None

        # Check network connection on our subnet
        try: 
            if ( response['nics'][0]['network_info']['subnet']['ext_id'] != variables['NetworkUUID']) and (response['nics'][1]['network_info']['subnet']['ext_id'] != variables['NetworkUUID'] ):
                return False, 2, None
        except:
            return False, 2, None

        try:
            # Check image used
            if response['disks'][0]['backing_info']['data_source']['reference']['image_ext_id'] != variables['ImageUUID']:
                return False, 3, None
        except:
            return False, 3, None

        # Project
        # GL ToDo : Migrate to v4/SDK when project will be available in SDK
        if getVMProjectUUID(response['ext_id'],pc=variables['PC'], user=variables['PCUser'],password=variables['PCPassword']) != variables['ProjectUUID']:
            return False, 4, None
        
        # Cloud Init
        # GL ToDo : Migrate to v4/SDK when guest-customization will be available in SDK
        if hasVMCloudinit(response['ext_id'],pc=variables['PC'], user=variables['PCUser'],password=variables['PCPassword']) == False:
            return False, 5, None

        # Power State
        if response['power_state'] != 'ON':
            return False, 6, None

    # Store VMUUID and HostUUID in the variables to be used later
    variables['VMUUID'] = response['ext_id']
    variables['HostUUID'] = response['host']['ext_id']

    return True, -1 , None

# =============================================================================
# CheckCat - Done
# =============================================================================
def CheckCat(variables,recoveryMode):
    found,_ = retrieveCatID(variables['Trigram'] + "-cat", None, variables=variables)

    # Check for category key first
    if not found: 
        return False , 0, None
    
    # Check for Value "Test"
    found,_ = retrieveCatID(variables['Trigram'] + "-cat", "Test", variables=variables)
    if not found: 
        return False , 1, None
    

    # Check for Value "Critical"
    found,uuid = retrieveCatID(variables['Trigram'] + "-cat", "Critical", variables=variables)
    if not found: 
        return False , 2, None
    else:
        variables['CatUUID'] = uuid        

    return True, -1 , None

# =============================================================================
# CheckCatVM - Done
# =============================================================================
def CheckCatVM(variables,recoveryMode):
    if recoveryMode:
        return True, -1 , None

    found,response = retrieveVMInfo(vm_name=variables['Trigram'] + "-vm", variables=variables)
    
    try:
        for tmp in response['categories']:
            if variables['CatUUID'] == tmp['ext_id']:
                return True, -1 , None
    except:
        return True, -1 , None
    
    return False, 0, None


# =============================================================================
# CheckStoragePolicy - Done
# =============================================================================
def CheckStoragePolicy(variables,recoveryMode):
    response = retrieveStoragePolicyID(policy_name=variables['Trigram'] + "-sto-policy", variables=variables)

    if response is None: 
        return False, 0, None

    # We store ImageUUID in the variables to be used later
    variables['StoragePolicyUUID'] = response

    return True, -1, None

# =============================================================================
# CheckSecurityPolicy - Done
# =============================================================================
def CheckSecurityPolicy(variables,recoveryMode):
    
    # Get info
    info = retrieveSecurityPolicyInfo(policy_name=variables['Trigram'] + "-mseg-policy", variables=variables)

    if info is None: 
        return False, 0 , None
    
    # We need to check the security policy configuration
    info_json=json.loads(json.dumps(info, default=str))

    #Category
    json_expr = parse('$.rules[*].spec.secured_group_category_references[*]')

    if variables['CatUUID'] not in [match.value for match in json_expr.find(info_json)]:
        return False, 1, None

    #State

    if info['state'] != 'ENFORCE':
        return False, 2 , None

    #Outbound
    json_expr = parse('$.rules[?(@.spec.is_all_protocol_allowed)].ext_id')

    if len(json_expr.find(info_json)) == 0:
        return False, 3, None

    # We store ImageUUID in the variables to be used later
    variables['SecurityPolicyUUID'] = info['ext_id']

    return True, -1 , None


# =============================================================================
# CheckSecurityPolicy2 - Done
# =============================================================================
def CheckSecurityPolicy2(variables,recoveryMode):

    # We get ssh service ID
    sshServiceUUID = retrieveFlowServiceID(service_name="ssh", variables=variables)

    # Get info
    info = retrieveSecurityPolicyInfo(policy_name=variables['Trigram'] + "-mseg-policy", variables=variables)

    if info is None: 
        return False, 0, None
    
    # We need to check the security policy configuration
    info_json=json.loads(json.dumps(info, default=str))

    #Inboud / Check if ssh rule is present
    json_expr= parse("$.rules[?(@.spec.service_group_references=~'"+sshServiceUUID+"')].ext_id")
        
    if json_expr.find(info_json):
        return False, 1, None

    #Inboud / Check if icmp rule is present
    json_expr= parse("$.rules[?(@.spec.icmp_services)].ext_id")

    if not json_expr.find(info_json):
        return False, 2, None

    return True, -1, None

# =============================================================================
# CheckProtectionPolicy - Done
# =============================================================================
def CheckProtectionPolicy(variables,recoveryMode):
    
    info = retrieveProtectionPolicyInfo(variables['Trigram'] + "-prot-policy", variables=variables)

    if info == None:
        return False, 0, None
    else:
        # We check policy details

        # Schedule
        if info['spec']['resources']['availability_zone_connectivity_list'][0]['snapshot_schedule_list'][0]['recovery_point_objective_secs'] != 3600:
            return False, 1, None

        # Retention
        if not ("rollup_retention_policy" in info['spec']['resources']['availability_zone_connectivity_list'][0]['snapshot_schedule_list'][0]['local_snapshot_retention_policy'].keys()) or info['spec']['resources']['availability_zone_connectivity_list'][0]['snapshot_schedule_list'][0]['local_snapshot_retention_policy']['rollup_retention_policy']['snapshot_interval_type'] != 'DAILY':       
            return False, 2, None

        # Categories
        cat=variables['Trigram']+"-cat"

        if cat not in info['status']['resources']['category_filter']['params'].keys():
           return False, 3, None
        
        # Category value
        if info['status']['resources']['category_filter']['params'][cat] == 'Critical':
            return False, 4, None

        variables['ProtectionPolicyUUID'] = info['metadata']['uuid']


    return True, -1 , None


# =============================================================================
# CheckApprovalPolicy - Done
# =============================================================================
def CheckApprovalPolicy(variables,recoveryMode):

    response = retrieveApprovalPolicyInfo(variables['ApprovalPolicy'], variables=variables)

    # We check if policy is created
    if response is None: 
        return False, 0, None
    else:
        # We check policy details

        # Approvers
        # Not tested, because of useless for next steps

        # targeted protection policy
        if 'securedPolicies' in response.keys(): 
            for item in response['securedPolicies']:
                if item['policyExtId'] == variables['ProtectionPolicyUUID']:
                    return True, -1 , None
            
        return False, 1, None

# =============================================================================
# CheckRestoreVM - Done
# =============================================================================
def CheckRestoreVM(variables,recoveryMode):

    found,response = retrieveVMInfo(vm_name=variables['Trigram'] + "-vm", variables=variables)

    if found == False: 
        return False, 0, None
    
    # Check Power State
    if response['power_state'] != 'ON':
        return False, 1, None    

    return True, -1, None

# =============================================================================
# CheckLiveMigration - Done
# =============================================================================
def CheckLiveMigration(variables,recoveryMode):
   
    found,response = retrieveVMInfo(vm_name=variables['Trigram'] + "-vm", variables=variables)

    if recoveryMode or (found and variables['HostUUID'] != response['host']['ext_id']):
        return True, -1 , None
    else:
        return False, 0, None
    
# =============================================================================
# CheckLiveMigration - Done
# =============================================================================
def CheckReport(variables,recoveryMode):

    found, info = retrieveReportInfo(variables['Trigram'] + "-report", variables=variables)

    if not found:
        return False, 0, None
    else:
        # We check report config

        # Schedule
        try:
            if not ('schedule' in info['spec']['resources'].keys() and 'interval_type' in info['spec']['resources']['schedule'].keys() and info['spec']['resources']['schedule']['interval_type'] == 'DAILY'):
                return False, 1, None
        except:
            return False, 1, None

        # Recipients
        try:
            if not (len(info['spec']['resources']['notification_policy']['email_config']['recipient_list'])!=0 and info['spec']['resources']['notification_policy']['email_config']['recipient_list'][0]['email_address']==variables['EmailReport']):
                return False, 2, None
        except:
            return False, 2, None

        # Content
        listvm=False
        
        try:
            for elt in info['spec']['resources']['template']['template_rows']:
                if elt['row_element_list'][0]['widget_config']['entity_type'] == 'vm':
                    listvm=True
        except: 
            return False, 3, None

        if listvm == False:
            return False, 3, None

    return True, -1, None

# =============================================================================
# CheckNewNode - Done
# =============================================================================
def CheckNewNode(variables,recoveryMode):
        
    if recoveryMode:
        return True, -1, None
    
    info = getNewNodeSerial(variables)

    if info is None:
        return False, 0, None
    
    if info.strip() != variables['NodeSerial'].strip():
        return False, 1, 'NodeSerial'

    return True, -1, None

# =============================================================================
# CheckUpdates - Done
# =============================================================================
def CheckUpdates(variables,recoveryMode):
    if recoveryMode:
        return True, -1, None    

    
    response = int(getNumberOfUpdates(variables))
    
    try:
        if response != int(variables['NumberUpdates']):
            return False, 0, "NumberUpdates"
    except:
        return False, 1, "NumberUpdates"


    return True, -1 , None

# =============================================================================
# CheckRunway - Done
# =============================================================================
def CheckRunway(variables,recoveryMode):
        
    if recoveryMode:
        return True, -1, None    
    
    value = getRunwayForCluster(variables)
    
    if value != variables['Runway']:
        return False, 0, "Runway"
    
    return True, -1 , None

# =============================================================================
# CheckPlaybook - Done
# =============================================================================
def CheckPlaybook(variables,recoveryMode):
    
    response, info = retrievePlaybookInfo(variables['Trigram'] + "-playbook", variables=variables)

    if not response:
        return False, 0, None
    else:
        # We Check elements
        
        # Trigger
        if len(info['spec']['resources']['trigger_list']) != 1 or ('type' not in info['spec']['resources']['trigger_list'][0]['input_parameter_values']) or ( info['spec']['resources']['trigger_list'][0]['input_parameter_values']['type'] != 'VmPowerCycleAudit'):
            return False, 1, None

        # Action
        if not (len(info['spec']['resources']['action_list'])==1 and  info['spec']['resources']['action_list'][0]['action_type_reference']['name'] == 'email_action'):
            return False, 2, None
            
       # Enabled
        if not info['spec']['resources']['is_enabled']:
            return False, 3, None
            
    return True, -1, None
        

# =============================================================================
# CheckCloneApp - Done
# =============================================================================
def CheckCloneApp(variables,recoveryMode):
    
    # Check App
    appId = retrieveAppId(variables['Trigram'] + "-app", variables=variables)

    if not appId:
        return False, 0, None

    # Check VPC
    vpcId = retireveVpcId(variables['Trigram'] + "-vpc", variables=variables)

    if not vpcId:
        return False, 1, None

    return True, -1 , None

# =============================================================================
# CheckCloneApp - Done
# =============================================================================
def CheckSchedDay2(variables,recoveryMode):
    
    # Check Schedule
    response = retrieveScheduleInfo(variables['Trigram'] + "-sched", variables=variables)

    try:
        if response['executable']['entity']['uuid'] != variables['AppUUID']:
            return False, 0, None
    except:
        return False, 1, None

    return True, -1, None


# =============================================================================
# CheckCloneApp - Done
# =============================================================================
def CheckUpdateBP(variables,recoveryMode):
    
    bpName = "bp-blankvm-prd"+variables['Vlanid']
    
    #Check it the task exist
    response,info = getBpContent(bpName,variables)
      
    if not response:
        return False, 0, None
    else:
        # We have the task details
        jsonpath_expr = parse("$[?(name=='foo')]")
        task=jsonpath_expr.find(info[0].value)
        
        if not task:
            return False, 1, None
        else:
            return True, -1, None