rom setuptools import find_packages, setup

setup(
    name='TracMentions', version='0.1',
    packages=find_packages(exclude=['*.tests*']),
    entry_points = """
        [trac.plugins]
        mentions = tracmentions.plugin
    """,
)
