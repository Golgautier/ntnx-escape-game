from dotenv import load_dotenv

from flask import Flask, render_template
import json, os, base64

app = Flask(__name__)

# Definition of the global variables
load_dotenv('config.env')

def loadScores():
    """
    Load scores from the scores.json file located in the parent directory.

    Returns:
        dict: A dictionary containing the scores and maximum score.
    """
    parentDir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    scoreDir = os.path.join(parentDir, 'score')
    
    # Intialize the data structure
    data = {"score": [], "maximumScore": {}}
    
    mas_stage_path = os.path.join(scoreDir, 'maxStage.json')
    if os.path.exists(mas_stage_path):
        with open(mas_stage_path) as f:
            data["maximumScore"] = json.load(f)['maximumScore']
    
    # Load all trigram score files
    for filename in os.listdir(scoreDir):
        if filename.endswith('.json') and len(os.path.splitext(filename)[0]) == 3:
            file_path = os.path.join(scoreDir, filename)
            trigram = os.path.splitext(filename)[0]
            with open(file_path) as f:
                file_data = json.load(f)
                file_data["player"] = trigram
                data["score"].append(file_data)

    print("Loaded scores from:", data)

    # Sort scores by player name
    data["score"].sort(key=lambda x: (x["value"], x["lastUpdated"]), reverse=True)
    return data

@app.route('/')
@app.route('/terminal')
def terminal():
    """
    Render the page for in Browser SSH terminal.

    Returns:
        str: Rendered HTML of the terminal page.
    """
    return render_template('terminal.html', hostname=os.getenv('FRONTENDHOST'), username=os.getenv('HOSTSSHUSERNAME'), password=base64.b64encode(os.getenv('HOSTSSHPASSWORD').encode("ascii")).decode('utf-8'))

@app.route('/ssh')
def ssh():
    """
    Render the page for in Browser SSH terminal.

    Returns:
        str: Rendered HTML of the terminal page.
    """
    return render_template('terminal2.html', hostname=os.getenv('FRONTENDHOST'), username=os.getenv('PLAYERSSHUSERNAME'), password=base64.b64encode(os.getenv('PLAYERSSHPASSWORD').encode("ascii")).decode('utf-8'))

@app.route('/scoreboard')
def scoreBoard():
    """
    Render the scoreboard page with scores and maximum score.

    Returns:
        str: Rendered HTML of the scoreboard page.
    """
    data = loadScores()
    return render_template('scoreboard.html', maximumScore=data["maximumScore"], scores=data["score"])

if __name__ == '__main__':
    app.run(host=os.getenv('FRONTENDHOST'), port=os.getenv('FRONTENDPORT'), debug=True)
