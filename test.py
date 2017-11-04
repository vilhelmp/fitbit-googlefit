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

from pandas import DataFrame
import numpy as np

from helpers import *
from convertors import *
from remote import *

from dateutil.parser import parse

FITBIT_CREDENTIALS_FILE = "auth/fitbit.json"
FITBIT_API_URL = 'https://api.fitbit.com/1'
GFIT_MAX_POINTS_PER_UPDATE = 2000
DATE_FORMAT = "%Y-%m-%d"


start_date_str='2017-06-01'
end_date_str='2017-06-02'

convertor = Convertor('none', None)

credentials = json.load(open(FITBIT_CREDENTIALS_FILE))


fitbitClient = fitbit.Fitbit(**credentials)

userProfile = fitbitClient.user_profile_get()
tzinfo = dateutil.tz.gettz(userProfile['user']['timezone'])
convertor.UpdateTimezone(tzinfo)

start_date = convertor.parseHumanReadableDate(start_date_str)
end_date = convertor.parseHumanReadableDate(end_date_str)


dataType = 'steps'

for single_date in convertor.daterange(start_date, end_date):
    date_stamp = single_date.strftime(DATE_FORMAT)
    
res_path,detail_level,resp_id  = 'activities/steps','1min','activities-steps-intraday'


ts_data = fitbitClient.intraday_time_series(res_path, 
                base_date=date_stamp,
                detail_level=detail_level)
                
data = np.array([ np.array([i['time'],i['value'] ]) for i in ts_data['activities-steps-intraday']['dataset'] ])

date = ts_data['activities-steps'][0]['dateTime']

# should be able to do this more elegant with Pandas directly
data = np.array([ np.array([i['time'],i['value'] ]) for i in ts_data['activities-steps-intraday']['dataset'] ])
time, value = data.T

dtime = [parse(date+' '+i) for i in time]



# test plotting...
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
plt.ion()
plt.style.use('seaborn-pastel')
plt.step(dtime,value,color='SteelBlue', lw=1.5)

plt.gcf().autofmt_xdate()
myFmt = mdates.DateFormatter('%H:%M')
plt.gca().xaxis.set_major_formatter(myFmt)




