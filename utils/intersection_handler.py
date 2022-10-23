'''
Author:fvilmos 
https://github.com/fvilmos
'''

import numpy as np
class IntersectonHandler():
    def __init__(self,scan_distance_next=10.0,scan_distance_prev=3.0, rotation_rate=0.1) -> None:
        self.rotation_rate = rotation_rate
        self.scan_distance_next = scan_distance_next
        self.scan_distance_prev = scan_distance_prev
        self.car_command = 'forward'
        self.junction_ahead = False
        self.sm_state = 0 # 0 scan ahead, 1 scan current, 2 scan previous
        self.vehicle_last_state = None

    def run(self,wp, vehicle):
        # test if junction ahead
        if self.sm_state == 0:
            is_junction = (wp.next(self.scan_distance_next)[0]).is_junction
            if is_junction == True:
                self.junction_ahead = True
                self.sm_state = 1
            else:
                self.junction_ahead == False

        elif self.sm_state == 1:
            self.junction_ahead  = True
            in_junction= (wp.previous(self.scan_distance_prev)[0]).is_junction

            if in_junction == True:
                self.sm_state = 2

        elif self.sm_state == 2:
            out_junction= (wp.previous(self.scan_distance_prev)[0]).is_junction

            if out_junction == False:
                self.sm_state = 0
                self.junction_ahead = False

        vt = vehicle.get_transform()

        if self.vehicle_last_state is not None:
            diff = np.round(vt.rotation.yaw - self.vehicle_last_state.rotation.yaw,2)
        else:
            diff = 0.0

        if self.junction_ahead:
            if diff < -self.rotation_rate:
                self.car_command = 'left'
            elif diff > self.rotation_rate:
                self.car_command = 'right'
            else:
                self.car_command = 'forward'
        else:
            self.car_command = 'keep_lane'

        self.vehicle_last_state = vt
        self.last_wp = wp

        return self.car_command

    def get_status():
        pass
