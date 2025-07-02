from setuptools import setup, find_packages

setup(
    name="payment-gateway-system",
    version="0.1.0",
    description="Mock Payment Gateway with Self-Healing Capabilities",
    author="Your Name",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.8",
    install_requires=[
        "dataclasses",
        "typing-extensions",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0.0",
            "pytest-cov",
            "black",
            "flake8",
            "mypy",
        ]
    },
)