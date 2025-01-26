from setuptools import setup

setup(name="updater",
version="0.3.0",
author="MCVSoftware",
author_email="support@mcvsoftware.com",
url="https://github.com/mcvsoftware/updater",
packages=["updater"],
long_description=open("readme.md", "r").read(),
description="Cross platform Auto updater for python desktop apps",
package_data={"updater": ["bootstrappers/**/*"]},
zip_safe = False,
install_requires=["pypubsub", "PySocks", "win_inet_pton"]
)
