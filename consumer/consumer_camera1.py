import time
import pickle
import logging
import boto3
import requests
import cv2
import numpy as np

from confluent_kafka import Consumer, TopicPartition
from prometheus_client import Gauge, start_http_server

# ---------------- CAMERA 1 CONFIGURATION ----------------

STREAM_ID = "camera1"

KAFKA_BROKERS = (
    "b-1.videopipeline.mgvvii.c2.kafka.eu-north-1.amazonaws.com:9094,"
    "b-2.videopipeline.mgvvii.c2.kafka.eu-north-1.amazonaws.com:9094,"
    "b-3.videopipeline.mgvvii.c2.kafka.eu-north-1.amazonaws.com:9094"
)

KAFKA_TOPIC = "video.camera1"
KAFKA_GROUP_ID = "video-consumer-group-camera1"

INFERENCE_URL = (
    "http://ab85a96ee32bb4edb981d3dd99f5d9c3-166869099."
    "eu-north-1.elb.amazonaws.com/infer"
)

S3_BUCKET = "optifye-inference-results"
S3_PREFIX = "annotated"
METRICS_PORT = 8001

# ---------------- LOGGING ----------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("consumer")

# ---------------- AWS CLIENT ----------------

s3 = boto3.client("s3")

# ---------------- PROMETHEUS ----------------

start_http_server(METRICS_PORT)

kafka_lag_gauge = Gauge(
    "kafka_consumer_lag",
    "Kafka consumer lag (high watermark - committed offset)",
    ["stream_id"]
)

# ---------------- KAFKA CONSUMER ----------------

consumer_conf = {
    "bootstrap.servers": KAFKA_BROKERS,
    "security.protocol": "SSL",
    "group.id": KAFKA_GROUP_ID,
    "auto.offset.reset": "latest",
    "enable.auto.commit": True
}

consumer = Consumer(consumer_conf)
consumer.subscribe([KAFKA_TOPIC])

logger.info(f"🟢 Confluent Kafka consumer started for {STREAM_ID}")

# ---------------- HELPERS ----------------

def annotate_frame(frame_bytes, box):
    img_array = np.frombuffer(frame_bytes, np.uint8)
    frame = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

    x, y, w, h = box["x"], box["y"], box["w"], box["h"]
    label = box["label"]

    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
    cv2.putText(
        frame,
        label,
        (x, y - 10),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (0, 255, 0),
        2
    )

    success, encoded = cv2.imencode(".jpg", frame)
    if not success:
        raise RuntimeError("Failed to encode annotated frame")

    return encoded.tobytes()


def upload_to_s3(image_bytes, key):
    s3.put_object(
        Bucket=S3_BUCKET,
        Key=key,
        Body=image_bytes,
        ContentType="image/jpeg"
    )


def compute_kafka_lag(consumer, msg):
    tp = TopicPartition(msg.topic(), msg.partition())

    low, high = consumer.get_watermark_offsets(tp, timeout=1.0)
    committed = consumer.committed([tp], timeout=1.0)[0].offset

    if committed < 0:
        return high

    return max(high - committed, 0)


# ---------------- MAIN LOOP ----------------

try:
    while True:
        msg = consumer.poll(timeout=1.0)

        if msg is None:
            continue

        if msg.error():
            logger.error(f"Kafka error: {msg.error()}")
            continue

        batch = pickle.loads(msg.value())
        logger.info(f"📦 Received batch with {len(batch)} frames")

        # ----- Kafka lag -----
        lag = compute_kafka_lag(consumer, msg)
        kafka_lag_gauge.labels(stream_id=STREAM_ID).set(lag)
        logger.info(f"📊 Kafka lag for {STREAM_ID}: {lag}")

        # ----- Inference -----
        response = requests.post(
            INFERENCE_URL,
            json={"frames": ["dummy"] * len(batch)},
            timeout=5
        )
        response.raise_for_status()

        results = response.json()["results"]

        # ----- Annotate first frame only -----
        box = results[0]["boxes"][0]
        annotated = annotate_frame(batch[0], box)

        timestamp = int(time.time())
        s3_key = f"{S3_PREFIX}/frame_{timestamp}.jpg"

        upload_to_s3(annotated, s3_key)
        logger.info(f"✅ Uploaded annotated frame to s3://{S3_BUCKET}/{s3_key}")

except KeyboardInterrupt:
    logger.info("Stopping consumer")

finally:
    consumer.close()
