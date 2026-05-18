import cv2
import numpy as np

def crop_solar_panel(img_array):
    """
    Takes an RGB numpy array (image), finds the largest rectangular contour (the panel),
    and crops it perfectly using a perspective transform.
    Returns (cropped_array, crop_status_string).
    """
    try:
        # Convert to grayscale
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        
        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Thresholding (EL panels have distinct dark backgrounds)
        _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Find contours
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return img_array, "Attempted — Failed"
            
        # Get the largest contour by area
        largest_contour = max(contours, key=cv2.contourArea)
        
        # Ensure it's large enough to actually be the panel (e.g. > 10% of image area)
        h, w = img_array.shape[:2]
        img_area = h * w
        if cv2.contourArea(largest_contour) < 0.1 * img_area:
            return img_array, "Attempted — Failed"
            
        # Get the minimum area bounding rectangle
        rect = cv2.minAreaRect(largest_contour)
        box = cv2.boxPoints(rect)
        box = np.int0(box)
        
        # Source points
        src_pts = box.astype("float32")
        
        # Function to order points: top-left, top-right, bottom-right, bottom-left
        def order_points(pts):
            rect = np.zeros((4, 2), dtype="float32")
            s = pts.sum(axis=1)
            rect[0] = pts[np.argmin(s)]
            rect[2] = pts[np.argmax(s)]
            diff = np.diff(pts, axis=1)
            rect[1] = pts[np.argmin(diff)]
            rect[3] = pts[np.argmax(diff)]
            return rect

        src_pts_ordered = order_points(src_pts)
        
        # Determine the width and height of the new image
        (tl, tr, br, bl) = src_pts_ordered
        widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
        widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
        maxWidth = max(int(widthA), int(widthB))
        
        heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
        heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
        maxHeight = max(int(heightA), int(heightB))
        
        dst_pts = np.array([
            [0, 0],
            [maxWidth - 1, 0],
            [maxWidth - 1, maxHeight - 1],
            [0, maxHeight - 1]
        ], dtype="float32")
        
        # Apply the perspective transformation
        M = cv2.getPerspectiveTransform(src_pts_ordered, dst_pts)
        warped = cv2.warpPerspective(img_array, M, (maxWidth, maxHeight))
        
        # Check if the area actually shrunk meaningfully
        was_cropped = (maxWidth * maxHeight) < (0.95 * img_area)
        
        crop_status = "Needed & Done" if was_cropped else "Not Needed"
        return warped, crop_status
        
    except Exception as e:
        print(f"Auto-crop failed, using original image: {e}")
        return img_array, "Attempted — Failed"
