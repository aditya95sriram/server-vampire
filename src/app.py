"""The application entry point."""

import sys
if sys.version_info.major < 3:
    raise Exception("User error: This application only supports Python 3, so please use python3 instead of python!")

import json

from flask import Flask, request
from flask_cors import CORS

from model.parsing import parse
from model.vampire import VampireWrapper

import tempfile

import argparse

app = Flask(__name__)
app.config.from_object(__name__)
CORS(app)

parser = argparse.ArgumentParser(description='Run Vampire Server')
parser.add_argument("-vampire", "--vampire", required=True, action="store", dest="vampirePath", help="path to vampire-executable")
args = parser.parse_args()

vampireWrapper = VampireWrapper(args.vampirePath)

def startVampire(manualCS):
    request_params = request.get_json()
    fileContent = request_params.get('file', '')
    if fileContent == "":
        message = "User error: Input encoding must not be empty!"
        print(message)
        return json.dumps({
            "status" : "error",
            "message" : message
        })
    vampireUserOptions = request_params.get("vampireUserOptions", "")

    temporaryFile = tempfile.NamedTemporaryFile()
    temporaryFile.write(str.encode(fileContent))
    temporaryFile.flush() # commit file buffer to disk so that Vampire can access it

    if manualCS:
        output = vampireWrapper.startManualCS(temporaryFile.name, vampireUserOptions)
    else:
        output = vampireWrapper.start(temporaryFile.name, vampireUserOptions)

    if vampireWrapper.vampireState == "error":
        message = "User error: Wrong options for Vampire or mistake in encoding"
        print(message)
        return json.dumps({
            "status" : "error",
            "message" : message
        })

    lines = parse(output)
    temporaryFile.close()

    if manualCS:
        return json.dumps({
            'status' : "success",
            'vampireState' : vampireWrapper.vampireState, 
            'lines' : [line.to_json() for line in lines], 
        })
    else:
        return json.dumps({
            'status' : "success",
            'vampireState' : vampireWrapper.vampireState, 
            'lines' : [line.to_json() for line in lines]
        })

@app.route('/vampire/start', methods=['POST'])
def handle_startVampire():  
    return startVampire(False)

@app.route('/vampire/startmanualcs', methods=['POST'])
def handle_startVampireManualCS():
    return startVampire(True)

@app.route('/vampire/select', methods=['POST'])
def handle_selection():    
    request_params = request.get_json()
    selectedId = int(request_params.get('id', ''))

    if(vampireWrapper.vampireState != "running"):
        message = "User error: Vampire is not running, so it makes no sense to perform selection!"
        print(message)
        return json.dumps({
            'status' : "error",
            "message" : message,
            'vampireState' : vampireWrapper.vampireState
        })
    # TODO: check that selectedId was accepted by Vampire
    output = vampireWrapper.select(selectedId)
    lines = parse(output)

    return json.dumps({
        "status" : "success",
        'vampireState' : vampireWrapper.vampireState, 
        'lines' : [line.to_json() for line in lines], 
    })  

if __name__ == '__main__':
    app.run()
