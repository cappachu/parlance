
from setuptools import setup, find_packages
import parlance

setup(
    name='parlance',
    version=parlance.__version__,
    description='Chat with Folks on Your Local Area Network',
    author='Codanda B. Appachu',
    author_email = 'cappachu@gmail.com',
    url='https://github.com/cappachu/parlance',
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'parlance = parlance.parlance:main',
        ]
    },
    install_requires=[
        'urwid',
        'argparse',
    ],
    download_url = 'https://github.com/cappachu/parlance/tarball/1.0.0', 
    keywords = ['multicast', 'chat', 'local area network']
)
