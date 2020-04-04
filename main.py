import os
os.environ['GLOG_minloglevel'] = '2'

from flask import *
from flask import render_template
from flask_googlemaps import GoogleMaps
#from flask_googlemaps import Map
from flask import request
from app import app
from waitress import serve
#GoogleMaps(app, key="AIzaSyC7mDYbvnmQCBDIgkcXthbmwAT2WVSN0jE")


def begin_submit_step3():
    # Get details about event and push to database (Of course, sanitize inputs too.
    print("Begin submit step 3")

@app.route('/process_request', methods=['POST'])
def process_input():
    #Sanitize user input and add to SQL table
    print(request.form)
    return home_page()

@app.route('/beginsubmitB', methods=['POST'])
def begin_submit_step2():
    print("Begin submit step 2")
    returned = [x for x in request.form][0]
    print(returned)
    if returned == 'yes.x':
        return render_template("beginsubmitB.html")
    else:
        return home_page(not_free = True)

@app.route('/beginsubmit')
def begin_submit():
    print("Begin submit step 1")
    return render_template("beginsubmit.html")

@app.route('/')
def home_page(not_free = False):
    print("User has accessed home page.")
    return render_template("index_blocks.html", not_free = not_free)

if __name__ == '__main__':

    print("Server program has begin. Beginning service.")
    try:
        print("Attempting to open on port 80")
        serve(app, host='0.0.0.0', port=80)
    except:
        print("Unsuccessful. Attempting on port 8000")
        serve(app, host='0.0.0.0', port=8000)
    print("Main sequence closed. The program has ended.")