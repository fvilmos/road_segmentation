'''
Author: fvilmos
https://github.com/fvilmos
'''

from utils.data_recorder import DataRecorder
from utils.intersection_handler import IntersectonHandler
from utils import utils
from utils import recorder_config

import os
import sys
from queue import Queue
from queue import Empty
import cv2
import numpy as np


# don't use GPU, carla uses allready
os.environ['CUDA_VISIBLE_DEVICES'] = '-1'

spath, _ = os.path.split(os.path.realpath(__file__))

sys.path.append(recorder_config.egg_file_abs_path)
print("carla .egg path:" + recorder_config.egg_file_abs_path)

import carla

def get_camera_image(frame):
    """
    Transforms png format to RGB for opencv
    Args:
        frame (carla.SensorData): carla sensor data object

    Returns:
        uint8: formated RGB frame
    """
    data = np.frombuffer(frame[0].raw_data, dtype=np.dtype("uint8"))
    data = np.reshape(data, (frame[0].height, frame[0].width, 4))
    if frame[1] == 'cam_01':
        data = data[:, :, :3]
    if frame[1] == 'cam_d_01':
        data = data[:,:,:1]

    return np.array(data)

def sensor_callback(sensor_data, sensor_queue, sensor_name):
    """
    Sendor data callback

    Args:
        sensor_data (Sensor_Data): Carla object which holds the sensor data
        sensor_queue (object): Queue object
        sensor_name ([type]): [description]
        vehicle (Vehicle object): Ego vehicle object
    """
    sensor_queue.put((sensor_data, sensor_name))


#credits: carla => Deprecated/PythonClient/carla/image_converter.py
def labels_to_cityscapes_palette(image):
    """
    Convert an image containing CARLA semantic segmentation labels to
    Cityscapes palette.
    """
    classes = {
    # 0: [0, 0, 0], # None
    # 1: [70, 70, 70], # Buildings
    # 2: [190, 153, 153], # Fences
    # 3: [72, 0, 90], # Other
    # 4: [220, 20, 60], # Pedestrians
    # 5: [153, 153, 153], # Poles
    # 6: [157, 234, 50], # RoadLines
    # 7: [128, 64, 128], # Roads
    # 8: [244, 35, 232], # Sidewalks
    # 9: [107, 142, 35], # Vegetation
    # 10: [0, 0, 255], # Vehicles
    # 11: [102, 102, 156], # Walls
    # 12: [220, 220, 0] # TrafficSigns

    # 3 class: road, vehicles/pedestrians, others
    0: [0, 0, 0], # None
    1: [0, 0, 0], # Buildings
    2: [0, 0, 0], # Fences
    3: [0, 0, 0], # Other
    4: [255, 0, 0], # Pedestrians
    5: [0, 0, 0], # Poles
    6: [0,255, 0], # RoadLines
    7: [0,255,0], # Roads
    8: [0, 0, 0], # Sidewalks
    9: [0, 0, 0], # Vegetation
    10: [255, 0, 0], # Vehicles
    11: [0, 0, 0], # Walls
    12: [0, 0, 0] # TrafficSigns

    }
    data = np.frombuffer(image.raw_data, dtype=np.dtype("uint8"))
    data = np.reshape(data, (image.height, image.width, 4))[:,:,2]

    result = np.zeros((data.shape[0], data.shape[1], 3))
    for key, value in classes.items():
        result[np.where(data == key)] = value
    return result

def main():

    # use this to define the record granurality
    sensor_update_time = recorder_config.sensor_update_time

    path, _ = os.path.split(os.path.realpath(__file__))
    path += recorder_config.out_dir

    print (path)

    # recorder object
    meta_data = {}
    dr = DataRecorder(path,recorder_config.db_name)
    path = dr.enable_recording(recorder_config.record_data)

    client = carla.Client('localhost', 2000)
    client.set_timeout(8.0)
    
    # get Trafic Manager, needed to set for synch mode and autopilot
    tm = client.get_trafficmanager(8000)
    
    maps = client.get_available_maps()

    # set the world's map
    world = None
    if recorder_config.RANDOM_MAP == True:
        world = client.load_world(np.random.choice(maps))
    else:
        world = client.load_world(maps[recorder_config.MAP_INDEX])
    

    sensor_list = []
    sensor_queue = Queue(maxsize=4)

    try:

        # needed to restor the original setup
        original_settings = world.get_settings()
        settings = world.get_settings()

        # Set synch mode
        settings.fixed_delta_seconds = 0.05
        settings.substepping = True
        settings.synchronous_mode = True
        tm.set_synchronous_mode(True)
        
        world.apply_settings(settings)

        # Bluepints for the sensors
        blueprint_library = world.get_blueprint_library()
        v_bp = blueprint_library.filter('vehicle')[recorder_config.CAR_INDEX]
        
        # get one of the spam points
        map = world.get_map()

        # car will be spammed randomly on the map
        spam_points = map.get_spawn_points()
        if recorder_config.RANDOM_START_POSITION == True:
            start_position = np.random.choice(spam_points)
        else:
            start_position = map.get_spawn_points()[11]

        vehicle = world.spawn_actor(v_bp, start_position)

        # ignore traffic lights
        tm.ignore_lights_percentage(vehicle,100)

        # enable autopilot for data colection
        vehicle.set_simulate_physics(True)
        
        if recorder_config.autopilot == True:
            print ('Autopilot on')
            vehicle.set_autopilot(True)
        else:
            print ('Autopilot off')
            vehicle.set_autopilot(False)

        # create camera sensor
        cam_bp = blueprint_library.find('sensor.camera.rgb')
        cam_bp.set_attribute("fov",str(100))
        cam_bp.set_attribute("image_size_x",str(recorder_config.CAM_W))
        cam_bp.set_attribute("image_size_y",str(recorder_config.CAM_H))
        cam_bp.set_attribute("sensor_tick",str(sensor_update_time))

        
        camera_sensor_transform = carla.Transform(carla.Location(x=2.0, z=1.6),carla.Rotation (pitch = -15.0))
        cam_01 = world.spawn_actor(cam_bp, camera_sensor_transform, attach_to=vehicle)
        cam_01.listen(lambda data: sensor_callback(data, sensor_queue, "cam_01"))
        sensor_list.append(cam_01)

        # imu is uesd as dummy sensor to attach 3rd person view
        imu_bp = blueprint_library.find('sensor.other.imu')
        imu_3rd_transform = carla.Transform(carla.Location(x=-4.0,y=0.0, z=3.0), carla.Rotation (pitch = -30.0))
        imu = world.spawn_actor(imu_bp, imu_3rd_transform,attach_to=vehicle)

        
        # select camera type
        d_cam_bp = blueprint_library.find('sensor.camera.semantic_segmentation')

        d_cam_bp.set_attribute("fov",str(100))
        d_cam_bp.set_attribute("image_size_x",str(recorder_config.CAM_W))
        d_cam_bp.set_attribute("image_size_y",str(recorder_config.CAM_H))
        d_cam_bp.set_attribute("sensor_tick",str(sensor_update_time))

        cam_d_01 = world.spawn_actor(d_cam_bp, camera_sensor_transform,attach_to=vehicle)
        cam_d_01.listen(lambda data: sensor_callback(data, sensor_queue, "cam_d_01"))
        sensor_list.append(cam_d_01)

        # get sepectator object, is needed for 3rd person update 
        spectator = world.get_spectator()

        count = 1
        cmd = 'forward'
        intersection_state_obj = IntersectonHandler(scan_distance_next=8,scan_distance_prev=3,rotation_rate=0.1)

        # Main loop
        while True:

            # Tick the server
            world.tick()

            # dict to hold sensor file info
            file_names = {}
            
            try:
                # update 3rd person view with vehicle position
                spectator.set_transform(imu.get_transform())

                # collect ego vehicle information
                vcontrol = vehicle.get_control()

                # convert veocity to km/h
                vel = vehicle.get_velocity()
                vvel = 3.6 * np.sqrt(vel.x**2 + vel.y**2 + vel.z**2)
                
                # loop over sensors
                for _ in range(len(sensor_list)):
                    # get synchronized data from sensors, andsave it
                    s_frame = sensor_queue.get(True,0.001)

                    if recorder_config.record_data == True:
                        if dr.record == True:
                            if s_frame[1] == 'cam_d_01':
                                file_names['depth'] = s_frame[1] + '_' + str(s_frame[0].frame)+'.jpg'

                                # convert depth info to logaritmic representation
                                img_xxx = labels_to_cityscapes_palette(s_frame[0])
                                cv2.imwrite(path + file_names['depth'], img_xxx)
                                
                            else:
                                file_names['rgb'] = s_frame[1] + '_' + str(s_frame[0].frame)+'.jpg'
                                img_xxx = get_camera_image(s_frame)
                                cv2.imwrite(path + file_names['rgb'], img_xxx)


                    #==================
                    # filter sesor out
                    #==================
                    if s_frame[1] != 'cam_01':
                        continue

                    waypoint = map.get_waypoint(vehicle.get_location(),project_to_road=True,lane_type=carla.LaneType.Driving)    

                    cmd = intersection_state_obj.run(wp=waypoint,vehicle=vehicle)

                    img = get_camera_image(s_frame)
                    dimg = img.copy()

                    k = cv2.waitKey(1)

                    ########################  
                    # Autopilot mode active
                    ########################  
                    if recorder_config.autopilot == True:
                        utils.puttext_bg(dimg,"driver: " + '{}'.format('autopilot'),(20,60))
                    else:
                        utils.puttext_bg(dimg,"driver: " + '{}'.format('manual-asdwq r'),(20,60))

                    # set throttle
                    if k == ord('w'):
                        vcontrol.throttle += 0.1
                    if k == ord('s'):
                        vcontrol.throttle -= 0.1
                    
                    # steer left / right
                    if k == ord('a'):
                        vcontrol.steer -= 0.1
                    
                    if k == ord('d'):
                        vcontrol.steer += 0.1

                    # reverse
                    if k == ord('q'):
                        if  vcontrol.reverse == True:
                            vcontrol.reverse = False
                        else:
                            vcontrol.reverse = True

                    if k == ord('r'):
                        if dr.record == True:
                            dr.record = False
                        else:
                            dr.record = True
                    
                    # exit on ESC
                    if k == 27:
                        return


                    vcontrol.steer = round (min(0.7, max(-0.7, vcontrol.steer)),2)
                    vcontrol.throttle = min(1.0, max(0.0, vcontrol.throttle))

                    vehicle.apply_control(vcontrol)
                    vcontrol.brake = 0 

                    # draw driwing wheel
                    # poloar coordinates
                    r = 20
                    x = int(r * np.cos(-1.57 + 4*vcontrol.steer))
                    y = int(r * np.sin(-1.57 + 4*vcontrol.steer))

                    cv2.circle(dimg,(dimg.shape[1]//2,dimg.shape[0]//2),r,[255,0,0],1)
                    cv2.circle(dimg,(dimg.shape[1]//2+x,dimg.shape[0]//2+y),5,[255,0,255],-1)

                    utils.puttext_bg(dimg,"steer: " + '{:.2f}'.format(vcontrol.steer),(20,20))
                    utils.puttext_bg(dimg,"throttle: " + '{:.2f}'.format(vcontrol.throttle),(20,30))
                    utils.puttext_bg(dimg,"velocity: " + '{:.2f}'.format(vvel),(20,40))
                    utils.puttext_bg(dimg,"direction: " + '{}'.format(cmd),(20,50))
                    utils.puttext_bg(dimg,"keys: asdwq r-rec",(20,10))

                    if dr.record == True:
                        utils.puttext_bg(dimg,"*REC* ",(280,20))

                    cv2.imshow('RGB_CAM', dimg) 

            except Empty:
                # no data in the quieue
                pass

            count +=1
            #save data          
            dr.save_sensor_data_dict(file_names,vcontrol=vcontrol,velo=vvel,direction=cmd,junction=cmd,meta_dict=meta_data)
    except :
        # gather error info
        exc_type, exc_value, exc_traceback = sys.exc_info()
        print (exc_type, exc_value,exc_traceback)

    finally:

        # save and restore on exit
        print ('Destroy...')
        dr.close_file()
        world.apply_settings(original_settings)
        for sensor in sensor_list:
            sensor.destroy()

        imu.destroy()
        vehicle.destroy()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print('Done')
