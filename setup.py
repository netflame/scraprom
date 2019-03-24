from setuptools import setup, find_packages
import scraprom

with open('README.md', 'r') as fh:
    long_description = fh.read()

setup(
    name=scraprom.__name__,
    version=scraprom.__version__,
    url='https://github.com/netflame/scraprom',
    description=scraprom.__description__,
    long_description=long_description,
    long_description_content_type="text/markdown",
    author=scraprom.__author__,
    author_email=scraprom.__author_email__,
    license='MIT',
    packages=find_packages(exclude=('tests', 'tests.*')),
    include_package_data=True,
    zip_safe=False,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Framework :: Scrapy',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Topic :: Internet :: WWW/HTTP',
    ],
    install_requires=[
        'prometheus_client',
        'scrapy',
    ],
    python_requires='>=3',
    keywords='scrapy prometheus exporter',
)
