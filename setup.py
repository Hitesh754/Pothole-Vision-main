from setuptools import setup, find_packages

setup(
    name="roadsense-ai",
    version="1.0.0",
    description="AI-powered road and civil structure damage detection pipeline",
    author="Parth Jangir & Team RoadSense AI",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        "ultralytics>=8.1.0",
        "opencv-python>=4.8.0",
        "numpy>=1.24.0,<2.0.0",
        "pyyaml>=6.0",
        "fastapi>=0.104.0",
        "uvicorn>=0.24.0",
        "Pillow>=10.0.0",
        "imagehash>=4.3.1"
    ],
)

