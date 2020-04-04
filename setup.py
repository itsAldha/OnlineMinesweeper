from setuptools import setup, find_packages

setup(
    name='main',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'flask',
        'flask-wtf'
    ],
    setup_requires=[
        'pytest-runner',
    ],
    tests_require=[
        'pytest',
    ],
)
