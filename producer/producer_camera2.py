import cv2
import time
import pickle
import numpy as np
from kafka import KafkaProducer

# ---------- CAMERA 2 CONFIGURATION ----------
STREAM_ID = "camera2"

KAFKA_BROKERS = [
    "b-1.videopipeline.mgvvii.c2.kafka.eu-north-1.amazonaws.com:9094",
    "b-2.videopipeline.mgvvii.c2.kafka.eu-north-1.amazonaws.com:9094",
    "b-3.videopipeline.mgvvii.c2.kafka.eu-north-1.amazonaws.com:9094",
]

TOPIC = "video.camera2"
RTSP_URL = "rtsp://localhost:8554/cam2"
BATCH_SIZE = 25

# ---------- KAFKA PRODUCER ----------
producer = KafkaProducer(
    bootstrap_servers=KAFKA_BROKERS,
    security_protocol="SSL",
    value_serializer=lambda v: pickle.dumps(v),
    max_request_size=10485760,
)

def get_rtsp_stream(url):
    print(f"Connecting to RTSP: {url}...")
    cap = cv2.VideoCapture(url)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 3)
    return cap

cap = get_rtsp_stream(RTSP_URL)
batch = []

print(f"Starting RTSP → Kafka producer for {STREAM_ID}")

try:
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    while True:
        ret, frame = cap.read()
        if not ret or frame is None:
            continue

        if not ret:
            print("Stream interrupted. Reconnecting...")
            cap.release()
            time.sleep(2)
            cap = get_rtsp_stream(RTSP_URL)
            continue

        success, encoded_frame = cv2.imencode(".jpg", frame)
        if not success:
            continue

        batch.append(encoded_frame.tobytes())

        if len(batch) == BATCH_SIZE:
            try:
                future = producer.send(TOPIC, batch)
                producer.flush()

                payload_size = sum(len(f) for f in batch)
                print(f"✅ Sent batch: {BATCH_SIZE} frames | Total size: {payload_size // 1024} KB")

                batch = []
            except Exception as e:
                print(f"❌ Kafka Error: {e}")

except KeyboardInterrupt:
    print("Stopping producer...")
finally:
    cap.release()
    producer.close()
