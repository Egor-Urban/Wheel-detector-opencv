# WheelCounterApp.py

import cv2
import logging
import traceback

from datetime import datetime
from pathlib import Path

from FrameProcessor import FrameProcessor
from WheelFilter import WheelFilter


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


class WheelCounterApp:
    def __init__(self, video_source, output_path=None, mode='file'):
        try:
            self.mode = mode
            self.cap = cv2.VideoCapture(video_source)
            
            if not self.cap.isOpened():
                raise ValueError(f"Failed to open video source: {video_source}")
            
            if mode == 'file':
                logging.info(f"Video file opened: {video_source}")
            else:
                logging.info(f"Camera opened: ID {video_source}")

            self.processor = FrameProcessor(mode=mode)
            self.filter = WheelFilter(mode=mode)
            self.frame_count = 0

            w = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            h = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = int(self.cap.get(cv2.CAP_PROP_FPS))
            
            if fps <= 0:
                fps = 25
            
            if mode == 'file':
                total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
                logging.info(f"Video: {w}x{h}, {fps} FPS, {total_frames} frames")
            else:
                logging.info(f"Camera: {w}x{h}, {fps} FPS (estimated)")

            self.out = None
            if output_path:
                fourcc = cv2.VideoWriter_fourcc('M', 'J', 'P', 'G')
                self.out = cv2.VideoWriter(output_path, fourcc, fps, (w, h))
                
                if not self.out.isOpened():
                    logging.warning(f"Failed to create output file: {output_path}")
                    self.out = None
                else:
                    logging.info(f"Output will be saved to: {output_path}")

            self.wheel_log = []
            
            self.fps_start_time = datetime.now()
            self.fps_frame_count = 0
            self.current_fps = 0
            
            self.show_debug = False

        except Exception as e:
            logging.error(f"App initialization error: {e}")
            raise
        

    def draw_wheels(self, img, wheels, circles_count=0):
        for x, y, r in wheels:
            cv2.circle(img, (x, y), r, (0, 0, 255), 2)
            cv2.circle(img, (x, y), 3, (0, 255, 0), -1)

        text = f"Wheels: {len(wheels)}"
        font = cv2.FONT_HERSHEY_SIMPLEX
        
        font_scale = 1.5
        thickness = 2

        (text_width, text_height), baseline = cv2.getTextSize(text, font, font_scale, thickness)
        cv2.rectangle(img, (10, 10), (30 + text_width, 50 + text_height), (0, 0, 0), -1)
        cv2.putText(img, text, (20, 50), font, font_scale, (0, 255, 0), thickness)

        if self.mode == 'camera':
            circles_text = f"Circles: {circles_count}"
            (c_width, c_height), c_baseline = cv2.getTextSize(circles_text, font, 1, 2)
            cv2.rectangle(img, (10, 70), (30 + c_width, 105 + c_height), (0, 0, 0), -1)
            cv2.putText(img, circles_text, (20, 105), font, 1, (255, 255, 0), 2)

        if self.mode == 'camera':
            fps_text = f"FPS: {self.current_fps:.1f}"
            (fps_w, fps_h), fps_bl = cv2.getTextSize(fps_text, font, 1, 2)
            cv2.rectangle(img, (10, 120), (30 + fps_w, 155 + fps_h), (0, 0, 0), -1)
            cv2.putText(img, fps_text, (20, 155), font, 1, (255, 0, 255), 2)

        mode_text = f"Mode: {'FILE' if self.mode == 'file' else 'CAMERA'} | Q-quit"
        if self.mode == 'camera':
            mode_text += " | D-debug"
        cv2.putText(img, mode_text, (20, img.shape[0] - 20), font, 0.7, (200, 200, 200), 2)


    def calculate_fps(self):
        self.fps_frame_count += 1
        
        if self.fps_frame_count >= 10:
            elapsed = (datetime.now() - self.fps_start_time).total_seconds()
            if elapsed > 0:
                self.current_fps = self.fps_frame_count / elapsed
            
            self.fps_start_time = datetime.now()
            self.fps_frame_count = 0


    def run(self):
        logging.info(f"Starting video processing in {self.mode} mode...")
        
        if self.mode == 'camera':
            logging.info("Camera mode: Press 'D' to toggle debug view, 'Q' to quit")
        
        try:
            while self.cap.isOpened():
                ret, frame = self.cap.read()
                if not ret:
                    if self.mode == 'file':
                        logging.info("End of video file reached")
                        break
                    else:
                        logging.warning("Failed to read frame from camera")
                        continue

                self.frame_count += 1
                
                gray, edges = self.processor.preprocess(frame)
                if gray is None or edges is None:
                    continue

                circles = self.processor.detect_circles(edges)
                circles_count = len(circles[0]) if circles is not None else 0
                wheels = self.filter.filter(circles, gray, frame.shape) if circles is not None else []

                self.wheel_log.append((self.frame_count, wheels))
                if wheels and self.mode == 'camera':
                    logging.info(f"Frame {self.frame_count}: {len(wheels)} wheels found")

                display_frame = frame.copy()
                
                if self.show_debug and circles is not None and self.mode == 'camera':
                    for i in circles[0, :]:
                        x, y, r = int(i[0]), int(i[1]), int(i[2])
                        cv2.circle(display_frame, (x, y), r, (255, 0, 0), 1)
                        cv2.putText(display_frame, f"r:{r}", (x-20, y-r-5), 
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 0, 0), 1)
                
                self.draw_wheels(display_frame, wheels, circles_count)
                
                if self.out:
                    self.out.write(display_frame)
                
                if self.mode == 'camera':
                    self.calculate_fps()
                
                cv2.imshow("Wheel Detection", display_frame)

                if self.mode == 'file' and self.frame_count % 30 == 0:
                    logging.info(f"Processed frames: {self.frame_count}")

                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    logging.info("Interrupted by user (pressed 'q')")
                    break
                elif key == ord('d') and self.mode == 'camera':
                    self.show_debug = not self.show_debug
                    logging.info(f"Debug mode: {'ON' if self.show_debug else 'OFF'}")

        except Exception as e:
            logging.error(f"Error during video processing: {e}")
            logging.error(traceback.format_exc())
            
        finally:
            self.cleanup()


    def cleanup(self):
        self.cap.release()
        
        if self.out:
            self.out.release()
            
        cv2.destroyAllWindows()
        
        logging.info(f"Processing finished. Total frames processed: {self.frame_count}")

        total_wheels = sum(len(w[1]) for w in self.wheel_log)
        avg_wheels = total_wheels / self.frame_count if self.frame_count > 0 else 0
        
        logging.info(f"Total wheels detected: {total_wheels}")
        logging.info(f"Average wheels per frame: {avg_wheels:.2f}")
        logging.info(f"Detailed per-frame log saved in {log_file}")