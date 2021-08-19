# -*- coding: utf-8 -*-
"""
Created on Thu Nov 12 14:14:35 2020
Anonymizer Component of the OIH-Edge .
@author: AUS
"""
import numpy as np
import pandas as pd
import copy
from component.ComponentBaseClass import ComponentBaseClass


# Input data format
# json_body={
#     'deviceID':'4711383',
#     'data':{
#         'sensor1':[
#                {'timestamp':'2020-06-20T16:12:54', 'value':'34534,345'},
#                {'timestamp':'2020-06-20T16:12:55', 'value':'34534,345'}
#               ],
#         'sensor2':[
#                {'timestamp':'2020-06-20T16:12:54', 'value':'closed'},
#                {'timestamp':'2020-06-20T16:12:55', 'value':'closed'}
#               ]
#         }
# }
#
#
# config={
#     'default': {
#         'name':'thresholder',
#             'window': 10,
#             'threshold':[100,200],
#             'substitution': [120,180]  #also calcuation or deletion of th sub values is possible. e.g. ('delete','mean')
#         },
#     'Sensor2':{
#         'name':'skipN',
#             'N': 10,
#         },
#     'Sensor3':{
#         'name':'featex',
#             'window': 10,
#             'feature': ['mean','std','var','kurtosis']
#         },
#     'Sensor4':{
#         'name':'randomizer',
#             'window': 10,
#             #'percent': 0.5,
#             'distribution': {'name': 'win_dist',
#                              'std': 1
#                               },
#                             {'name': 'random',
#                             'range': (1,100)
#                               }
#         },
#     'Sensor5':{
#         'name':'hider',
#         },
#     'Sensor6':{
#         'name':'categorizer',
#         'cats':[0,10,20,30,40,50],   #categories <10, 10-20, 20-30, 30-40, >40   #-float("inf")
#         'labels':[1,2,3,4,5]    #len(labels) must be len(cats)-1
#         },
#     }
#
#


class Anonymizer(ComponentBaseClass):
    def __init__(self, config):
        super().__init__(config)
        self.config=config
        self.sensor_config=None
        self.ano_methods=['thresholder','skipN','hider','randomizer','categorizer']
        self.iter_data=[]
        self.ret_data=[]
        self.error = None
        self.info = None
        self.wait=True
    
    def synchron(self,data,sensor):
        """
        This function is used when the sensor method is None. 
        The data will not be cached, but forwarded synchronously without any anonyzation. 
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
        
    def hider(self,data,sensor):
        self.iter_data['data'][sensor]=[]
    
    def thresholder(self,data,sensor):
        
        try:
            if len(data)>=self.sensor_config['window']:
                
                (low_ts, up_ts)=self.sensor_config['threshold']    
                (low_sub, up_sub)=self.sensor_config['substitution']
                self.wait=False
                modulo = self._calc_modulo(len(data),self.sensor_config['window'])
            
                if modulo!= 0:
                    #This is the dataset which will be aggregated.
                    ann_data=pd.DataFrame(data[:-modulo])
        
                    #This is the remaining data in the buffer
                    self.iter_data['data'][sensor]=data[-modulo:]
                    
                else:
                    ann_data=pd.DataFrame(data[:])
                    self.iter_data['data'][sensor]=[]
                    
                ann_data= np.array_split(ann_data,len(ann_data)/self.sensor_config['window'])
                
                for ann in ann_data:
                    ann['value'][ann['value'] > up_ts]=up_sub
                    ann['value'][(ann['value'] < low_ts) & (ann['value'] != up_sub)]=low_sub
                    
                    self.ret_data['data'][sensor].extend(ann.to_dict(orient='records')[:])
        
        except Exception as error:
             self.error = str(self.__class__) + ": " + str(error)
               
    def skipN(self,data,sensor):
        
        try:    
            if len(data)>=self.sensor_config['N']:
                self.wait=False
                modulo = self._calc_modulo(len(data),self.sensor_config['N'])
            
                if modulo!= 0:
                    #This is the dataset which will be aggregated.
                    ann_data=pd.DataFrame(data[:-modulo])
        
                    #This is the remaining data in the buffer
                    self.iter_data['data'][sensor]=data[-modulo:]
                    
                else:
                    ann_data=pd.DataFrame(data[:])
                    self.iter_data['data'][sensor]=[]
                    
                ann_data= np.array_split(ann_data,len(ann_data)/self.sensor_config['N'])
                
                self.ret_data['data'][sensor]=[{'timestamp':pd.DataFrame(ann)['timestamp'].iloc[-1], 'value':pd.DataFrame(ann)['value'].iloc[-1]} for ann in ann_data]
        
        except Exception as error:
            self.error = str(self.__class__) + ": " + str(error)
            
    def randomizer(self,data,sensor):
        
        try:
            if len(data)>=self.sensor_config['window']:
                
                self.wait=False
                modulo = self._calc_modulo(len(data),self.sensor_config['window'])
            
                if modulo!= 0:
                    #This is the dataset which will be aggregated.
                    ann_data=pd.DataFrame(data[:-modulo])
        
                    #This is the remaining data in the buffer
                    self.iter_data['data'][sensor]=data[-modulo:]
                    
                else:
                    ann_data=pd.DataFrame(data[:])
                    self.iter_data['data'][sensor]=[]
                    
                ann_data= np.array_split(ann_data,len(ann_data)/self.sensor_config['window'])
                
                if self.sensor_config['distribution']['name']=='random':
                    rl,rh=self.sensor_config['distribution']['range']
                    for ann in ann_data:
                        
                        ann['value']=ann['value']+ np.random.randint(rl,rh, ann.shape[0])
                        self.ret_data['data'][sensor].extend(ann.to_dict(orient='records')[:])
                
                elif self.sensor_config['distribution']['name']=='win_dist':
                    #print('TO-DO')
                    return None
        except Exception as error:
            self.error = str(self.__class__) + ": " + str(error)
                
    def categorizer(self,data,sensor):
        
        try:
            self.wait=False
            self.iter_data['data'][sensor]=[]
            
            df_data=pd.DataFrame(data)
            
            if type(self.sensor_config['cats'])==list:
                df_data['value']=pd.cut(df_data['value'],self.sensor_config['cats'],labels=self.sensor_config['labels'])
            elif type(self.sensor_config['cats'])==tuple:
                low,high,num=self.sensor_config['cats']
                lab=list(np.linspace(low,high,num))
                lab.insert(0,-float("inf"))
                lab.insert(len(lab),float("inf"))
                df_data['value']=pd.cut(df_data['value'],lab,labels=False)
                del lab
                
            self.ret_data['data'][sensor].extend(df_data.to_dict(orient='records')[:])
            del df_data
        except Exception as error:
            self.error = str(self.__class__) + ": " + str(error)
                                
    def correlation(self,data,sensor):
        return data
    
    def process(self, data):
        return self._process(data)
    
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
    
    def _clean_ret_data(self):
        for sensor in self.ret_data['data']:
            self.ret_data['data'][sensor].clear()
    
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
                    self.sensor_config=self.config[sensor]
                else:
                    self.sensor_config=self.config['default']
                    
                if self.sensor_config['name'] not in self.ano_methods:
                    raise ValueError('Anonymization method %s not known' %(self.sensor_config['name']))               
                
                if self.sensor_config['name']==None:
                    self.synchron(self.iter_data['data'][sensor],sensor)
                elif self.sensor_config['name']=='hider':
                    self.hider(self.iter_data['data'][sensor],sensor)
                elif self.sensor_config['name']=='categorizer':
                    self.categorizer(self.iter_data['data'][sensor],sensor)
                elif self.sensor_config['name']=='thresholder':
                    self.thresholder(self.iter_data['data'][sensor],sensor)
                elif self.sensor_config['name']=='skipN':
                    self.skipN(self.iter_data['data'][sensor],sensor)
                elif self.sensor_config['name']=='randomizer':
                    self.randomizer(self.iter_data['data'][sensor],sensor)
        except Exception as error:
            self.error = str(self.__class__) + ": " + str(error)
                
        
        if self.wait == False:
            self.wait=True
            return self.ret_data
        else:
            #self.info = ("Anonymizer didnt achieve necessary window size ")
            return None
        
                

        
  
        
