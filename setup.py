import setuptools

setuptools.setup(
    name="gromosWoof",
    version="0.0.1",
    description="A package to track the progress of running gromos simulations on a slurm cluster",
    author="Marc Schuh",
    url="https://github.com/schuhmc/gromosWoof",
    packages=['gromosWoof'],
    install_requires=["setuptools>=61.0", "paramiko", "pandas"],
    classifiers=[
    'Development Status :: Testing',
    'Operating System :: Linux',
    'Programming Language :: Python :: 3.11'
    ]
)