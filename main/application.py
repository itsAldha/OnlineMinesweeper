#!flask/bin/python
from flask import Flask
from main.flaskrun import flaskrun

application = Flask(__name__)



if __name__ == '__main__':
    flaskrun(application)
