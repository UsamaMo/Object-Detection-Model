# CP467-Project
## Team Members: Usama, Duc Minh Nguyen, Quang Quynh Anh Lam

Below, I will list a general overview of the step-by-step instructions we have to follow for this project.


## 1. Collect and Prepare Data:
Take 1 scene picture with 15-20 different objects
Take 20-30 shots of that 1 scene
just change angle so that atleast it overlaps with one more image

declutter , finind interest points
Take individual pictures of each object to compare with object in scene (Harris, Sift)

object dataset - individual pictures of each object
scene dataset - (20-30) shots for the different views

## 2. Feature Detection: (SIFT/Harris Corner)
What to do: Find unique points on the objects that can help to identify them.
How to do it: Use OpenCV's feature detection functions to locate and describe important points on each image.
Output: Images showing important points on the objects, saved in the “Keypoints” folder.


## 3. Feature Matching: (SIFT/Harris Corner)
What to do: Compare points on the object images with those in the scene images to find where they match.
How to do it: Use OpenCV's matching functions to find and pair up similar points between the object and scene images.
Output: Images showing lines connecting points that match up, saved in the “Matches” folder.

## 4. Object Detection in Scenes: 
What to do: Confirm which objects from your object set are in the scene images.
How to do it: Based on where the matching points are, figure out where each object is in the scene and draw a box around it.
Output: Scene images with objects outlined and named, saved in the “Detected_Objects” folder.

## 5. Image stitching: 
What to do: Merge several scene images into one large image.
How to do it: Use OpenCV's stitching functions to connect the images at overlapping points to create a panoramic view.
Output: A single, large, continuous image created from many smaller ones, saved as “Stitched_Scene”.

## 6. Evaluation:
What to do: Check how accurately your program found and identified the objects.
How to do it: Tally the objects your program detected correctly, missed, incorrectly identified, and correctly left out. Then calculate the precision, recall, F1-score, and accuracy.
Output: A table with these statistics for each scene image.

## 7. Submission:
What to do: Combine all the pieces of code from the different tasks into a coherent project. Turn in your completed project.
How to do it: Follow the submission guidelines provided by your course instructor or the syllabus.
Output: Your project is submitted and awaiting grading.



Relevant Code Below:

