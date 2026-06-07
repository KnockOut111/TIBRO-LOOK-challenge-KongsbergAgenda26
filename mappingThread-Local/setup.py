from setuptools import setup
from glob import glob
import os

package_name = "mapping_thread_local"

setup(
    name=package_name,
    version="0.0.1",
    packages=[package_name],
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        (os.path.join("share", package_name, "launch"), glob("launch/*.launch.py")),
        (os.path.join("share", package_name, "config"), glob("config/*.yaml")),
        (os.path.join("share", package_name, "rviz"), glob("rviz/*.rviz")),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="team",
    maintainer_email="todo@example.com",
    description="Mapping bringup for ExoMy autonomy stack",
    license="TODO",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": [],
    },
)
