from setuptools import setup, find_packages

setup(
    name="zdem_dfn",
    version="1.0.0",
    description="ZDEM 离散元离散裂隙网络生成引擎 / Discrete Fracture Network Generation Engine for ZDEM Simulations",
    packages=find_packages(),
    install_requires=[
        "tqdm>=4.62.0",
        "matplotlib>=3.4.0",
    ],
    python_requires=">=3.10",
    entry_points={
        "console_scripts": [
            "zdem-dfn=zdem_dfn.engine:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: Chinese (Simplified)",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering",
        "Topic :: Scientific/Engineering :: Physics",
    ],
)
