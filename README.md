# Optifye Video Processing Pipeline

An end-to-end, scalable video processing pipeline built using Kafka and Kubernetes for real-time inference.

---

## Architecture Overview

- Video frames are produced to **Kafka (AWS MSK)**
- A **Kafka consumer** batches frames and sends them to an inference service
- The **Inference service** runs on **Amazon EKS**
- Annotated frames are uploaded to **Amazon S3**
- Inference pods **autoscale based on Kafka consumer lag** using **Prometheus + KEDA**

---

## Tech Stack

- AWS MSK (Kafka)
- Amazon EKS
- Docker
- Prometheus
- KEDA
- GitHub Actions (CI/CD)
- Amazon ECR & S3

---

## Autoscaling

Inference deployments automatically scale based on **Kafka consumer lag** exposed as a Prometheus metric.  
KEDA monitors this metric and triggers scaling when lag crosses a configured threshold.

---

## CI/CD

CI/CD is implemented using **GitHub Actions** with **OIDC-based AWS authentication**:

- Builds inference Docker image
- Pushes image to Amazon ECR
- Performs rolling updates on EKS

No static AWS credentials are stored in the repository.

---

## Repository Structure
consumer/     # Kafka consumer
producer/     # Kafka producer
inference/    # Inference service (EKS)
k8s/          # Kubernetes manifests
msk-infra/    # Kafka infrastructure


---

## Key Highlights

- Stateless, scalable inference service
- Autoscaling driven by real workload metrics
- Production-grade CI/CD pipeline
- Secure, cloud-native authentication

