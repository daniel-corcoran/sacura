import os
from flask import *
from flask import render_template
from flask import request
from app import app
from waitress import serve

from profanityfilter import ProfanityFilter

os.environ['GLOG_minloglevel'] = '2'

def sanitize_strings(food_location, food_activity, food_duration):
    # Ensure that strings contain SFW content.
    # If food_location or food_activity contain censored content, return False.
    # If food_duration is not a number between 1 and 4, return False.
    pf = ProfanityFilter()
    food_location_sanitized = pf.censor(food_location)
    food_activity_sanitized = pf.censor(food_activity)

    if food_location_sanitized != food_location:
        print("food_location: {}".format(food_location))
        print("food_location_sanitized: {}".format(food_location_sanitized))
        print("Mismatched. Censored contents detected.")
        food_location = False

    if food_activity_sanitized != food_activity:
        print("food_activity: {}".format(food_activity))
        print("food_activity_sanitized: {}".format(food_activity_sanitized))
        print("Mismatched. Censored contents detected.")
        food_activity = False
    try:
        food_duration = float(food_duration)
    except:
        print("food_duration: {}".format(food_duration))
        print("Not a floating point number.")
        food_duration = False
    if food_duration is not False and (food_duration > 4 or food_duration < 0.5):
        print("Food duration of {} falls out of bounds. ".format(food_duration))

    return food_location, food_activity, food_duration


@app.route('/process_request', methods=['POST'])
def process_input():
    # Sanitize user input and add to SQL table.
    # Compare IP address of user and make sure they aren't spamming events (IE. Have multiple events at once).

    print(request.form)
    # Keys in the submission:
    # food-duration-input   Time (in hours) the post should remain active. 1 - 4.
    # food-location-input   Directions to the event. Doesn't have to be coordinates.
    # food-activity-input   Description of food and activites at this event.
    # token

    user_ip_address = request.environ['REMOTE_ADDR']
    food_duration_input = request.form['food-duration-input']
    food_location_input = request.form['food-location-input']
    food_activity_input = request.form['food-activity-input']

    print("Raw form submission") # Pre-filtering.
    print("user_ip_address:\t{}".format(user_ip_address))
    print("food_duration_input:\t{}".format(food_duration_input))
    print("food_location_input:\t{}".format(food_location_input))
    print("food_activity_input:\t{}".format(food_activity_input))

    food_location_sanitized, food_activity_sanitized, food_duration_sanitizer = sanitize_strings(food_location_input,
                                                                                                 food_activity_input,
                                                                                                 food_duration_input)



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