'''
Author: fvilmos
https://github.com/fvilmos
'''
# location of CARLA egg file, needed for the data collector script
egg_file_abs_path = '' # full path to the .egg file, like: '<your path>\\CARLA\\WindowsNoEditor\\PythonAPI\\carla\\dist\\carla-0.9.13-py3.7-win-amd64.egg'

sensor_update_time = 0.08

out_dir = "\\out\\"

# select for automatic or manual drive
autopilot = True

#database name
db_name = '_info.rec'

# record data
record_data = True

# built in map index
RANDOM_MAP = False
MAP_INDEX=1

# car will be spammed randomly on the map
RANDOM_START_POSITION=False

# car index, 36 = Audi, 10 = Mini
CAR_INDEX=36

# camera image size
CAM_W= 320
CAM_H = 240
