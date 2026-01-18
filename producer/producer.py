import os
import cv2
import time
import pickle
import numpy as np
from kafka import KafkaProducer

# ---------- STREAM CONFIGURATION ----------
STREAM_ID = os.environ.get("STREAM_ID", "camera1")

KAFKA_BROKERS = os.environ.get(
    "KAFKA_BROKERS",
    "b-1.videopipeline.mgvvii.c2.kafka.eu-north-1.amazonaws.com:9094,"
    "b-2.videopipeline.mgvvii.c2.kafka.eu-north-1.amazonaws.com:9094,"
    "b-3.videopipeline.mgvvii.c2.kafka.eu-north-1.amazonaws.com:9094"
).split(",")

TOPIC = os.environ.get("KAFKA_TOPIC", "video.camera1")
RTSP_URL = os.environ.get("RTSP_URL", "rtsp://localhost:8554/cam")
BATCH_SIZE = int(os.environ.get("BATCH_SIZE", "25"))

# 2. Update the producer initialization
producer = KafkaProducer(
    bootstrap_servers=KAFKA_BROKERS,
    security_protocol="SSL",
    value_serializer=lambda v: pickle.dumps(v),
    max_request_size=10485760,
)

def get_rtsp_stream(url):
    print(f"Connecting to RTSP: {url}...")
    cap = cv2.VideoCapture(url)
    # Optimization: Set buffer size to minimize latency
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
            # Ignore the noise and wait for the next successful frame
            continue
        
        # If stream breaks, attempt to reconnect
        if not ret:
            print("Stream interrupted. Reconnecting...")
            cap.release()
            time.sleep(2)
            cap = get_rtsp_stream(RTSP_URL)
            continue

        # Encode frame to JPEG to reduce network load
        success, encoded_frame = cv2.imencode(".jpg", frame)
        if not success:
            continue

        batch.append(encoded_frame.tobytes())

        # When we reach 25 frames, send the batch
        if len(batch) == BATCH_SIZE:
            try:
                # send() is asynchronous
                future = producer.send(TOPIC, batch)
                # We use flush() to ensure the batch is sent before continuing
                producer.flush() 
                
                payload_size = sum(len(f) for f in batch)
                print(f"✅ Sent batch: {BATCH_SIZE} frames | Total size: {payload_size // 1024} KB")
                
                batch = [] # Clear the batch
            except Exception as e:
                print(f"❌ Kafka Error: {e}")

except KeyboardInterrupt:
    print("Stopping producer...")
finally:
    cap.release()
    producer.close()
