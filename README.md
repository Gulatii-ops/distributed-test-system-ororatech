# Distributed Test System

A distributed automated test system built with RabbitMQ, Celery, and Docker that demonstrates task routing, worker isolation, and concurrent execution.

## 🎯 **What this does**
????????????????????????????????????????????????
---

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   dispatch.py   │    │   RabbitMQ      │    │  Docker Workers │
│   (Dispatcher)  │────│   (Broker)      │────│                 │
│                 │    │                 │    │  ┌─────────────┐│
└─────────────────┘    │  ┌──────────────┤    │  │  Worker A   ││
                       │  │   queue_a    │◄───┤  │ (task_a)    ││
                       │  │              │    │  └─────────────┘│
                       │  ├──────────────┤    │  ┌─────────────┐│
                       │  │   queue_b    │◄───┤  │  Worker B   ││
                       │  │              │    │  │ (task_b)    ││
                       │  └──────────────┘    │  └─────────────┘│
                       └─────────────────┘    └─────────────────┘
```

## 🚀 Features

### Core Requirements
- ✅ **RabbitMQ Integration**: Message broker running locally
- ✅ **Celery Tasks**: Two isolated tasks (`task_a` and `task_b`)
- ✅ **Container Isolation**: Each worker processes only designated tasks
- ✅ **Concurrent Execution**: Parallel task dispatching and result collection

???????????????????????????????????????????

### Enhanced Features (Stretch Goals)
- 🎨 **Rich Visualization**: Colored output with real-time status updates
- 📊 **Performance Metrics**: Execution timing and statistics
- 📝 **Structured Logging**: JSON-formatted logs with metadata
- 🔄 **Retry Mechanism**: Automatic retries with exponential backoff
- 💾 **Result Persistence**: JSON output for further analysis
- 🐳 **Docker Orchestration**: Complete containerized deployment
- 🔍 **Health Monitoring**: Broker connection and worker status checks

## 📋 Prerequisites

- **Docker & Docker Compose**: For container orchestration
- **RabbitMQ**: Message broker (running locally, not in container)
- **Python 3.8+**: For local development and testing

## 🛠️ Setup Instructions

### 1. Install and Start RabbitMQ

#### macOS (using Homebrew)
```bash
# Install RabbitMQ
brew install rabbitmq

# Start RabbitMQ server
brew services start rabbitmq

```

#### Linux
```bash
# Install RabbitMQ
sudo apt-get update
sudo apt-get install rabbitmq-server

# Start RabbitMQ service
sudo systemctl start rabbitmq-server
sudo systemctl enable rabbitmq-server
```

#### Verify RabbitMQ Installation
```bash
# Check if RabbitMQ is running
sudo rabbitmqctl status

# Access management UI [http://localhost:15672 (guest/guest)]
rabbitmq-plugins enable rabbitmq_management
```

### 2. Clone and Setup Project

```bash
# Clone the repository (or download the files)
git clone <repository-url>
````
## Quick Start with Makefile

The easiest way to run the system:

```bash
make test    # Complete automated test
```

Or step by step:
```bash
make up         # Start containers
make run        # Run dispatcher
make down       # Stop containers
```
## Manual Setup

### 1. Install Python dependencies
```
pip install -r requirements.txt
```

### 2. Build and Run Worker Containers

```bash
# Build the Docker image
docker-compose build

# Start both worker containers
docker-compose up -d

# Verify containers are running
docker-compose ps
```

Expected output:
```
 Name                    Command               State    Ports
----------------------------------------------------------------
%-worker-a   celery -A celery_app worke ...   Up ...
%-worker-b   celery -A celery_app worke ...   Up ...
```

### 3. Run the Dispatcher

```bash
# Execute the dispatcher script
python dispatch.py
```

## Makefile Commands

```bash
make help       # Show usage
make install    # Install dependencies
make build      # Build containers
make up         # Start containers
make down       # Stop containers
make run        # Run dispatcher
make test       # Full test sequence
make logs       # Show logs
make ps         # Container status
make clean      # Clean up
```

## 📱 Expected Output

When you run `python dispatch.py`, you should see output similar to:

```
Dispatching tasks...
Result from task_a: Hello from Task A
Result from task_b: Hello from Task B
```

## Architecture

- **task_a**: Processed only by worker-a (queue_a)
- **task_b**: Processed only by worker-b (queue_b)
- **RabbitMQ**: Message broker running on host
- **Docker**: Two isolated worker containers

## Files

- `celery_app.py`: Celery configuration and tasks
- `dispatch.py`: Simple dispatcher script
- `Dockerfile`: Worker container definition
- `docker-compose.yml`: Container orchestration
- `requirements.txt`: Python dependencies

## Cleanup

```bash
docker-compose down
```
