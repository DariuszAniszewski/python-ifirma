from setuptools import setup, find_packages

setup(
    name="python-ifirma",
    version="0.0.2",
    packages=find_packages(),
    install_requires=[
        'requests',
        'six',
    ],
    author='Dariusz Aniszewski',
    author_email='dariusz@aniszewski.eu',
    license='BSD License',

)