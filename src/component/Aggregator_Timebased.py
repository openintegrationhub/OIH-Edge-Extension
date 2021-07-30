# -*- coding: utf-8 -*-
"""
Created on Tue Nov  3 14:14:44 2020
Aggregator Component of the On-Edge Adapter.

@author: AUS
"""
#import numpy as np
import pandas as pd
import copy 
from datetime import datetime

from component.ComponentBaseClass import ComponentBaseClass


class Aggregator(ComponentBaseClass):
    
    def __init__(self, config):
        """
        Parameters
        ----------
        config : dict
        User configuration of the Aggregator component.
        e.g.:
            'config':{ 
                    'default': {"method":'mean',
                                "window_size":'5s'},	                            
                    'sensor2': {"method":'mean',
                                "window_size":'5s'} 
                                }
                    	'...':{...}
        """
        super().__init__(config)
        self.config = config
        self.method = self.config['default']['method']  #default aggregation method
        self.window = self.config['default']['window_size'] #default window_size
        #self.agg_methods=['mean','median','last','first','sum','min','max'] #implemented aggregation methods
        self.iter_data = []  #buffer raw data
        self.ret_data = []   #aggregated output data
        self.error = None
        self.info = None
        self.wait = True
        self.reference_ts_old = []
        self.reference_ts_new = []   #To-Do: combine to one reference-info
        self.reference_ts_old_setted = False
    
    def synchron(self,data,sensor):
        """
        This function is used when the sensor method is None. 
        The data will not be cached, but forwarded synchronously without any aggregation. 
        Parameters
        ----------
        data : list
            the list consists of dictionaries with a timestamp and a value
            e.g.
            {'timestamp': '2020-06-20T16:12:54', 'value': '34534,345'}.
        sensor : string
            Name of the sensor.

        Returns
        -------
        None.
        """
        self.wait = False
        self.iter_data['data'][sensor] = []
        self.ret_data['data'][sensor] = data

    def _calc_ref_ts(self,last_ts, cur_ts):
        
        mod = (last_ts.timestamp() - cur_ts.timestamp()) % (float(self.window.split('s')[0]))
        new_ts = last_ts.timestamp() - mod + float(self.window.split('s')[0])
      
        return datetime.fromtimestamp(new_ts)

    def aggregate(self,data,sensor):
        if len(data)> 1:
            if datetime.strptime(data[-1]['timestamp'],'%Y-%m-%dT %H:%M:%S:%f') > self.reference_ts_new['data'][sensor]:
                self.wait = False
                self.reference_ts_old['data'][sensor] = self.reference_ts_new['data'][sensor]
                self.reference_ts_new['data'][sensor] = self._calc_ref_ts(datetime.strptime(data[-1]['timestamp'],'%Y-%m-%dT %H:%M:%S:%f'), self.reference_ts_old['data'][sensor])
                
                data_df = pd.DataFrame(data)
                data_df['timestamp']=pd.to_datetime(data_df['timestamp'], format='%Y-%m-%dT %H:%M:%S:%f')
                
                agg_data = data_df[data_df['timestamp']<=self.reference_ts_old['data'][sensor]]
                
                non_agg_size = len(data_df) - len(agg_data)
                
                agg_data.index = agg_data['timestamp']
                
                if non_agg_size == 0:
                    self.iter_data['data'][sensor] = []
                else:
                    self.iter_data['data'][sensor] = data[-non_agg_size:]
                    
                agg_data = agg_data.groupby(pd.Grouper(freq=self.window, origin = pd.Timestamp(self.reference_ts_old['data'][sensor]))).aggregate(self.method)
                agg_data['timestamp'] = agg_data.index
                agg_data['timestamp'].dt.strftime('%Y-%m-%dT %H:%M:%S:%f')
                
                self.ret_data['data'][sensor] = agg_data.to_dict('records')

    def _clean_ret_data(self):
        for sensor in self.ret_data['data']:
            self.ret_data['data'][sensor].clear()
            
    def _clean_ts_ref_values(self):
        for sensor in self.reference_ts_old['data']:
            self.reference_ts_old['data'][sensor] = None
            self.reference_ts_new['data'][sensor] = None
        
    def _calc_modulo(self, data_size, window_size):
        """
        Doc TO-DO

        Parameters
        ----------
        data_size : TYPE
            DESCRIPTION.
        window_size : TYPE
            DESCRIPTION.

        Returns
        -------
        mod : TYPE
            DESCRIPTION.

        """
        mod = data_size % window_size
        return mod
    
    def _process(self,data):
        """
        Doc TO-DO

        Parameters
        ----------
        data : TYPE
            DESCRIPTION.

        Returns
        -------
        TYPE
            DESCRIPTION.

        """    
        try:      
            if len(self.ret_data)==0:
                self.ret_data=copy.deepcopy(data)
                self._clean_ret_data()
            else:
                self._clean_ret_data()
                
            # If iter_data is not empty, than extend the sensor values with the incoming data.
            if len(self.iter_data)==0:
                self.iter_data=copy.deepcopy(data)
            else :
                for sensor in self.iter_data['data']:
                    self.iter_data['data'][sensor].extend(data['data'][sensor])
            
            if len(self.reference_ts_old) == 0:
                self.reference_ts_old=copy.deepcopy(data)
                self.reference_ts_new=copy.deepcopy(data)
                self._clean_ts_ref_values()
                
                
            for sensor in self.iter_data['data']:
                if sensor in self.config:
                    self.method=self.config[sensor]['method']
                    self.window=self.config[sensor]['window_size']
                else:
                    self.method=self.config['default']['method']
                    self.window=self.config['default']['window_size']                
              
                if self.reference_ts_old_setted == False and self.reference_ts_old['data'][sensor]==None:
                    first_ts=self.iter_data['data'][sensor][0]['timestamp']
                    ref_ts=datetime.fromtimestamp(datetime.strptime(first_ts,'%Y-%m-%dT %H:%M:%S:%f').timestamp() + float(self.window.split('s')[0]))
                    self.reference_ts_new['data'][sensor]=ref_ts
                    
                if self.method==None:
                    self.synchron(self.iter_data['data'][sensor],sensor)
                else:
                    self.aggregate(self.iter_data['data'][sensor],sensor)
                    
            if None not in self.reference_ts_old['data'].values():
                self.reference_ts_old_setted=True
                    
        except Exception as error:
            self.error = str(self.__class__) + ": " + str(error)
            self.logger.exception("ERROR:")
        
        if not self.wait:
            self.wait=True
            return self.ret_data
        else:
            self.info = "Aggregator didnt achieve necessary window size "
            return None

    def process(self, data):
        """
        Parameters
        ----------
        data : dict
        
        JSON_BODY={
        'data':{
            'sensor1':[
                    {'timestamp':'2020-06-20T16:12:54', 'value':'34534,345'},
                    {'timestamp':'2020-06-20T16:12:55', 'value':'34534,345'}
                  ],
            'sensor2':[
                    {'timestamp':'2020-06-20T16:12:54', 'value':'closed'},
                    {'timestamp':'2020-06-20T16:12:55', 'value':'closed'}
                  ]
            ...
            ...
            ...
            }
        Returns
        -------
        dict
        Same structure as the input. 
        Just with the aggregated data (if not in synchron mode). 
        """
        return self._process(data)
        
  
        