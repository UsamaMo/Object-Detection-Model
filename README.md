# CP467-Project
## Team Members: Usama, Daniel, Ahnya

Below, I will list a general overview of the step-by-step instructions we have to follow for this project.


1. Prepare Your Environment:
What to do: Set up the software and workspace you'll need.
How to do it: Install Python and OpenCV, create a virtual environment, and install any additional libraries you need (like NumPy) using a requirements.txt file.
Output: A ready-to-use programming environment on your computer.


2. Collect and Prepare Data:
What to do: Get the images you need to work with.
How to do it: Set up a physical scene with objects and take many pictures from different angles. Make sure some parts of the scene overlap in different pictures. Also, take clear pictures of each object by itself.
Output: Two sets of images: one set of the scene (S1, S2, ..., Sn) and one set of objects (O1, O2, ..., Om).

3. Feature Detection:
What to do: Find unique points on the objects that can help to identify them.
How to do it: Use OpenCV's feature detection functions to locate and describe important points on each image.
Output: Images showing important points on the objects, saved in the “Keypoints” folder.


4 Feature Matching:
What to do: Compare points on the object images with those in the scene images to find where they match.
How to do it: Use OpenCV's matching functions to find and pair up similar points between the object and scene images.
Output: Images showing lines connecting points that match up, saved in the “Matches” folder.

5. Object Detection in Scenes:
What to do: Confirm which objects from your object set are in the scene images.
How to do it: Based on where the matching points are, figure out where each object is in the scene and draw a box around it.
Output: Scene images with objects outlined and named, saved in the “Detected_Objects” folder.

6. Image Stitching:
What to do: Merge several scene images into one large image.
How to do it: Use OpenCV's stitching functions to connect the images at overlapping points to create a panoramic view.
Output: A single, large, continuous image created from many smaller ones, saved as “Stitched_Scene”.

7. Evaluation:
What to do: Check how accurately your program found and identified the objects.
How to do it: Tally the objects your program detected correctly, missed, incorrectly identified, and correctly left out. Then calculate the precision, recall, F1-score, and accuracy.
Output: A table with these statistics for each scene image.

8. Submission:
What to do: Combine all the pieces of code from the different tasks into a coherent project. Turn in your completed project.
How to do it: Follow the submission guidelines provided by your course instructor or the syllabus.
Output: Your project is submitted and awaiting grading.
