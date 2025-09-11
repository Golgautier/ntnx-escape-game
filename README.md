# ntnx-escape-game
Roleplay to discover Nutanix platform

# Preparation
- Book a HPOC with following characteristics : 
    - 3 nodes cluster (no more, no less)
    - AOS 7
    - PC2024.3.1+ (Need Calm 4.1 min)
    - Self-Service enabled
    - Leap Enabled
    - Flow security enabled
- In PC > Self-service, upload the **runbook**  `blueprint/EG-prerequisites.json` in the `lab` project 
- Launch it
- Upload the **blueprint** `blueprint/EG-EscapeGame.json` in the `lab` project (WARNING : Ensure you have launched the runbook first or you'll have problems)
  - Then, in this blueprint :
    - Update NUTANIX credential with password `nutanix/4u` (in the credential menu)
    - Update PLAYER credential with password `keepgoing` (in the credential menu)
- Save it
- Launch it
  - Chose a name of your choice
  - Fill the form
    - Select cluster and primary Network (`Game` section)
  - Clck on `deploy`

Note : 
 - 1st task of the blueprint checks AD credential. If tasks fails, please delete the app, change AD Endpoint credentials, and then redeploy the app from the BP.

!! IMPORTANT !! Known Issues : 
 - The current deployment has a little problem. Please update manually the project `production` to remove then re-add the user `thebadguy`
 - Please confirm the cluster has only 3 nodes (I experienced an issue once, because of erasure-coding). If not, please remove 4th node.

# Player prerequisites
- Internet Access
- If you want to use VPN access, ensure your players have installed and tested it first

# Game launch
- Use Day 2 actions of the BP to :
  - Launch invitation email to your players (you'll have to enter recipients list)
  - Launch "End of lab" email (First recipients list will be used)

Self-Service Application description will provide the URL to play, as it will be mentioned in the invitation email too.

Note : Day-2 operations can be found clicking on `Self-Service > Application > {your application} > Manage tab`, and you will run them by clicking on play icon, just after the day-2 action name.

# Dashboard

In the app description, you'll see dashboard URL. Display the dashboard on a screen, it will improve game feeling for players.

# Tips
- Unsuccesfull lab checks may happen even if the exercise is succesfully done. In this case, the player can refresh is web page, use the same trigram, and recovery mode will bring him to the same lab step, which could pass...
  - This is caused by ID memorized by script during execution, but not existing anymore (for exemple, if the player has deleted and recreated OS image, the game will wait the old ID, not the new one.)
- If you need to setup a stage to a user, you can look at [gameContent.json](gameContent.json) file to identify the stage number you need to use. 

