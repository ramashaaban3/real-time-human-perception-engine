# Real-Time Human Perception Engine

## Overview

Real-Time Human Perception Engine is a microservice-based real-time perception and decision-making system developed for human-aware robotic interaction scenarios. The project combines computer vision, rule-based reasoning, optional Large Language Model (LLM) integration, and orchestration services within a Dockerized architecture.

The system receives image or video frames, detects humans using YOLOv8, analyzes scene conditions, and generates high-level interaction decisions such as greeting users, requesting alignment, or warning about multiple people in the scene.

The architecture is designed to be modular, scalable, and suitable for real-time robotic perception pipelines.

---

# System Architecture

The project consists of three primary microservices:

1. Perception Service
2. Reasoning Service
3. Orchestrator Service

### Pipeline Flow

```text
Input Frame / Video
        ↓
Orchestrator Service
        ↓
Perception Service (YOLOv8)
        ↓
Perception JSON Output
        ↓
Reasoning Service
        ↓
Rules / LLM Decision Layer
        ↓
Decision JSON Output
```

---

# Features

* Real-time human detection using YOLOv8
* Multi-person scene analysis
* Horizontal position estimation (left / center / right)
* Stabilized decision generation
* Cooldown-based action control
* Rule-based reasoning engine
* Optional LLM integration
* Dockerized microservice architecture
* SQLite event logging
* Automated evaluation pipeline
* End-to-end orchestrator service
* Swagger/OpenAPI documentation

---

# Technologies Used

| Technology              | Purpose                     |
| ----------------------- | --------------------------- |
| Python 3.11             | Core development language   |
| FastAPI                 | REST API services           |
| YOLOv8                  | Human detection             |
| OpenCV                  | Image processing            |
| Docker & Docker Compose | Containerization            |
| SQLite                  | Event logging               |
| Pydantic                | API schema validation       |
| OpenAI API              | Optional LLM reasoning      |
| Requests                | Inter-service communication |

---

# Project Structure

```text
real-time-human-perception-engine/
│
├── perception_service/
│   ├── app/
│   ├── Dockerfile
│   └── requirements.txt
│
├── reasoning_service/
│   ├── app/
│   ├── logs/
│   ├── Dockerfile
│   └── requirements.txt
│
├── orchestrator/
│   ├── app/
│   ├── Dockerfile
│   └── requirements.txt
│
├── shared/
│   └── schemas.py
│
├── tests/
│   ├── test_cases.json
│   ├── results.csv
│   ├── summary.txt
│   └── run_tests.py
│
├── datasets/
│   ├── tests/
│   └── demo_video.mp4
│
├── docker-compose.yml
├── README.md
└── .gitignore
```

---

# Perception Service

The Perception Service is responsible for low-level scene understanding.

### Responsibilities

* Receiving image frames
* Running YOLOv8 inference
* Detecting people in the scene
* Calculating confidence scores
* Estimating horizontal position
* Returning structured JSON outputs

### Endpoint

```text
POST /v1/perception/frame
```

### Example Response

```json
{
  "people_count": 1,
  "primary_person": {
    "detected": true,
    "confidence": 0.94,
    "position": "center"
  },
  "inference_time_ms": 52.13,
  "fps": 19.17
}
```

---

# Reasoning Service

The Reasoning Service converts perception outputs into high-level interaction decisions.

### Supported Actions

| Action            | Description                 |
| ----------------- | --------------------------- |
| GREET             | User centered and stable    |
| ALIGN_REQUEST     | User detected on left/right |
| MULTI_PERSON_WARN | Multiple people detected    |
| NO_ACTION         | No valid interaction        |

### Stabilization Logic

The system uses a temporal stabilization mechanism based on recent frame history.

Decision rules are evaluated over multiple consecutive frames to reduce unstable detections and false triggers.

### Cooldown Mechanism

A cooldown mechanism prevents repetitive actions from being continuously triggered.

### Endpoint

```text
POST /v1/reasoning/decide-llm
```

---

# Optional LLM Layer

The system optionally supports Large Language Model integration.

### Supported Modes

| Mode  | Description                  |
| ----- | ---------------------------- |
| rules | Pure rule-based reasoning    |
| llm   | LLM-assisted reasoning       |
| auto  | Automatic fallback mechanism |

### LLM Output Schema

```json
{
  "action": "GREET",
  "utterance_tr": "Merhaba, hoş geldiniz.",
  "certainty": 0.92
}
```

If the LLM service fails or quota limits are exceeded, the system automatically falls back to the rule-based engine.

---

# Orchestrator Service

The Orchestrator Service coordinates the complete end-to-end pipeline.

### Responsibilities

* Receiving frames
* Forwarding requests to perception service
* Sending perception results to reasoning service
* Combining outputs
* Returning unified pipeline results

### Endpoint

```text
POST /v1/pipeline/run
```

---

# Event Logging

The system stores runtime events in SQLite.

### Logged Information

* Perception outputs
* Reasoning decisions
* Latency measurements
* Action history
* Detection metadata

This enables offline evaluation and performance analysis.

---

# Automated Test Pipeline

A custom evaluation pipeline was developed to validate system behavior under multiple real-world scenarios.

### Test Categories

* Single person
* Multi-person scenes
* Crowded scenes
* Empty scenes
* Partial human visibility
* Indoor scenes
* Distant people
* Complex backgrounds

### Evaluation Metrics

| Metric                | Description                     |
| --------------------- | ------------------------------- |
| Action Accuracy       | Correct high-level action       |
| People Count Accuracy | Correct people-count estimation |
| Position Accuracy     | Correct horizontal localization |
| False Trigger Count   | Incorrect activations           |
| Average Latency       | End-to-end pipeline delay       |

### Running Tests

```bash
python tests/run_tests.py
```

### Example Results

```text
Total tests: 20
Passed: 14
Action accuracy: 80%
People count accuracy: 80%
Position accuracy: 85%
False triggers: 0
Average latency: 531.65 ms
```

---

# Installation

## Clone Repository

```bash
git clone <repository-url>
cd real-time-human-perception-engine
```

---

# Running the System

## Build Containers

```bash
docker compose build
```

## Start Services

```bash
docker compose up
```

---

# Health Check Endpoints

| Service      | Endpoint                                                     |
| ------------ | ------------------------------------------------------------ |
| Perception   | [http://localhost:8001/health](http://localhost:8001/health) |
| Reasoning    | [http://localhost:8002/health](http://localhost:8002/health) |
| Orchestrator | [http://localhost:8000/health](http://localhost:8000/health) |

---

# Swagger Documentation

| Service      | Swagger URL                                              |
| ------------ | -------------------------------------------------------- |
| Perception   | [http://localhost:8001/docs](http://localhost:8001/docs) |
| Reasoning    | [http://localhost:8002/docs](http://localhost:8002/docs) |
| Orchestrator | [http://localhost:8000/docs](http://localhost:8000/docs) |

---

# Running Demo Pipeline

```bash
python orchestrator/app/run_demo.py
```

The demo script processes video frames and displays:

* detected people count
* estimated position
* generated action
* utterance output
* end-to-end latency

---

# Example Pipeline Output

```text
[frame=180]
people=1
position=center
action=GREET
source=llm_fallback_rules
latency_ms=468.09
utterance=Merhaba, hoş geldiniz.
```

---

# Future Improvements

* Webcam streaming support
* GPU acceleration
* Tracking integration
* Voice interaction module
* Advanced LLM prompts
* RAG-based contextual reasoning
* ROS2 integration
* Edge-device deployment

---

# Conclusion

This project demonstrates a modular and real-time human-aware interaction pipeline combining computer vision, reasoning systems, and optional LLM integration.

The architecture provides a scalable foundation for future robotic perception and human-robot interaction applications.

---

# Authors

Developed as part of an AI and Robotics engineering project.
