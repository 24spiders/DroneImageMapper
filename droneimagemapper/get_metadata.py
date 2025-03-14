# -*- coding: utf-8 -*-
"""
Created on Thu Mar 13 14:18:00 2025

@author: Labadmin
"""

from PIL import Image
from pyproj import Proj, Transformer
import os
import geopandas as gpd
from shapely.geometry import Point


class XMPReader:
    def __init__(self,
                 image_path):
        """
        XMPReader reads the XMP data of a single drone (DJI JPEG) image and parses some relevant metadata.
        Properties include coordinates and heights.
        TODO: Some of the parsing can be cleaned up (less hardcoded numbers)
        TODO: There are many more properties in the XMP data; should add more (e.g., date, yaw/pitch/roll of drone and camera, etc)

        Args:
            image_path (str): path to the DJI drone image

        """
        self.image_path = image_path
        self.xmp_string = self._read_xmp_data(image_path)
        self.lon_lat = self._get_lon_lat()
        self.flight_height = self._get_flight_height()

    def _read_xmp_data(self, image_path):
        """
        Reads the XMP data from a JPEG image

        Args:
            image_path (str): Path to the iamge.

        Returns:
            xmp_string (str): The XMP data as a continuous string.

        """
        # Open the image
        with open(image_path, "rb") as fin:
            # Read as a string
            img = fin.read()
            img_as_string = str(img)
            # Parse the XMP
            xmp_start = img_as_string.find('<x:xmpmeta')
            xmp_end = img_as_string.find('</x:xmpmeta')
            if xmp_start != xmp_end:
                xmp_string = img_as_string[xmp_start:xmp_end + 12]
        return xmp_string

    def _get_lon_lat(self):
        """
        Parses the longitude and latitude from the XMP data. DJI stores this in EPSG:4326 by default.

        Returns:
            gps_longitude (float): Longitude of the drone at the time of image capture in EPSG:4326.
            gps_latitude (float): Latitude of the drone at the time of image capture in EPSG:4326.

        """
        gps_longitude = float(self.xmp_string[self.xmp_string.find('drone-dji:GpsLongitude="') + len('drone-dji:GpsLongitude="'):self.xmp_string.find('drone-dji:AbsoluteAltitude=') - 7])
        gps_latitude = float(self.xmp_string[self.xmp_string.find('drone-dji:GpsLatitude="') + len('drone-dji:GpsLatitude="'):self.xmp_string.find('drone-dji:GpsLongitude="') - 7])
        return (gps_longitude, gps_latitude)

    def _get_flight_height(self):
        """
        Parses the relative altitude from the XMP data. Returns in METRES

        Returns:
            flight_height (float): Relative altitude (m) of the drone at the time of image capture.

        """
        flight_height = float(self.xmp_string[self.xmp_string.find('drone-dji:RelativeAltitude="') + len('drone-dji:RelativeAltitude="'):self.xmp_string.find('drone-dji:GimbalRollDegree=') - 7])
        return flight_height

    def reproject_coords(self, out_epsg):
        """
        Reprojects the coordinates from lat/lon (EPSG:4326) to the given EPSG

        Args:
            out_epsg (str): The EPSG that is desired. e.g., if EPSG:32611 is desired, out_epsg='EPSG:32611'

        Returns:
            x_t (float): Transformed x coordinate.
            y_t (float): Transformed y coordinate.

        """
        inProj = Proj(init='epsg:4326')
        outProj = Proj(init=out_epsg)
        transproj = Transformer.from_proj(inProj, outProj)
        x_t, y_t = transproj.transform(self.lon_lat[0], self.lon_lat[1])
        return (x_t, y_t)


class SurveyToSpatial:
    def __init__(self,
                 img_dir,
                 out_epsg):
        """
        Reads a directory of survey images, converts to geospatial format (a GeoJSON of points containing metadata attributes)

        Args:
            img_dir (str): Directory to the folder containing drone JPEGs.
            out_epsg (str): The EPSG that is desired. e.g., if EPSG:32611 is desired, out_epsg='EPSG:32611'

        """
        self.out_epsg = out_epsg
        self.imgs = [os.path.join(img_dir, img) for img in os.listdir(img_dir) if img.lower().endswith('.JPG')]
        self.img_metadata = self._get_image_metadata()

    def _get_image_metadata(self):
        """
        Gets coordinates and metadata for each image in the survey.

        Returns:
            img_data (dict): Dictionary with coordinates and metadata.

        """
        img_coords = []
        img_names = []
        heights = []
        for img in self.imgs:
            XMP = XMPReader(img)
            x, y = XMP.reproject_coords(self.out_epsg)
            img_coords.append((x, y))
            _, t = os.path.split(img)
            img_names.append(t)
            heights.append(XMP.flight_height)
        img_data = {'coords': img_coords,
                    'filenames': img_names,
                    'heights': heights}
        return img_data

    def img_to_geojson(self, geojson_path):
        """
        Outputs a GeoJSON with a point at each image with the metadata associated with that image.

        Args:
            geojson_path (str): Path to save the GeoJSON.

        """
        geometry = [Point(x, y) for x, y in self.img_metadata['coords']]
        gdf = gpd.GeoDataFrame(geometry=geometry, crs=f'EPSG:{self.out_epsg}')
        for key, values in self.img_metadata.items():
            gdf[key] = values
        gdf.to_file(geojson_path, driver='GeoJSON')
