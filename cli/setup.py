import setuptools

setuptools.setup(
    name="covidtest",
    version="0.1",
    description="Command line interface for covidtest application",
    url="https://github.com/anders-biostat/covid-test-web-site/cli",
    author="Lennart S.",
    author_email="lennart@c6h12o6.de",
    license="MIT",
    packages=setuptools.find_packages(),
    setup_requires=[
        "wheel",
    ],
    install_requires=[],
    scripts=[
        "covidtest-cli",
    ],
    zip_safe=True,
)
