import tobii_research as tr
from math import isnan, nan
from time import time

from .gaze_filter import OneEuroFilter, IvtFilter
from .models import EyePosition, GazePoint


CALIBRATION_POINTS = [(0.5, 0.5), (0.1, 0.1), (0.1, 0.9), (0.9, 0.1), (0.9, 0.9)]

oe_filter_x = OneEuroFilter()
oe_filter_y = OneEuroFilter()
ivt_filter = IvtFilter(v_threshold=2)


class EyeTracker:
    def __init__(self) -> None:
        self.output_file = ""
        self.current_timestamp = None
        self.user_exists = False
        self.gaze_point = GazePoint(x=nan, y=nan)
        self.fixation_point = GazePoint(x=nan, y=nan)
        self.left_eye_position = EyePosition(x=nan, y=nan, z=nan)
        self.right_eye_position = EyePosition(x=nan, y=nan, z=nan)

        devices = tr.find_all_eyetrackers()
        if devices:
            self.device = devices[0]
            self.calibration = tr.ScreenBasedCalibration(self.device)
        else:
            self.device = None
            self.calibration = None
            print("No eyetrackers found")
            return


    def gaze_data_callback(self, gaze_point):
        # self.current_timestamp = gaze_point["system_time_stamp"]
        self.current_timestamp = time()
        left_x, left_y = gaze_point["left_gaze_point_on_display_area"]
        right_x, right_y = gaze_point["right_gaze_point_on_display_area"]

        x = (left_x + right_x) / 2
        y = (left_y + right_y) / 2

        if isnan(x) or isnan(y):
            self.gaze_point = GazePoint(x=x, y=y)
            self.fixation_point = GazePoint(x=x, y=y)
            return

        # Jitter filter
        x = oe_filter_x(self.current_timestamp, x)
        y = oe_filter_y(self.current_timestamp, y)
        self.gaze_point = GazePoint(x=x, y=y)

        # Fixation filter
        fp = ivt_filter(self.current_timestamp / 1000000, x, y)
        self.fixation_point = GazePoint(x=fp[0], y=fp[1])


    def user_position_guide_callback(self, user_position_guide):
        self.user_exists = user_position_guide['left_user_position_validity'] or user_position_guide['right_user_position_validity']
        if not self.user_exists:
            self.left_eye_position = EyePosition(x=nan, y=nan, z=nan)
            self.right_eye_position = EyePosition(x=nan, y=nan, z=nan)
            return

        left = user_position_guide["left_user_position"]
        right = user_position_guide["right_user_position"]

        self.left_eye_position = EyePosition(x=1 - left[0], y=left[1], z=left[2])
        self.right_eye_position = EyePosition(x=1 - right[0], y=right[1], z=right[2])


    def subscribe(self) -> None:
        if self.device:
            self.device.subscribe_to(tr.EYETRACKER_GAZE_DATA, self.gaze_data_callback, as_dictionary=True)
            self.device.subscribe_to(tr.EYETRACKER_USER_POSITION_GUIDE, self.user_position_guide_callback, as_dictionary=True)


    def unsubscribe(self) -> None:
        if self.device:
            self.device.unsubscribe_from(tr.EYETRACKER_GAZE_DATA, self.gaze_data_callback)
            self.device.unsubscribe_from(tr.EYETRACKER_USER_POSITION_GUIDE, self.user_position_guide_callback)
