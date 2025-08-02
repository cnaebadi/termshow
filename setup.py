from setuptools import setup

setup(
    name='termshow',
    version='1.0.0',
    description='Simple terminal slideshow tool',
    author='Sina Ebadi',
    author_email='cneebadii@yahoo.com',
    py_modules=['termshow'],
    entry_points={
        'console_scripts': [
            'termshow=termshow:main',
        ],
    },
    classifiers=[
        'Programming Language :: Python :: 3',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)
