# Pytorch CUDA GPU Setup Scripts

![Component ID](https://img.shields.io/badge/Component%20ID-comp__7e6fc-blue)
![Version](https://img.shields.io/badge/Version-v1.0.0-green)

A collection of utility scripts and a notebook to help you set up and verify your PyTorch installation with CUDA GPU support. This component is essential for ensuring your deep learning environment is correctly configured to leverage hardware acceleration.

## 🚀 Features

- **Driver Verification**: Check your NVIDIA driver version and supported CUDA version using `nvidia-smi`.
- **Installation Helper**: Commands to install PyTorch, torchvision, and torchaudio with specific CUDA support (e.g., CUDA 12.1).
- **Environment Verification**: Verify Python and PyTorch versions.
- **GPU Diagnostics**:
    - Detect CUDA availability.
    - List available GPU devices.
    - Display GPU memory and compute capability.
    - Perform a test tensor allocation on the GPU to confirm functionality.

## 📖 Usage

1.  **Open the Notebook**: Open `setup.ipynb` in your preferred environment (VS Code, Jupyter Lab, etc.).
2.  **Check Drivers**: Run the first cell to verify your NVIDIA drivers are installed and working.
3.  **Install Dependencies**: If you haven't installed PyTorch yet, run the installation cell. *Note: Adjust the CUDA version in the URL if necessary.*
4.  **Verify Setup**: Run the verification script to check if PyTorch can see your GPU and allocate tensors.

## 📋 Metadata

- **Author**: Vijay Ram Enaganti
- **Tags**: `GPU`, `Pytorch`, `CUDA`, `Python`
- **Component ID**: `comp_7e6fc`
