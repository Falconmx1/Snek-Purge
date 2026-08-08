from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="snek-purge",
    version="2.0.0",
    author="Falconmx1",
    description="🧹 Limpia tu sistema como un profesional: caché, intercambio, temporales y más",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Falconmx1/Snek-Purge",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Environment :: Console",
        "Intended Audience :: End Users/Desktop",
        "Topic :: System :: Systems Administration",
        "Topic :: Utilities",
    ],
    python_requires=">=3.6",
    install_requires=[
        "psutil>=5.9.0",
        "tqdm>=4.64.0",
        "colorama>=0.4.6",
    ],
    entry_points={
        "console_scripts": [
            "snek-purge=snek_purge:main",
        ],
    },
)
