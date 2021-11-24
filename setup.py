from setuptools import setup

setup(
    name="rhp12rn",
    version="0.1.0",
    description="Python controller for the ROBOTIS RH-P12-RN and RH-P12-RN(A) grippers.",
    url="https://github.com/TimSchneider42/python-rhp12rn-controller",
    author="Tim Schneider",
    author_email="schneider@ias.informatik.tu-darmstadt.de",
    license="MIT",
    packages=["rhp12rn"],
    install_requires=[
        "dynamixel-sdk @ git+https://github.com/ROBOTIS-GIT/DynamixelSDK.git@c7e1eb71c911b87f7bdeda3c2c9e92276c2b4627#egg=dynamixel-sdk&subdirectory=python"
        ],

    classifiers=[
        "Development Status :: 1 - Planning",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: BSD License",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3.6",
    ],
)
