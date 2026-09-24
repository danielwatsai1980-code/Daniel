import cv2
from ultralytics import YOLO


def run_yolo26_color_webcam():
    # Load the latest lightweight YOLO26 model
    model = YOLO("yolo26n.pt")

    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Error: Could not open camera.")
        return

    print("Running YOLO26 detection in full color. Press 'q' to exit.")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Run inference directly on the original full-color frame
        results = model(frame, stream=True)

        # Draw bounding boxes and class labels directly on the color image
        for r in results:
            annotated_frame = r.plot()

        cv2.imshow("YOLO26 Detection - Full Color", annotated_frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    run_yolo26_color_webcam()