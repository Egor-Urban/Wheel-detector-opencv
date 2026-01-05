# FrameProcessor.py

import cv2
import numpy as np
import logging

from datetime import datetime
from pathlib import Path


log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)
log_file = log_dir / f"{datetime.now().strftime('%Y-%m-%d')}.log"


logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(log_file, mode='a', encoding='utf-8'),
        logging.StreamHandler()
    ]
)


class FrameProcessor:
    def __init__(self, mode='file'):
        self.mode = mode
        self.blur_size = (11, 11)
        
        if mode == 'camera':
            self.canny_params = (30, 150, 3)
            self.hough_dp = 1.5
            self.hough_min_dist = 100
            self.hough_param1 = 50
            self.hough_param2 = 30
            self.hough_min_radius = 20
            self.hough_max_radius = 150
            logging.info("FrameProcessor initialized in CAMERA mode")
        else:
            self.canny_params = (0, 200, 3)
            self.hough_dp = 2
            self.hough_min_dist = 200
            self.hough_param1 = 60
            self.hough_param2 = 25
            self.hough_min_radius = 54
            self.hough_max_radius = 77
            logging.info("FrameProcessor initialized in FILE mode")
        
        
    def preprocess(self, frame):
        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            if self.mode == 'camera':
                clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
                gray = clahe.apply(gray)
            
            blur = cv2.GaussianBlur(gray, self.blur_size, 0)
            edges = cv2.Canny(blur, self.canny_params[0], self.canny_params[1], 
                            apertureSize=self.canny_params[2])
            
            return gray, edges
        
        except Exception as e:
            logging.error(f"Error preprocessing frame: {e}")
            return None, None


    def detect_circles(self, edges):
        try:
            circles = cv2.HoughCircles(
                edges, 
                cv2.HOUGH_GRADIENT, 
                dp=self.hough_dp,
                minDist=self.hough_min_dist,
                param1=self.hough_param1,
                param2=self.hough_param2,
                minRadius=self.hough_min_radius,
                maxRadius=self.hough_max_radius
            )
            
            if circles is not None:
                circles = np.uint16(np.around(circles))
                
            return circles
        
        except Exception as e:
            logging.error(f"Error detecting circles: {e}")
            return None