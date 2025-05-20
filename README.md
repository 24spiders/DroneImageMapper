# DroneSurveyMapper
A tool for reading drone image metadata (Exif, XMP) and creating survey GeoJSONs for use in GIS. A convenient way to visualize surveys and keep track of flight parameters.


![image](https://github.com/user-attachments/assets/e903b300-bd77-41df-bc8a-9ce4662dbd85)


## Features
This tool outputs a GeoJSON where each point represents a drone image. Each point has the following properties:
- Filename
- Date (MM/DD/YYYY)
- Time
- Altitude (m)
- Flight Height (m)
- Image Dimensions (w x h, px)
- Camera Model
- 35mm Focal Length (mm)
- Digital Zoom Ratio
- Gimbal Roll/Yaw/Pitch (degrees)
- Flight Roll/Yaw/Pitch (degrees)

## Usage
Navigate to the cloned directory and call

`python map_images.py survey_dir geojson_path --out_epsg EPSG:####`

Where
- survey_dir: Path to the folder containing drone imagery. e.g., "C:\MySurvey"
- geojson_path: path where the output GeoJSON file will be saved. e.g., "C:\MySurvey\survey.geojson"
- --out_epsg (optional): EPSG code for output projection, e.g., "EPSG:4326". Default is EPSG:4326.


## Installation
Navigate to the cloned directory and call
`python setup.py develop`
