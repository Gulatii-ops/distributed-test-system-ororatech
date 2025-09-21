# Distributed Test System Setup Script
# This script automates the complete setup and execution of the distributed test system

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if RabbitMQ is running
check_rabbitmq() {
    if command_exists rabbitmqctl; then
        if rabbitmqctl status >/dev/null 2>&1; then
            return 0
        fi
    fi
    return 1
}

# Function to start RabbitMQ
start_rabbitmq() {
    print_status "Starting RabbitMQ..."
    
    # macOS
    if command_exists brew; then
        if ! check_rabbitmq; then
            brew services start rabbitmq
            sleep 5
        fi
    else
        print_error "Homebrew not found. Please install RabbitMQ manually."
        exit 1
    fi
    
    # Verify RabbitMQ is running
    if check_rabbitmq; then
        print_success "RabbitMQ is running"
    else
        print_error "Failed to start RabbitMQ"
        exit 1
    fi
}

# Function to check if Docker is running
check_docker() {
    if command_exists docker; then
        if docker info >/dev/null 2>&1; then
            return 0
        fi
    fi
    return 1
}

# Function to wait for containers to be ready
wait_for_containers() {
    print_status "Waiting for containers to be ready..."
    local max_attempts=30
    local attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        if docker-compose ps | grep -q "Up"; then
            print_success "Containers are up and running"
            return 0
        fi
        sleep 2
        attempt=$((attempt + 1))
    done
    
    print_error "Containers failed to start properly"
    return 1
}

# Function to run tasks and save JSON
run_tasks_and_save() {
    print_status "Running tasks A and B..."
    
    # Create logs directory if it doesn't exist
    mkdir -p logs
    
    # Run the dispatcher
    python3 dispatch.py
    
    # Check if log file was created
    if ls logs/log_*.json 1> /dev/null 2>&1; then
        latest_log=$(ls -t logs/log_*.json | head -n1)
        print_success "Results saved to: $latest_log"
    else
        print_warning "No JSON log file found"
    fi
}

# Main execution
main() {
    print_status "Starting Distributed Test System Setup..."
    
    # Check prerequisites
    print_status "Checking prerequisites..."
    
    if ! command_exists docker; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! command_exists docker-compose; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    if ! command_exists python3; then
        print_error "Python 3 is not installed. Please install Python 3 first."
        exit 1
    fi
    
    print_success "All prerequisites found"
    
    # Step 1: Start RabbitMQ
    print_status "Step 1: Starting RabbitMQ..."
    if ! check_rabbitmq; then
        start_rabbitmq
    else
        print_success "RabbitMQ is already running"
    fi
    
    # Step 2: Install Python dependencies
    print_status "Step 2: Installing Python dependencies..."
    if [ -f requirements.txt ]; then
        pip3 install -r requirements.txt
        print_success "Dependencies installed"
    else
        print_warning "requirements.txt not found, skipping dependency installation"
    fi
    
    # Step 3: Build and start Docker containers
    print_status "Step 3: Building and starting Docker containers..."
    
    if ! check_docker; then
        print_error "Docker is not running. Please start Docker Desktop."
        exit 1
    fi
    
    # Build containers
    docker-compose build
    print_success "Containers built"
    
    # Start containers
    docker-compose up -d
    print_success "Containers started"
    
    # Step 4: Verify containers are running
    print_status "Step 4: Verifying containers are running..."
    wait_for_containers
    
    # Show container status
    print_status "Container status:"
    docker-compose ps
    
    # Step 5: Run tasks A and B and save JSON
    print_status "Step 5: Running tasks A and B..."
    run_tasks_and_save
    
    # Step 6: Stop containers
    print_status "Step 6: Stopping containers..."
    docker-compose down
    print_success "Containers stopped"
    print_status "You can now:"
    print_status "  - View logs: docker-compose logs"
    print_status "  - Start containers: docker-compose up -d"
}

# Run main function
main "$@"
