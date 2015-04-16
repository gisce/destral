from setuptools import setup, find_packages


setup(
    name='destral',
    version='0.1.0',
    packages=find_packages(),
    url='https://github.com/gisce/destral',
    install_requires=[
        'osconf',
        'expects'
    ],
    license='MIT',
    author='GISCE-TI, S.L.',
    author_email='devel@gisce.net',
    entry_points={
        'console_scripts': [
            'ootest = destral.cli:main'
        ]
    },
    description=''
)
