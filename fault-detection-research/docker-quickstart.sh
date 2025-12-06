#!/bin/bash
################################################################################
# Docker Quick Start Script
# Fault Detection Research Environment
#
# This script automates the Docker setup process:
# - Checks prerequisites
# - Builds Docker image
# - Starts container
# - Runs verification tests
################################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
IMAGE_NAME="fault-detection-research:latest"
CONTAINER_NAME="fault-detection-env"
COMPOSE_FILE="docker-compose.yml"

################################################################################
# Functions
################################################################################

print_header() {
    echo ""
    echo "================================================================================"
    echo -e "${BLUE}$1${NC}"
    echo "================================================================================"
    echo ""
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

check_command() {
    if command -v $1 &> /dev/null; then
        print_success "$1 is installed"
        return 0
    else
        print_error "$1 is not installed"
        return 1
    fi
}

################################################################################
# Main Script
################################################################################

print_header "Fault Detection Research - Docker Quick Start"

# Step 1: Check prerequisites
print_header "Step 1: Checking Prerequisites"

PREREQ_OK=true

if check_command docker; then
    DOCKER_VERSION=$(docker --version | awk '{print $3}' | sed 's/,//')
    print_info "Docker version: $DOCKER_VERSION"
else
    print_error "Please install Docker first: https://docs.docker.com/get-docker/"
    PREREQ_OK=false
fi

if check_command docker-compose; then
    COMPOSE_VERSION=$(docker-compose --version | awk '{print $4}' | sed 's/,//')
    print_info "Docker Compose version: $COMPOSE_VERSION"
else
    print_warning "docker-compose not found, trying 'docker compose' (v2)"
    if docker compose version &> /dev/null; then
        print_success "Docker Compose v2 is available"
        alias docker-compose='docker compose'
    else
        print_error "Please install Docker Compose"
        PREREQ_OK=false
    fi
fi

if [ "$PREREQ_OK" = false ]; then
    print_error "Prerequisites check failed. Please install missing dependencies."
    exit 1
fi

print_success "All prerequisites met!"

# Step 2: Check if already running
print_header "Step 2: Checking Existing Containers"

if docker ps -a | grep -q $CONTAINER_NAME; then
    print_warning "Container '$CONTAINER_NAME' already exists"
    read -p "Do you want to remove it and start fresh? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_info "Stopping and removing existing container..."
        docker-compose down
        print_success "Existing container removed"
    else
        print_info "Keeping existing container"
        if docker ps | grep -q $CONTAINER_NAME; then
            print_success "Container is already running"
            print_info "Skipping build and start steps"
            SKIP_BUILD=true
            SKIP_START=true
        else
            print_info "Container exists but is stopped"
            SKIP_BUILD=true
            SKIP_START=false
        fi
    fi
fi

# Step 3: Build Docker image
if [ "$SKIP_BUILD" != true ]; then
    print_header "Step 3: Building Docker Image"
    print_info "This may take 5-10 minutes on first run..."

    if docker-compose build; then
        print_success "Docker image built successfully"
    else
        print_error "Failed to build Docker image"
        exit 1
    fi
else
    print_header "Step 3: Building Docker Image (Skipped)"
    print_info "Using existing image"
fi

# Step 4: Start container
if [ "$SKIP_START" != true ]; then
    print_header "Step 4: Starting Container"

    if docker-compose up -d; then
        print_success "Container started successfully"
        sleep 3  # Give container time to fully start
    else
        print_error "Failed to start container"
        exit 1
    fi
else
    print_header "Step 4: Starting Container (Skipped)"
    print_info "Container already running"
fi

# Step 5: Verify installation
print_header "Step 5: Verifying Installation"

print_info "Checking container status..."
if docker ps | grep -q $CONTAINER_NAME; then
    print_success "Container is running"
else
    print_error "Container is not running"
    docker logs $CONTAINER_NAME
    exit 1
fi

print_info "Checking Python environment..."
if docker exec $CONTAINER_NAME python3 --version &> /dev/null; then
    PYTHON_VERSION=$(docker exec $CONTAINER_NAME python3 --version | awk '{print $2}')
    print_success "Python $PYTHON_VERSION is available"
else
    print_error "Python not found in container"
    exit 1
fi

print_info "Checking Python dependencies..."
if docker exec $CONTAINER_NAME python3 -c "import numpy, pandas, sklearn, imblearn; print('OK')" &> /dev/null; then
    print_success "All Python dependencies installed"
else
    print_error "Python dependencies missing"
    exit 1
fi

print_info "Checking Java (for CloudSim)..."
if docker exec $CONTAINER_NAME java -version &> /dev/null 2>&1; then
    print_success "Java is installed"
else
    print_warning "Java not found (only needed for CloudSim integration)"
fi

print_info "Checking project files..."
if docker exec $CONTAINER_NAME ls -la /workspace/requirements.txt &> /dev/null; then
    print_success "Project files accessible"
else
    print_error "Project files not found"
    exit 1
fi

# Step 6: Run test
print_header "Step 6: Running Quick Test"

print_info "Testing scikit-learn import..."
if docker exec $CONTAINER_NAME python3 -c "from sklearn.ensemble import RandomForestClassifier; print('Scikit-learn OK')" &> /dev/null; then
    print_success "Scikit-learn test passed"
else
    print_error "Scikit-learn test failed"
    exit 1
fi

# Success!
print_header "✅ Setup Complete!"

echo ""
echo -e "${GREEN}Your fault detection research environment is ready!${NC}"
echo ""
echo "Next steps:"
echo ""
echo "  1. Enter the container:"
echo -e "     ${BLUE}docker exec -it $CONTAINER_NAME bash${NC}"
echo ""
echo "  2. Run a demo experiment:"
echo -e "     ${BLUE}python3 train_models_demo.py${NC}"
echo ""
echo "  3. View logs:"
echo -e "     ${BLUE}docker-compose logs -f${NC}"
echo ""
echo "  4. Stop the container:"
echo -e "     ${BLUE}docker-compose down${NC}"
echo ""
echo "Quick reference:"
echo -e "  • Container name: ${YELLOW}$CONTAINER_NAME${NC}"
echo -e "  • Image name: ${YELLOW}$IMAGE_NAME${NC}"
echo -e "  • Jupyter (if enabled): ${YELLOW}http://localhost:8888${NC}"
echo ""
echo "Documentation:"
echo -e "  • Setup guide: ${BLUE}DOCKER_SETUP.md${NC}"
echo -e "  • Experiments: ${BLUE}EXPERIMENT_LOG.md${NC}"
echo -e "  • README: ${BLUE}README.md${NC}"
echo ""
echo "================================================================================"
echo ""

# Offer to enter container
read -p "Do you want to enter the container now? (Y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Nn]$ ]]; then
    echo ""
    print_info "Entering container..."
    docker exec -it $CONTAINER_NAME bash
fi
