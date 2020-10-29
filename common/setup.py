import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="covid-test-common", # Replace with your own username
    version="0.0.1",
    author="Lennart Stipulkowski",
    author_email="stipulkowski@stud.uni-heidelberg.de",
    description="Package containing common functionality for the covid-test-app",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/anders-biostat/covid-test-web-site",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)