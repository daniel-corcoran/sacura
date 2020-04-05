# q|daniel-_-corcoran|p

import os
from flask import *
from flask import render_template
from flask import request
from app import app
from waitress import serve
from profanityfilter import ProfanityFilter
import datetime
import random
import sqlite3
import geoip2.database

reader = geoip2.database.Reader('GeoLite2-City.mmdb')

os.environ['GLOG_minloglevel'] = '2'


def get_current_events():
    # Returns list of current events, and IPs on the waitlist (IE. Cannot post until 10 minute timer is up.)
    wait_ip = []
    curr_event = []

    now = datetime.datetime.now()
    print("Current time: {}".format(now))
    conn = sqlite3.connect('total_events.db')
    c = conn.cursor()
    select_query = '''SELECT * from events'''
    c.execute(select_query)
    records = c.fetchall()
    for event in records:
        event_id = event[0]
        event_ip = event[1]
        event_desc = event[2]
        event_loc = event[3]
        event_time = event[4]
        event_hrs = event[5]

        event_datetime_object = datetime.datetime.strptime(event_time.split('.')[0], '%Y-%m-%d %H:%M:%S')
        elapsed = now - event_datetime_object
        elapsed_m = elapsed.seconds / 60
        elapsed_h = elapsed.seconds / 3600
        if elapsed_m < 10.:
            wait_ip.append(event_ip)
        if elapsed_h < float(event_hrs):
            # Create a dictionary with the values.
            event_dic = {'event_id': event_id,
                         'event_ip': event_ip,
                         'event_desc': event_desc,
                         'event_loc': event_loc,
                         'event_time': event_time,
                         'event_hrs': float(event_hrs),
                         'elapsed': elapsed}

            curr_event.append(event_dic)
    return wait_ip, curr_event


def add_event(ip_address, food_activity, food_location, duration_hrs):
    event_id = random.randint(11111111111, 99999999999) # Generate random event ID
    print("Event ID: {}".format(event_id))
    # Connect to the database.
    conn = sqlite3.connect('total_events.db')
    c = conn.cursor()

    begin_time = str(datetime.datetime.now())
    sql = '''INSERT INTO events VALUES('{}', '{}', '{}', '{}', '{}', '{}')'''.format(event_id, ip_address,
                                                                                     food_activity, food_location,
                                                                                     begin_time, duration_hrs)
    c.execute(sql)
    conn.commit()
    conn.close()


def check_ip_spam(ip):
    # Check the submitter's IP address, and make sure they haven't submitted in 10 minutes.
    # This is necessary to prevent spam.
    # Return "True" if user must wait.
    ...
    wait_ip, curr_event = get_current_events()
    if ip in wait_ip:
        return True
    else:
        return False


def render_event(food_location, food_activity, food_duration, user_ip):
    # Render an event preview (Which will be saved as the event icon when user hits 'yes'.
    add_event(user_ip, food_activity, food_location, food_duration)


def sanitize_strings(food_location, food_activity, food_duration):
    # This function detects errors in the user input field.
    profanity = False  # Do any strings contain profanity?
    time = False  # Is the time field out of range, or not a number?
    empty = False  # Are any strings empty?  < 10 chars
    long = False  # Are any strings > 128 chars

    max_field_len = 50  # How long can a field be?
    min_activity_len = 10  # How short can a description be?
    min_location_len = 5  # How short can location description be?

    pf = ProfanityFilter()
    food_location_sanitized = pf.censor(food_location)
    food_activity_sanitized = pf.censor(food_activity)

    if food_location_sanitized != food_location:
        print("food_location: {}".format(food_location))
        print("food_location_sanitized: {}".format(food_location_sanitized))
        print("Mismatched. Censored contents detected.")
        profanity = True

    if food_activity_sanitized != food_activity:
        print("food_activity: {}".format(food_activity))
        print("food_activity_sanitized: {}".format(food_activity_sanitized))
        print("Mismatched. Censored contents detected.")
        profanity = True

    if '<script>' in food_activity or 'script' in food_location:
        print("<script> tag detected in input.")
        profanity = True

    if len(food_activity) > max_field_len or len(food_location) > max_field_len:
        long = True

    if len(food_activity) < min_activity_len or len(food_location) < min_location_len:
        empty = True

    try:
        food_duration = float(food_duration)
    except:
        print("food_duration: {}".format(food_duration))
        print("Not a floating point number.")
        time = True
    if time is False and (food_duration > 4 or food_duration < 0.5):
        print("Food duration of {} falls out of bounds. ".format(food_duration))
        time = True

    return {'profanity': profanity, 'time': time, 'empty': empty, 'long': long}


@app.route('/process_request', methods=['POST'])
def process_input():
    # Sanitize user input. If it checks out, we add it to the SQL table for events.
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

    print("Raw form submission")  # Pre-filtering.
    print("user_ip_address:\t{}".format(user_ip_address))
    print("food_duration_input:\t{}".format(food_duration_input))
    print("food_location_input:\t{}".format(food_location_input))
    print("food_activity_input:\t{}".format(food_activity_input))

    report = sanitize_strings(food_location_input, food_activity_input, food_duration_input)
    profanity = report['profanity']
    time = report['time']
    empty = report['empty']
    long = report['long']
    wait = check_ip_spam(user_ip_address)

    if True in [profanity, time, empty, long, wait]:

        print("Since the input is invalid we will ask for input again. ")
        return begin_submit_step2(profanity, time, empty, long, wait, try_again=True)
    else:
        # TODO: Replace with "submission successful" or "submission preview"

        add_event(user_ip_address, food_activity_input, food_location_input, food_duration_input)

        return home_page()


@app.route('/beginsubmitB', methods=['POST'])
def begin_submit_step2(profanity=False, time=False, empty=False, long=False, wait=False, try_again = False):
    returned = [x for x in request.form][0]
    print(returned)
    if returned == 'yes.x' or try_again:
        return render_template("beginsubmitB.html",
                               profanity=profanity,
                               time=time,
                               empty=empty,
                               long=long,
                               wait=wait)
    else:
        return home_page(not_free=True)


@app.route('/beginsubmit')
def begin_submit():
    return render_template("beginsubmit.html")


@app.route('/', methods=['POST', 'GET'])
def home_page(not_free=False):
    user_ip_address = request.environ['REMOTE_ADDR']
    print(user_ip_address)
    if user_ip_address == '127.0.0.1':
        bypass = True
    else:
        bypass = False
        response = reader.city(user_ip_address)
    if bypass or response.city.names['en'] == 'Cincinnati':
        print("User has accessed home page.")
        return render_template("index_blocks.html", not_free=not_free)
    else:
        print("User does not fall in geofence.")
        print(user_ip_address)
        print(response.city.names['en'])
        print("Sending to geofence warning.")
        return render_template("geofence_warning.html", loc = response.city.names['en'], ip=user_ip_address)
if __name__ == '__main__':

    print("Server program has begin. Beginning service.")
    try:
        print("Attempting to open on port 80")
        serve(app, host='0.0.0.0', port=80)
    except Exception as e:
        print(e)
        print("Unsuccessful. Attempting on port 8000")
        serve(app, host='0.0.0.0', port=8000)
    print("Main sequence closed. The program has ended.")
