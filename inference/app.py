from fastapi import FastAPI
import time
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
 
logger = logging.getLogger(__name__)

app = FastAPI()

@app.post("/infer")
def infer(payload: dict):
    start = time.time()

    frames = payload.get("frames", [])
    logger.info(f"Received inference request with {len(frames)} frames")

    results = []

    for i in range(len(frames)):
        logger.info(f"Running inference on frame {i}")
        results.append({
            "frame_id": i,
            "boxes": [
                {"x": 50, "y": 50, "w": 100, "h": 150, "label": "person"}
            ]
        })

    elapsed = int((time.time() - start) * 1000)
    logger.info(f"Inference completed in {elapsed} ms")

    return {"results": results}

