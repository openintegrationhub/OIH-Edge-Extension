# -*- coding: utf-8 -*-
"""
Created on Tue Nov 10 15:29:48 2020

@author: AUS
"""

from src.Component import Aggregator
import datetime
import random
import time

mode={
    'name':'aggregator-test',
    'description':'testing the functionality of the aggregator',
    'steps':[
        {
        'name':'agg',
    'config':{ 
    'default': ('mean',2),	  #statt z.B. ('mean',2) auch  (None,None) möglich                            
    'sensor2': ('last',5)
    }
         }
        ]
    }

T_AGG= Aggregator.Aggregator(mode['steps'][0]['config'])

DATA = {
        'data': {
            'sensor1':[],
            'sensor2':[]
        },
        "meta":{'deviceID':'4711383'}
    }

data_all=[[],[],[]]

START = time.time()
while time.time() - START < 8:
    time.sleep(1)
    
    for _ in range(1):
        RANDOM_NUMBER = random.randint(0,100)
        dt=datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        DATA['data']['sensor1'].extend([{
            'timestamp': dt,
                 'value': RANDOM_NUMBER}])
        DATA['data']['sensor2'].extend([{
            'timestamp': dt,
                 'value': RANDOM_NUMBER}])

    RET=T_AGG.process(DATA)
    data_all[0].append(DATA['data']['sensor1'][:])
    DATA['data']['sensor1'].clear()
    DATA['data']['sensor2'].clear()
    if RET!=None:
        print(RET)
        data_all[1].append(RET['data']['sensor1'][:])
        data_all[2].append(RET['data']['sensor2'][:])

        