#!/usr/bin/env python3

"""

TESTING GROUNDS TO LEARN HOW THE FITBIT-GOOGLEFIT sync app works.

"""


import time
import argparse
import logging
import dateutil.tz
import dateutil.parser
import configparser
import json
from datetime import timedelta, date, datetime

import fitbit
from fitbit.exceptions import HTTPTooManyRequests
from apiclient.discovery import build
from oauth2client.file import Storage
from oauth2client.client import OAuth2Credentials

import pandas as pd
import numpy as np

from helpers import *
from convertors import *
from remote import *

from dateutil.parser import parse


#### PLOTTING

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
plt.ion()
plt.style.use('seaborn-pastel')

####

FITBIT_CREDENTIALS_FILE = "auth/fitbit.json"
FITBIT_API_URL = 'https://api.fitbit.com/1'
GFIT_MAX_POINTS_PER_UPDATE = 2000
DATE_FORMAT = "%Y-%m-%d"


start_date_str='2017-08-01'     # including!
end_date_str='2017-08-02'       # excluding!

convertor = Convertor('none', None)

credentials = json.load(open(FITBIT_CREDENTIALS_FILE))


fitbitClient = fitbit.Fitbit(**credentials)

try:
    userProfile = fitbitClient.user_profile_get()
except:
    for t in ('access_token', 'refresh_token'):    
        credentials[t] = fitbitClient.client.token[t]
    json.dump(credentials, open(FITBIT_CREDENTIALS_FILE, 'w'))
    credentials = json.load(open(FITBIT_CREDENTIALS_FILE))
    fitbitClient = fitbit.Fitbit(**credentials)
    userProfile = fitbitClient.user_profile_get()

###########
# at this point you can fetch anything:
# e.g.
#ts_data = fitbitClient.time_series('activities/heart', 
#        period='1d', 
#        base_date='')
# activities/steps
# activities/distance
# activities/heart
# activities/calories

# body/weight
# body/fat

# sleep
#

###########

tzinfo = dateutil.tz.gettz(userProfile['user']['timezone'])
convertor.UpdateTimezone(tzinfo)

start_date = convertor.parseHumanReadableDate(start_date_str)
end_date = convertor.parseHumanReadableDate(end_date_str)

##### CONVERTORS
# move to convertors.py later 
# to convert the returned dictionaries to output
# more managable for writing to a database
def convert_steps():
    return None

def convert_hr():
    return None

def convert_distance():
    return None

def convert_calories():
    return None

### Fetch
# lists of things to fetch
activities = ['steps','distance', 'heart', 'calories']
# resolution to fetch said activities in
resolutions = ['1min', '1min',     '1sec',  '1min']

# overwrite the last date processed to a file
# ONLY once the date has been processed
date_processed = None
# alternatively there could be a function that tries to 
# determine the last successful sync date?

# now loop through every date, and if sucessful, update the 
# last sync date string
# this will probably change and be replace with high level functions
# but need to start somewhere.

for single_date in convertor.daterange(start_date, end_date):
    date_stamp = single_date.strftime(DATE_FORMAT)
    
    for aType,res,idx_id in activities,resolutions,index_names:
        try:
            ts_data = fitbitClient.intraday_time_series('activities/'+aType, 
                    base_date=date_stamp,
                    detail_level=res)
        # Need to catch the exception for too many requests/calls
        # if it hits this, should print the last date synced
        except:
            # ??
        # now we have the data for this activity
        # it usually contains a dictonary with several keys. 
        # One of which is also a daily summary.
        
        # Do different things depending on which activity
        
        #'activities-steps-intraday','activities-distance-intraday','activities-heart-intraday','activities-calories-intraday'
        data = np.array([ np.array([i['time'],i['value'] ]) for i in ts_data['activities-'+aType+'-intraday']['dataset'] ])
        time, value = data.T
        # I want full dates? 
        # need to figure out how to best write dates and times in a database!
        # the datetime function parse will fudge a datetime object
        dtime = [parse(date_stamp+' '+i) for i in time]
        if aType in ['steps']: # if steps, the data type is integer
            steps = pd.Series(data.T[1].astype('int'), index=dtime)





# steps
#res_path,detail_level,resp_id  = 'activities/steps','1min','activities-steps-intraday'
# distance
#res_path,detail_level,resp_id  = 'activities/distance','1min','activities-distance-intraday'
#HR
res_path,detail_level,resp_id  = 'activities/heart','1sec','activities-heart-intraday'
# calories
#res_path,detail_level,resp_id  = 'activities/calories','1min','activities-calories-intraday'



#data = np.array([ np.array([i['time'],i['value'] ]) for i in ts_data['activities-steps-intraday']['dataset'] ])
data = np.array([ np.array([i['time'],i['value'] ]) for i in ts_data['activities-heart-intraday']['dataset'] ])

#date = ts_data['activities-steps'][0]['dateTime']
date = ts_data['activities-heart'][0]['dateTime']

# should be able to do this more elegant with Pandas directly
#data = np.array([ np.array([i['time'],i['value'] ]) for i in ts_data['activities-steps-intraday']['dataset'] ])
data = np.array([ np.array([i['time'],i['value'] ]) for i in ts_data['activities-heart-intraday']['dataset'] ])
time, value = data.T





# test plotting...

plt.step(dtime,value,color='SteelBlue', lw=1.5)

plt.gcf().autofmt_xdate()
myFmt = mdates.DateFormatter('%H:%M')
plt.gca().xaxis.set_major_formatter(myFmt)




############
# Weight and fat

poundtokg = 0.453592

ts_data = fitbitClient.get_bodyweight(base_date='2017-08-01', 
                                    end_date='2017-08-30')['weight']
date = [i['date'] for i in ts_data]
time = [i['time'] for i in ts_data]
weight = np.array([i['weight'] for i in ts_data])*poundtokg
fat = np.array([i['fat'] for i in ts_data])
dtime = [parse(i+' '+j) for i,j in zip(date,time)]

#fitbitLogs = fitbitClient.ReadFromFitbit(callMethod,base_date=date_stamp,end_date=date_stamp)[resp_id]


# weight kg
plt.subplot(211)
plt.plot(dtime,weight,ls='-',marker='.')
plt.gcf().autofmt_xdate()
myFmt = mdates.DateFormatter('%D:%H:%M')
plt.gca().xaxis.set_major_formatter(myFmt)
# fat kg
plt.subplot(212)
plt.plot(dtime,fat/100.*weight,ls='-',marker='.')
plt.gcf().autofmt_xdate()
myFmt = mdates.DateFormatter('%D:%H:%M')
plt.gca().xaxis.set_major_formatter(myFmt)


############
# Sleep

ts_data = fitbitClient.get_sleep(datetime(2017, 8, 1, 0, 0))['sleep']
mdata = ts_data[0]['minuteData']

#date = [i['dateTime'] for i in ts_data]
time = [i['dateTime'] for i in mdata]
sleep = np.array([i['value'] for i in mdata])
#fat = np.array([i['fat'] for i in ts_data])
dtime = [parse('2017-08-01'+' '+j) for j in time]

#fitbitLogs = fitbitClient.ReadFromFitbit(callMethod,base_date=date_stamp,end_date=date_stamp)[resp_id]


# weight kg
plt.subplot(211)
plt.plot(dtime,sleep,ls='-',marker='.')
plt.gcf().autofmt_xdate()
myFmt = mdates.DateFormatter('%D:%H:%M')
plt.gca().xaxis.set_major_formatter(myFmt)
# fat kg
plt.subplot(212)
plt.plot(dtime,fat/100.*weight,ls='-',marker='.')
plt.gcf().autofmt_xdate()
myFmt = mdates.DateFormatter('%D:%H:%M')
plt.gca().xaxis.set_major_formatter(myFmt)

