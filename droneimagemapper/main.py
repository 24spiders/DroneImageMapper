# -*- coding: utf-8 -*-
"""
Created on Thu Mar 13 14:26:10 2025

@author: Labadmin
"""
import os
from get_metadata import SurveyToSpatial

if __name__ == '__main__':
    os.chdir(r'G:\Shared drives\UofA Wildfire\Documents\Folders to be Shared\Whitefeather Sharing\Data\Missions')
    mapper = SurveyToSpatial(survey_dir='Dogrib',
                             out_epsg='EPSG:32616')
    mapper.img_to_geojson(geojson_path='dogrib.geojson')
