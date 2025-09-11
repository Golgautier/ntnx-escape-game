from dotenv import load_dotenv
import json
import os
from escapegameengine import *
from functions import *
import urllib3
import sys
import random

urllib3.disable_warnings()

# Definition of the global variables
load_dotenv('config.env')

variables = {
    "Language": os.getenv('LANGUAGE'),
    "Username": os.getenv('USERNAME'),
    "PC": os.getenv('PC'),
    "PCPassword": os.getenv('PCPASSWORD'),
    "PCUser": os.getenv('PCUSER'),
    "Trigram": os.getenv('TRIGRAM'),
    "Vlanid": str(random.randrange(250)),
    "Nameserver": os.getenv('NAMESERVER'),
    "Gateway": os.getenv('GATEWAY'),
    "ImageURL": os.getenv('IMAGEURL'),
    "ProdUsername": os.getenv('PRODUSERNAME'),
    "ProdPassword": os.getenv('PRODPASSWORD'),
    "OldPC": os.getenv('OLDPC'),
    "OldPCUsername": os.getenv('OLDPCUSERNAME'),
    "OldPCPassword": os.getenv('OLDPCPASSWORD'),
    "ApprovalPolicy": os.getenv('APPROVALPOLICY'),
    "EmailReport": os.getenv('EMAILREPORT'),
    "Debug": False,
    "RecoveryUntilStage": 0,    
    "DockerRegistry": os.getenv('DOCKERREGISTRY'),
    "frontendHost": os.getenv("FRONTENDHOST"),
    "frontendPort": os.getenv("FRONTENDPORT")
}

firstStage=1
forceSilentModeDuringChecks = ['CheckTrigram','NeedRecovery']

# handling debug mode
if os.getenv('DEBUG') == 'True':
    variables['Debug'] = True
    firstStage=int(os.getenv('FIRSTSTAGE'))
    variables['UserUUID'] = os.getenv('USERUUID')
    variables['NetworkUUID'] = os.getenv('NETWORKUUID')
    variables['ProjectUUID'] = os.getenv('PROJECTUUID')
    variables['VMUUID'] = os.getenv('VMUUID')
    variables['ImageUUID'] = os.getenv('IMAGEUUID')
    variables['HostUUID'] = os.getenv('HOSTUUID')
    variables['CatUUID'] = os.getenv('CATUUID')
    variables['ProtectionPolicyUUID'] = os.getenv('PROTECTIONPOLICYUUID')



contentJsonFile="./gameContent.json"
labAnswersJsonFile="./labAnswers.json"
scoreFolder="./score"

# Main function
if __name__ == "__main__":

    # Load game content
    with open(contentJsonFile, 'r') as file:
        data = json.load(file)

    # Define maxstage
    maxStage = max(stage['id'] for stage in data['stages'])

    # Check for -clean parameter
    if '-clean' in sys.argv:
        maxStages=max(stage['id'] for stage in data['stages'])
        gameClean(scoreFolder, maxStages)
        print('Game cleaned')
        sys.exit(0)

    # Check for -changeStage parameter
    if '-changeStage' in sys.argv:
        try:
            trigram = sys.argv[2]
            stageId = int(sys.argv[3])
            if stageId < 1 or stageId > max(stage['id'] for stage in data['stages']):
                raise ValueError
        except (IndexError, ValueError):
            print('Invalid stage ID. Please provide a valid number between 1 and', maxStage)
            sys.exit(1)

        # Update score file
        UpdateScoreFile(scoreFolder, trigram, stageId, maxStage)
        print('Stage changed to', stageId, 'for user', trigram)
        
        # Exit 
        sys.exit(0)

    variables['SupportedLanguages'] = GetSupportedLanguages(contentJsonFile)

    # Clear the output screen
    os.system('cls' if os.name == 'nt' else 'clear')
     
    # *********************************** Display all stages *********************************** 
    with open(contentJsonFile, 'r') as file:
        data = json.load(file)

    # We browse all stages one by one
    for stage in data['stages']:
        
        # We load the message
        message,color,expectedvalue,checkScript=stageMessage(stage['id'], contentJsonFile, variables['Language'])
        
        # Check if we need to recover the stage
        if stage['id'] <= variables['RecoveryUntilStage'] and stage['active'] == True:
            
            # We do not display the message, because we are recovering the stage
            
            # ...but we check student work if needed, in silent mode
            if checkScript != '':
                CheckStage(checkScript, variables, silent=True)
        
        elif stage['id'] >= firstStage and stage['active'] == True:
            
            # We display the message because we are not recovering the stage and it is active            
            display(message, variables, color, expectedvalue)

            # Check student work if needed
            if checkScript != '':
                if stage['id'] == 1:
                    silentMode = True
                else:
                    silentMode = False
                CheckStage(checkScript, variables, silent=silentMode)

        # Update the score file
        UpdateScoreFile(scoreFolder, variables['Trigram'].lower(), stage['id'], maxStage, variables)

    # Reset display color
    sys.stdout.write('\033[0m')
