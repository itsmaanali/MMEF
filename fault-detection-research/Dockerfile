# Multi-Modal Fault Detection Research Environment
# Python 3.13 with all ML dependencies

FROM python:3.13-slim

# Set metadata
LABEL maintainer="Fault Detection Research Team"
LABEL description="Multi-Modal Fault Detection System with ML models"
LABEL version="1.0"

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive

# Set working directory
WORKDIR /workspace

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    curl \
    wget \
    vim \
    nano \
    tree \
    htop \
    # For matplotlib/seaborn
    libfreetype6-dev \
    libpng-dev \
    libjpeg-dev \
    # For scientific computing
    gfortran \
    libopenblas-dev \
    liblapack-dev \
    # Java for CloudSim (if needed)
    openjdk-17-jdk \
    maven \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN pip install --upgrade pip setuptools wheel

# Copy requirements file
COPY requirements.txt /workspace/

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project
COPY . /workspace/

# Create necessary directories
RUN mkdir -p \
    /workspace/models \
    /workspace/output/plots \
    /workspace/output/telemetry \
    /workspace/datasets/processed

# Set Java environment variables (for CloudSim)
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
ENV PATH="${JAVA_HOME}/bin:${PATH}"

# Expose ports (if running web services in future)
EXPOSE 8888 8080

# Default command - start bash shell
CMD ["/bin/bash"]

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python3 -c "import numpy, pandas, sklearn; print('OK')" || exit 1
