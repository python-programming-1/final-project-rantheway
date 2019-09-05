#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Sep  3 17:55:54 2019

@author: shen
"""
import pandas as pd
import folium
from sodapy import Socrata
from pyproj import Proj, transform
from folium.plugins import MarkerCluster
#from folium.plugins import Search
from osgeo import ogr

### get data from public API into dataframe
client = Socrata("data.lacity.org", None)
results = client.get("wjz9-h9np", limit=1000000)
df = pd.DataFrame.from_records(results)

### drop other columns
df=df[['ticket_number', 'issue_date', 'location', 'fine_amount', 'latitude', 'longitude']]

### remove rows with invalid coordinates information
df= df[df['latitude']!= 99999.0]
df= df[df['longitude']!= 99999.0]

### create sub-dataframe and add two columns
location=df.groupby(['latitude','longitude','location']).size().reset_index(name='count').sort_values(by='count',ascending=False)
location=location[location['count']>10]
location['color']=location['count'].apply(lambda count:"red" if count>=500 else
                                         "Orange" if count>=300 and count<500 else
                                         "Yellow" if count>=100 and count<300 else
                                         "green"
                                         )
location['size']=location['count'].apply(lambda count:15 if count>=500 else
                                         10 if count>=300 and count<500 else
                                         5 if count>=100 and count<300 else
                                         1 
                                         )
                                         
### convert orginal state plain coordinates data into EPSG:4326, which folium will accept as valid location input
inProj = Proj(init='ESRI:102645', preserve_units = True)
outProj = Proj(init='EPSG:4326')
x, y = location['latitude'].values, location['longitude'].values
location['longitude'], location['latitude']= transform(inProj,outProj, x, y)

### create a new map with the coordinates or City of Los Angeles as center point                                
m=folium.Map([34.052235,-118.243683], zoom_start=11)

### create a MarkerCluster layer to better declutter the map
### I can't figure out the loss of information of CircleMarker after I added the MarkerCluster layer
mc = MarkerCluster()
for lat, lgn, loc, clr, count, size in zip(location['latitude'], location['longitude'], location['location'],location['color'],location['count'],location['size']):
    folium.CircleMarker([lat, lgn],
                        popup=loc,
                        radius=size,
                        color='blue',
                        fill=True,
                        fill_opacity=0.7,
                        fill_color=clr,
                       ).add_to(mc)
mc.add_to(m)
folium.LayerControl().add_to(m)

### unfinished search part, which doesn't work properly with MarkerCluster class object
"""
cs = Search(layer=mc,
            search_label= 'popup', 
            placeholder="Search for citation zones", 
            collapsed=False, 
            ).add_to(m)    



"""
### get coordinates infor from google map(LA Motorcycle Parking Map)
ds = ogr.Open('Locations.kml')
mp = []
for lyr in ds:
    for feat in lyr:
        geom = feat.GetGeometryRef()
        if geom != None:
            for i in range(0, geom.GetPointCount()):
                mp.append(geom.GetPoint(i))
 
mp_df = pd.DataFrame(mp, columns=['longitude', 'latitude', 'value'])
              
mp_df = mp_df.drop(['value'], axis = 1)

### mark parking lots on the map
for row in mp_df.itertuples():
    m.add_child(folium.Marker(location=[row.latitude, row.longitude],
           popup='Free Motorcycle Parking Lot'))
    
   
m.save('LA_parking_citations.html')

 