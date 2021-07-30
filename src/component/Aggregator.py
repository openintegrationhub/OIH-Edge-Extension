# -*- coding: utf-8 -*-
"""
Created on Tue Nov  3 14:14:44 2020
Aggregator Component of the On-Edge Adapter.
TO-DO:
    1)Error handling
    2)Aggregation by time. 
    3)Doc of some functions
@author: AUS
"""

import copy
import numpy as np
import pandas as pd

from component.ComponentBaseClass import ComponentBaseClass


class Aggregator(ComponentBaseClass):
    
    def __init__(self, config):
        """
        Parameters
        ----------
        config : dict
        User configuration of the Aggregator component.
        e.g.:
            { 
            'default': ('mean',5),	  #statt z.B. ('mean',5) auch  ('None','None') möglich                            
            'Devices.ReactorTemp': ('last',5)
            ...
            }
        """
        super().__init__(config)
        self.config=config
        self.method=self.config['default'][0]  #default aggregation method
        self.window=self.config['default'][1]  #default window_size
        self.agg_methods=['mean','median','last'] #implemented aggregation methods
        self.iter_data = []  #buffer raw data
        self.ret_data = []   #aggregated output data
        self.error = None
        self.info = None
        self.wait = True
    
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
        self.wait=False
        self.iter_data['data'][sensor]=[]
        self.ret_data['data'][sensor]=data

    
    def aggregate(self,data,sensor):
        """
        Doc TO-DO

        Parameters
        ----------
        data : TYPE
            DESCRIPTION.
        sensor : TYPE
            DESCRIPTION.

        Raises
        ------
        ValueError
            DESCRIPTION.

        Returns
        -------
        None.

        """
        try:
            if len(data)>=self.window:
                
                self.wait=False
                modulo = self._calc_modulo(len(data),self.window)
            
                if modulo!= 0:
                    #This is the dataset which will be aggregated.
                    agg_data=pd.DataFrame(data[:-modulo])
        
                    #This is the remaining data in the buffer
                    self.iter_data['data'][sensor]=data[-modulo:]
                    
                else:
                    agg_data=pd.DataFrame(data[:])
                    self.iter_data['data'][sensor]=[]
                    
                
                agg_data= np.array_split(agg_data,len(agg_data)/self.window)
                
                if self.method not in self.agg_methods:
                    raise ValueError('Aggretion method %s not known' %(self.method))
                
                if self.method == 'mean':
                    #agg_data= [np.mean(d) for d in agg_data]
                    self.ret_data['data'][sensor]=[{'timestamp':pd.DataFrame(ad)['timestamp'].iloc[-1], 'value':pd.DataFrame(ad)['value'].aggregate('mean')} for ad in agg_data]
                elif self.method == 'median':
                    #agg_data= [np.median(d) for d in agg_data]
                    self.ret_data['data'][sensor]=[{'timestamp':pd.DataFrame(ad)['timestamp'].iloc[-1], 'value':pd.DataFrame(ad)['value'].aggregate('median')} for ad in agg_data]
                elif self.method == 'last':
                    #agg_data= [d[-1] for d in agg_data]
                    self.ret_data['data'][sensor]=[{'timestamp':pd.DataFrame(ad)['timestamp'].iloc[-1], 'value':pd.DataFrame(ad)['value'].iloc[-1]} for ad in agg_data]
         
        except Exception as error:
            self.error = str(self.__class__) + ": " + str(error)
            self.logger.exception("ERROR:")

                
    def _clean_ret_data(self):
        for sensor in self.ret_data['data']:
            self.ret_data['data'][sensor].clear()
        
    def _calc_modulo(self,data_size,window_size):
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
        mod=data_size % window_size        
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
            
            for sensor in self.iter_data['data']:
                if sensor in self.config:
                    self.method=self.config[sensor][0]
                    self.window=self.config[sensor][1]
                else:
                    self.method=self.config['default'][0]
                    self.window=self.config['default'][1]
                    
                if self.method==None:
                    self.synchron(self.iter_data['data'][sensor],sensor)
                else:
                    self.aggregate(self.iter_data['data'][sensor],sensor)
                    
        except Exception as error:
            self.error = str(self.__class__) + ": " + str(error)
            self.logger.exception("ERROR:")
        
        if self.wait == False:
            self.wait=True
            return self.ret_data
        else:
            self.info = ("Aggregator didnt achieve necessary window size ")
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
        
  
        