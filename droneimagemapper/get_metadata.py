# -*- coding: utf-8 -*-
"""
Created on Thu Mar 13 14:18:00 2025

@author: Labadmin
"""
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
from pyproj import Transformer, CRS
import os
import geopandas as gpd
from shapely.geometry import Point
from tqdm import tqdm


class EXIFXMPReader:
    def __init__(self,
                 image_path,
                 out_epsg='EPSG:4326'):
        """
        XMPReader reads the XMP data of a single drone (DJI JPEG) image and parses some relevant metadata.
        Properties include coordinates and heights.
        TODO: Some of the parsing can be cleaned up (less hardcoded numbers)
        TODO: There are many more properties in the XMP data; should add more (e.g., date, yaw/pitch/roll of drone and camera, etc)

        Args:
            image_path (str): path to the DJI drone image
            out_epsg (str): The EPSG that is desired. e.g., if EPSG:32611 is desired, out_epsg='EPSG:32611'. Default is EPSG:4326.

        """
        # Set attributes
        self.image_path = image_path
        self.xmp_string = self._read_xmp_data()
        self.exif_dict = self._read_exif_data()
        self.lon_lat = self._get_lon_lat()
        self.flight_height = self._get_flight_height()
        self.date_time = self._get_date_time()
        self.altitude = self._get_altitude()
        self.image_dims = self._get_image_dims()
        self.camera_model = self._get_camera_model()
        self.focal_length_35mm = self._get_35mm_focal_length()

        # Set transform
        self.transformer = self._set_transform(out_epsg)

    def _convert_to_degrees(self, value):
        """
        Converts from DMS coordinates to degrees

        Args:
            value (tuple): DMS coordinate.

        Returns:
            float: degree coordinates of value.

        """
        d, m, s = value
        return d + (m / 60.0) + (s / 3600.0)

    def _read_xmp_data(self):
        """
        Reads the XMP data from a JPEG image

        Returns:
            xmp_string (str): The XMP data as a continuous string.

        """
        # Open the image
        with open(self.image_path, "rb") as fin:
            # Read as a string
            img = fin.read()
            img_as_string = str(img)
            # Parse the XMP
            xmp_start = img_as_string.find('<x:xmpmeta')
            xmp_end = img_as_string.find('</x:xmpmeta')
            if xmp_start != xmp_end:
                xmp_string = img_as_string[xmp_start:xmp_end + 12]
        return xmp_string

    def _read_exif_data(self):
        """
        Reads the EXIF data from a JPEG image

        Returns:
            exif_dict (str): A dict with EXIF tags as keys

        """
        with Image.open(self.image_path) as image:
            exif_data = image._getexif()
        if not exif_data:
            raise Exception(f'Could not read EXIF data for {self.image_path}')
        exif_dict = {TAGS.get(tag, tag): value for tag, value in exif_data.items()}
        return exif_dict

    def _get_lon_lat(self):
        """
        Parses the longitude and latitude from the EXIF data. DJI stores this in Degrees/Minutes/Seconds by default, this converts to EPSG:4326.

        Returns:
            gps_longitude (float): Longitude of the drone at the time of image capture in EPSG:4326.
            gps_latitude (float): Latitude of the drone at the time of image capture in EPSG:4326.

        """
        gps_info = self.exif_dict.get('GPSInfo')
        gps_data = {GPSTAGS.get(tag, tag): value for tag, value in gps_info.items()}

        # Extract latitude and longitude
        if 'GPSLatitude' in gps_data and 'GPSLongitude' in gps_data:
            lat = self._convert_to_degrees(gps_data['GPSLatitude'])
            lon = self._convert_to_degrees(gps_data['GPSLongitude'])

            # Adjust for hemisphere
            if gps_data.get('GPSLatitudeRef') == 'S':
                lat = -lat
            if gps_data.get('GPSLongitudeRef') == 'W':
                lon = -lon

            return (lon, lat)

    def _get_flight_height(self):
        """
        Parses the relative altitude from the XMP data. Returns in METRES

        Returns:
            flight_height (float): Relative altitude (m) of the drone at the time of image capture.

        """
        flight_height = float(self.xmp_string[self.xmp_string.find('drone-dji:RelativeAltitude="') + len('drone-dji:RelativeAltitude="'):self.xmp_string.find('drone-dji:GimbalRollDegree=') - 7])
        return flight_height

    def _get_date_time(self):
        return self.exif_dict.get('DateTimeOriginal')

    def _get_altitude(self):
        return self.exif_dict.get('GPSInfo')[6]

    def _get_image_dims(self):
        with Image.open(self.image_path) as image:
            sz = image.size  # (width, height)
        return sz

    def _get_camera_model(self):
        return self.exif_dict.get('Model')

    def _get_35mm_focal_length(self):
        return self.exif_dict.get('FocalLengthIn35mmFilm')

    def _set_transform(self, out_epsg):
        in_crs = CRS.from_epsg(4326)
        out_crs = CRS.from_epsg(int(out_epsg.lower().replace('epsg:', '')))
        transformer = Transformer.from_crs(in_crs, out_crs, always_xy=True)
        return transformer

    def reproject_coords(self):
        """
        Reprojects the coordinates from lat/lon (EPSG:4326) to the given EPSG

        Returns:
            x_t (float): Transformed x coordinate.
            y_t (float): Transformed y coordinate.

        """
        x_t, y_t = self.transformer.transform(self.lon_lat[0], self.lon_lat[1])
        return (x_t, y_t)


class SurveyToSpatial:
    def __init__(self,
                 survey_dir,
                 out_epsg):
        """
        Reads a directory of survey images, converts to geospatial format (a GeoJSON of points containing metadata attributes)

        Args:
            img_dir (str): Directory to the folder containing drone JPEGs.
            out_epsg (str): The EPSG that is desired. e.g., if EPSG:32611 is desired, out_epsg='EPSG:32611'

        """
        self.out_epsg = out_epsg
        self.imgs = [os.path.join(survey_dir, img) for img in os.listdir(survey_dir) if img.lower().endswith('.jpg')]
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
        datetimes = []
        altitudes = []
        image_dims = []
        camera_models = []
        focal_lengths = []
        pbar = tqdm(total=len(self.imgs), desc='Reading image metadata')
        for img in self.imgs:
            Reader = EXIFXMPReader(img, self.out_epsg)
            x, y = Reader.reproject_coords()
            img_coords.append((x, y))
            _, t = os.path.split(img)
            img_names.append(t)
            heights.append(str(Reader.flight_height))  # Must be strings
            datetimes.append(str(Reader.date_time))
            altitudes.append(str(Reader.altitude))
            image_dims.append(str(Reader.image_dims))
            camera_models.append(str(Reader.camera_model))
            focal_lengths.append(str(Reader.focal_length_35mm))
            pbar.update(1)

        pbar.close()
        img_data = {'Coordinates': img_coords,
                    'Filename': img_names,
                    'Date Time': datetimes,
                    'Altitude (m)': altitudes,
                    'Flight Height (m)': heights,
                    'Image Dimensions (w x h)': image_dims,
                    'Camera Model': camera_models,
                    '35mm Focal Length': focal_lengths}
        return img_data

    def img_to_geojson(self, geojson_path):
        """
        Outputs a GeoJSON with a point at each image with the metadata associated with that image.

        Args:
            geojson_path (str): Path to save the GeoJSON.

        """
        geometry = [Point(x, y) for x, y in self.img_metadata['Coordinates']]
        gdf = gpd.GeoDataFrame(geometry=geometry, crs=f'{self.out_epsg}')
        for key, values in self.img_metadata.items():
            gdf[key] = values
        gdf.to_file(geojson_path, driver='GeoJSON')
