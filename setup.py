from setuptools import setup, find_packages


setup(
    name='destral',
    version='1.0.2',
    packages=find_packages(),
    url='https://github.com/gisce/destral',
    install_requires=[
        'osconf',
        'expects',
        'click',
        'mamba<=0.9.2',
        'coverage',
        'python-dateutil',
        'babel>=2.4.0',
        'junit_xml'
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
