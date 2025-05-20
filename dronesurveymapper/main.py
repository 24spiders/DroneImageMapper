# -*- coding: utf-8 -*-
"""
Created on Thu Mar 13 14:26:10 2025

@author: Labadmin
"""

from dronesurveymapper.image.get_metadata import SurveyImagesToSpatial
from drone_survey_mapper.video.video_exif_reader import DJIVideoExifReader

if __name__ == '__main__':
    # Imagery
    mapper = SurveyImagesToSpatial(survey_dir='test',
                                   out_epsg='EPSG:32615')
    mapper.img_to_geojson(geojson_path='test.geojson')

    # Video
    video_path = 'test.MP4'
    output_dir = './test/'
    VidReader = DJIVideoExifReader(video_path, output_dir)
    VidReader.extract_frames_from_video()
    frames, frame_keys = VidReader.parse_exiftxt()
    VidReader.save_frame_csv(frames, frame_keys)
