from setuptools import find_packages, setup

PACKAGE = 'TracMentions'
VERSION = '0.1'

setup(
    name=PACKAGE, version=VERSION,
    packages=find_packages(exclude=['*.tests*']),
    license='MIT',
    author='James Aylett',
    url = 'http://tartarus.org/james/computers/tracmentions/',
    entry_points = {
        'trac.plugins': ['tracmentions = tracmentions'],
        'console_scripts': [
            'update-trac-mentions = tracmentions.updater:update',
        ],
    },
    # entry_points = """
    #     [trac.plugins]
    #     tracmentions = tracmentions
    # """,
    install_requires=[
        'Trac>=0.11',
        'simplejson',
        'feedparser',
    ]
)
