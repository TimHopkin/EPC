from setuptools import setup, find_packages

setup(
    name="epc-tool",
    version="1.0.0",
    description="EPC Data Integration Tool for Digital Land Solutions",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Digital Land Solutions",
    author_email="contact@digitallandsolutions.co.uk",
    packages=find_packages(),
    install_requires=[
        "requests>=2.28.0",
        "pandas>=1.5.0", 
        "geopandas>=0.12.0",
        "click>=8.1.0",
        "python-dotenv>=1.0.0",
        "tqdm>=4.64.0",
        "folium>=0.14.0",
        "sqlalchemy>=1.4.0",
        "geopy>=2.3.0",
        "shapely>=2.0.0",
        "pyproj>=3.4.0"
    ],
    entry_points={
        'console_scripts': [
            'epc-tool=src.cli.commands:cli',
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
)