import time
import cv2


cam = "http://10.97.220.236:8080/video"
# cam = 0

def runCam():
    # 1. Initialize webcam (0 is usually the default internal camera)
    cap = cv2.VideoCapture(cam)

    if not cap.isOpened():
        print("Error: Could not open camera.")
        return

    # Set frame dimensions (optional)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    prev_frame_time = 0

    print("Processing video stream. Press 'q' on the image window to exit.")

    while True:
        # 2. Read frame-by-frame
        ret, frame = cap.read()
        if not ret:
            print("Error: Failed to grab frame.")
            break


        # 6. Display output window
        cv2.imshow("OpenCV Task - Grayscale Live Feed", frame)

        # 7. Press 'q' on your keyboard to quit
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    # Release hardware and close all OpenCV windows
    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    runCam()