import cv2
import numpy as np
from moviepy.editor import VideoFileClip, AudioFileClip
import tempfile
import os

def inpaint_frame_opencv(frame, mask, roi=None):
    """
    Apply OpenCV inpainting to a single frame.
    frame: numpy array (RGB)
    mask: numpy array (Grayscale/Single channel), where 255 is the area to inpaint.
    roi: tuple (x, y, w, h) of the bounding box to process. If None, process full frame.
    """
    # Create a writable copy of the frame
    frame = frame.copy()

    # Ensure mask is uint8
    if mask.dtype != np.uint8:
        mask = mask.astype(np.uint8)
    
    # Dilation allows the mask to cover the watermark edges better
    kernel = np.ones((3,3), np.uint8) # Reduced kernel size slightly for speed
    
    if roi:
        x, y, w, h = roi
        # Add padding to ROI to ensure context for inpainting
        pad = 5
        h_src, w_src = frame.shape[:2]
        
        x1 = max(0, x - pad)
        y1 = max(0, y - pad)
        x2 = min(w_src, x + w + pad)
        y2 = min(h_src, y + h + pad)
        
        # Crop
        frame_roi = frame[y1:y2, x1:x2]
        mask_roi = mask[y1:y2, x1:x2]
        
        # Dilate mask only in ROI
        dilated_mask_roi = cv2.dilate(mask_roi, kernel, iterations=1)
        
        # Inpaint ROI
        inpainted_roi = cv2.inpaint(frame_roi, dilated_mask_roi, 3, cv2.INPAINT_TELEA)
        
        # Copy back
        frame[y1:y2, x1:x2] = inpainted_roi
        return frame
    else:
        dilated_mask = cv2.dilate(mask, kernel, iterations=1)
        inpainted = cv2.inpaint(frame, dilated_mask, 3, cv2.INPAINT_TELEA)
        return inpainted

from proglog import ProgressBarLogger

class MyBarLogger(ProgressBarLogger):
    def __init__(self, callback):
        super().__init__()
        self.progress_notifier = callback

    def bars_callback(self, bar, attr, value, old_value=None):
        # Only track the 't' (time) bar which represents frame processing
        if bar == 't':
            percentage = (value / self.bars[bar]['total'])
            if self.progress_notifier:
                self.progress_notifier(percentage)

def process_video_with_mask(input_path, output_path, mask_image, progress_callback=None):
    """
    Process video frame by frame.
    input_path: Path to input video.
    output_path: Path to save output video.
    mask_image: Boolean or 0-255 numpy array defining the region to remove.
               Must match video aspect ratio/size roughly, or be resized.
    progress_callback: Function that accepts a float (0.0 to 1.0) for progress updates.
    """
    try:
        # Load video
        clip = VideoFileClip(input_path)
        
        # Prepare mask
        # Resize mask to match video dimensions if needed
        mask_h, mask_w = mask_image.shape[:2]
        video_w, video_h = clip.size
        
        # Ensure mask matches video size
        if (mask_w != video_w) or (mask_h != video_h):
             # Resize mask using OpenCV (handling the boolean/grayscale properly)
             mask_resized = cv2.resize(mask_image.astype(np.uint8), (video_w, video_h), interpolation=cv2.INTER_NEAREST)
        else:
            mask_resized = mask_image.astype(np.uint8)

        # Threshold to ensure binary mask for inpainting (0 or 255)
        # Assuming input mask might be anti-aliased or have alpha
        _, mask_binary = cv2.threshold(mask_resized, 127, 255, cv2.THRESH_BINARY)
        
        # Optimization: Calculate Bounding Box (ROI) of the mask
        # This allows us to inpaint ONLY the watermark area, not the whole 4K frame.
        points = cv2.findNonZero(mask_binary)
        roi = None
        if points is not None:
            roi = cv2.boundingRect(points) # (x, y, w, h)
        
        # Define the processing function for MoviePy
        def process_frame(get_frame, t):
            frame = get_frame(t)
            # frame is HxWx3 (RGB)
            # If no mask (empty), return original
            if roi is None:
                 return frame
            return inpaint_frame_opencv(frame, mask_binary, roi=roi)

        # Apply processing
        # We use fl_image which applies the function to every frame
        # We need to wrap our simple inpaint_frame to match fl_image signature which is f(image)
        # Note: We pass the mask_binary and ROI captured in closure
        new_clip = clip.fl_image(lambda img: inpaint_frame_opencv(img, mask_binary, roi=roi) if roi else img)
        
        # Setup Logger
        logger = None
        if progress_callback:
            logger = MyBarLogger(progress_callback)
        else:
            logger = 'bar'

        # Write output file
        # codec='libx264' is standard for mp4. audio_codec='aac' for audio.
        # preset='ultrafast' trades compression for speed. 'medium' is default.
        # threads=4 to use multi-threading for encoding
        new_clip.write_videofile(output_path, codec='libx264', audio_codec='aac', logger=logger, preset='faster', threads=4)
        
        clip.close()
        new_clip.close()
        return True, "Success"
        
    except Exception as e:
        return False, str(e)
