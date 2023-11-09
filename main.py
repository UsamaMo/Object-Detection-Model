import cv2
import numpy as np



#-----------------------------------------------------------------------------------------------------------
#THIS IS JUST STARTER CODE AND SAMPLE CODE  TO GIVE US A GENERAL IDEA OF WHAT TO DO
#-----------------------------------------------------------------------------------------------------------


# Function to read images and detect features
def detect_and_display_features(image_paths):
    # Read images and detect features
    for path in image_paths:
        image = cv2.imread(path)
        keypoints, descriptors = detect_features(image)
        # Display keypoints for each image
        display_keypoints(image, keypoints, path)

# Function to detect features using a chosen algorithm like SIFT
def detect_features(image):
    sift = cv2.SIFT_create()
    keypoints, descriptors = sift.detectAndCompute(image, None)
    return keypoints, descriptors

# Function to display keypoints on images and save them
def display_keypoints(image, keypoints, image_path):
    keypoints_image = cv2.drawKeypoints(image, keypoints, None)
    cv2.imwrite(f'{image_path}_keypoints.png', keypoints_image)

# TODO: Define functions for feature matching, image stitching, and evaluation metrics

# Main execution
if __name__ == "__main__":
    # List of image paths
    scene_image_paths = ['path_to_scene1', 'path_to_scene2', ...]
    object_image_paths = ['path_to_object1', 'path_to_object2', ...]
    
    # Detect and display features
    detect_and_display_features(scene_image_paths)
    detect_and_display_features(object_image_paths)
    
    # More code to follow for matching, stitching, and evaluation
