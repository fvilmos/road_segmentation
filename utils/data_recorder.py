# fvilmos, https://github.com/fvilmos
import os
from datetime import datetime
import json
class DataRecorder():
    def __init__(self, path='.\\', info_file_name='info.rec'):
        """
        Data Recorder class, records data.

        Args:
            path (string): absolut path to the directory to store data
            info_file_name (string): file to collect information from ego vehicle
        """
        self.path = path
        self.file_name = info_file_name
        self.count = 0
        self.record = False
    
    def enable_recording(self, val = False):
        if val == True:
            # open file for writeing
            try:
                # check if directory exists
                dir_exist = os.path.isdir(self.path)
                path = self.path
                if not dir_exist:        
                    os.mkdir(self.path)
                else:
                    #create a dir from timestamp
                    ts = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
                    dir_name = os.path.join(self.path,ts)
                    os.mkdir(dir_name)
                    path = dir_name + '\\'
                    self.path = path
                self.f = open(path + self.file_name,'w')
                #self.record = True
                print ("save path:" + path + self.file_name)
                return path

            except :
                print ('something went wrong...check filename, path, or if directory allready exists!')

    def save_sensor_data_dict(self,file_name_dict,vcontrol=None,velo=0.0,direction='',junction=0, meta_dict=None):
        """
        Call periodically to collect data
        Args:
            file_name_dict (dict): holds the image name (rgb / drgb)
            vcontrol ( VehicleControl, optional): Carla VehicleControl object. Defaults to None.
            velo (float, optional): Velocity [km/h]. Defaults to 0.0.
        """
        infoline = ''

        if meta_dict is None:
            meta_data = {}
        else:
            meta_data = meta_dict

        if self.record:
            # record if we have all date from the sensors
            try:
                # collect file names
                rgb_c = file_name_dict['rgb']
                depth_c = file_name_dict['depth']

                meta_data['index'] = self.count
                meta_data['throttle'] = '{:.2f}'.format(vcontrol.throttle)
                meta_data['steer'] = '{:.2f}'.format(vcontrol.steer)
                meta_data['brake'] = '{:.2f}'.format(vcontrol.brake)
                meta_data['hand_brake'] = vcontrol.hand_brake
                meta_data['reverse'] =  vcontrol.reverse
                meta_data['manual_geat_shift'] = vcontrol.manual_gear_shift
                meta_data['gear'] = '{:.2f}'.format(vcontrol.gear)
                meta_data['velo'] = '{:.1f}'.format(velo)
                meta_data['direction'] = direction
                meta_data['junction'] = junction

                meta_data['rgb_c'] = str(rgb_c)
                meta_data['depth_c'] = str(depth_c)

                d_obj = json.dumps(meta_data)

                self.f.write(d_obj)
                self.f.write('\n')
                print ("index: " + str(self.count) + " direction: " + str(direction) + "\n")
                self.count += 1

            except:
                # not all data avaialble, skipp
                pass



    def close_file(self):
        """
        Close file object
        """
        if self.record:
            self.f.close