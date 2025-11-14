"""Setup script for Lattice Sensor Data Integration Service."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="lattice-sensor-simulator",
    version="1.0.0",
    author="Micah Seghetti",
    description="Professional-grade sensor/drone simulator integrating with Anduril's Lattice SDK",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Mseghetti/Anduril-Lattice-Sensor-Data-Integration-Service",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.10",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "lattice-simulator=main:main",
        ],
    },
)

