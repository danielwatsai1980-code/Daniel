import cv2
from ultralytics import YOLO

CAM_SOURCES = [
    "http://10.16.231.21:8080/video",
    "http://192.168.0.5:81/stream",
    0,
]


def open_camera():
    for source in CAM_SOURCES:
        cap = cv2.VideoCapture(source)
        if cap.isOpened():
            print(f"Camera opened from: {source}")
            return cap
        print(f"Failed to open camera source: {source}")
    return None


def run_segmentation_with_labels():
    model = YOLO("yolov8n.pt")
    cap = open_camera()

    if cap is None:
        print("Error: Could not open any camera.")
        return

    while True:
        ret, frame = cap.read()
        if not ret or frame is None:
            print("Error: Failed to grab frame.")
            break

        results = model(frame, stream=True)
        annotated_frame = frame

        for r in results:
            annotated_frame = r.plot(boxes=True, labels=True)

        cv2.imshow("YOLO Detection", annotated_frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    run_segmentation_with_labels()