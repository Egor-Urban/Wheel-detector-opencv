# WheelFilter.py

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


class WheelFilter:
    def __init__(self, template_path="assets/wheel977.png", mode='file'):
        self.mode = mode
        self.template = None
        self.template_processed = None
        self.kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (7, 7))
        
        if mode == 'camera':
            self.min_radius = 20
            self.max_radius = 150
            self.min_y = 0  
            self.max_y = 100000
            self.ssd_threshold = 100000 
            self.use_template = False  
            logging.info("WheelFilter initialized in CAMERA mode (relaxed parameters)")
        else:
            self.min_radius = 53
            self.max_radius = 75
            self.min_y = 500
            self.max_y = 560
            self.ssd_threshold = 150000
            self.use_template = True
            logging.info("WheelFilter initialized in FILE mode (strict parameters)")
        
        if Path(template_path).exists() and self.use_template:
            self.template = cv2.imread(template_path, 0)
            
            if self.template is not None:
                self.template_processed = cv2.morphologyEx(self.template, cv2.MORPH_CLOSE, self.kernel)
                self.template_processed = cv2.resize(self.template_processed, (150, 150), interpolation=cv2.INTER_CUBIC)
                logging.info(f"Wheel template loaded: {template_path}")
            else:
                logging.warning(f"Failed to read template: {template_path}")
        else:
            if self.use_template:
                logging.warning(f"Template file {template_path} not found!")


    def ssd(self, img1):
        if self.template_processed is None:
            return 0
        
        try:
            dstt1 = cv2.morphologyEx(img1, cv2.MORPH_CLOSE, self.kernel)
            dstt1 = cv2.resize(dstt1, (150, 150), interpolation=cv2.INTER_CUBIC)
            diff = self.template_processed.astype(np.int32) - dstt1.astype(np.int32)
            diff = diff ** 2
            
            return np.sum(diff)
        
        except Exception as e:
            logging.error(f"SSD comparison error: {e}")
            return 0


    def is_circular_shape(self, crop_img):
        try:
            _, binary = cv2.threshold(crop_img, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
            
            contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if not contours:
                return False
            
            largest_contour = max(contours, key=cv2.contourArea)
            area = cv2.contourArea(largest_contour)
            
            if area < 100:  
                return False
            
            perimeter = cv2.arcLength(largest_contour, True)
            if perimeter == 0:
                return False
            
            circularity = 4 * np.pi * area / (perimeter * perimeter)
            
            return 0.4 < circularity < 1.2
            
        except Exception as e:
            logging.debug(f"Error in circularity check: {e}")
            return False


    def filter(self, circles, gray, frame_shape=None):
        wheels = []
        
        try:
            if circles is None:
                return wheels

            for i in circles[0, :]:
                x, y, r = int(i[0]), int(i[1]), int(i[2])
                
                if r < self.min_radius or r > self.max_radius:
                    continue
                
                if self.mode == 'file':
                    if y < self.min_y or y > self.max_y:
                        continue
                
                rectX = x - r
                rectY = y - r

                if rectX < 0 or rectY < 0:
                    continue
                
                if rectX + 2 * r > gray.shape[1] or rectY + 2 * r > gray.shape[0]:
                    continue

                crop_img = gray[rectY:(rectY + 2 * r), rectX:(rectX + 2 * r)]
                
                if crop_img.size == 0:
                    continue

                try:
                    (_, final_box) = cv2.threshold(crop_img, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
                    
                    is_wheel = False
                    
                    if self.mode == 'camera':
                        if self.is_circular_shape(final_box):
                            is_wheel = True
                    else:
                        if self.use_template:
                            ssd_value = self.ssd(final_box)
                            if ssd_value >= self.ssd_threshold:
                                is_wheel = True
                        else:
                            is_wheel = self.is_circular_shape(final_box)
                    
                    if is_wheel:
                        wheels.append((i[0], i[1], i[2]))
                        
                except Exception as e:
                    logging.debug(f"Error processing circle at ({x}, {y}), r={r}: {e}")
                    continue

            wheels = sorted(wheels, key=lambda x: x[0], reverse=True)
            
        except Exception as e:
            logging.error(f"Wheel filtering error: {e}")

        return wheels