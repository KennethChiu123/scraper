from setuptools import setup, find_packages

setup(
    name="scraper",  # Name of the package
    version="0.1",       # Version of the package
    packages=find_packages(),  # Automatically find all packages
    install_requires=[  # External dependencies your package needs
        "requests",
        "pytest",
        "beautifulsoup4",
        "transformers",
        "torch",
        "flask",
        "selenium",
        "pymongo",    # For MongoDB support
        "numpy==1.25.2",  # Specific version of numpy
    ],
    entry_points={
        "console_scripts": [
            "web-scraper=scraper.scraper:main",
            "web-api=api.app:main"
        ],
    },
    python_requires=">=3.11"
)