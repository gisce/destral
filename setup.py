from setuptools import setup, find_packages


setup(
    name='destral',
    version='1.12.2',
    packages=find_packages(),
    url='https://github.com/gisce/destral',
    install_requires=[
        'requests',
        'osconf',
        'expects',
        'six',
        'click',
        'mamba<0.11.0',
        'coverage',
        'lazy-object-proxy<1.7.0',
        'pylint',
        'python-dateutil',
        'babel>=2.4.0',
        'junit_xml',
        'psycopg2',
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
