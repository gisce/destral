from setuptools import setup, find_packages


setup(
    name='destral',
    version='0.20.1',
    packages=find_packages(),
    url='https://github.com/gisce/destral',
    install_requires=[
        'osconf',
        'expects',
        'click',
        'mamba',
        'coverage'
    ],
    license='GNU GPLv3',
    author='GISCE-TI, S.L.',
    author_email='devel@gisce.net',
    entry_points={
        'console_scripts': [
            'destral = destral.cli:destral'
        ]
    },
    description='OpenERP testing framework'
)
