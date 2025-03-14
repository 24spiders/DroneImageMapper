# -*- coding: utf-8 -*-
"""
Created on Thu Mar 13 14:26:10 2025

@author: Labadmin
"""
import os
from get_metadata import SurveyToSpatial

if __name__ == '__main__':
    # os.chdir(r'G:\Shared drives\UofA Wildfire\Documents\Folders to be Shared\Whitefeather Sharing\Data\Missions')
    os.chdir(r'G:\Shared drives\UofA Wildfire Surveys\01 - RPAS Images\Lobstick\ENTERPRISE')
    mapper = SurveyToSpatial(survey_dir='2',
                             out_epsg='EPSG:32615')
    mapper.img_to_geojson(geojson_path='2.geojson')
