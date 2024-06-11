import sys

from setuptools import setup, find_packages

requirements = [
    'requests',
    'osconf',
    'expects',
    'six',
    'click',
    'coverage',
    'lazy-object-proxy<1.7.0',
    'pylint<=2.17.7',
    'python-dateutil',
    'babel>=2.4.0',
    'junit_xml',
    'psycopg2',
]
if sys.version_info.major < 3:
    requirements.append('mamba<0.11.0')
else:
    requirements.append('mamba>=0.11.0')
setup(
    name='destral',
    version='1.19.1',
    packages=find_packages(),
    url='https://github.com/gisce/destral',
    install_requires=requirements,
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
