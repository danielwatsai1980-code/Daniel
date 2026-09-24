import cv2
from ultralytics import YOLO

cam = "http://10.16.231.21:8080/video"



def run_segmentation_with_labels():
    model = YOLO("yolo26n-seg.pt")

    cap = cv2.VideoCapture(cam)

    if not cap.isOpened():
        print("Error: Could not open camera.")
        return

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        results = model(frame, stream=True)

        for r in results:
            annotated_frame = r.plot(boxes=True, labels=True)

        cv2.imshow("Segmentation + Class Labels", annotated_frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    run_segmentation_with_labels()