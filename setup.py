try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="vulcan-app",
    version="1.1",
    author="Chatavut Viriyasuthee",
    author_email="chatavut@lab.ai",
    description="Vulcan's web application server.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/vulcan-coalition/vulcan-app.git",
    packages=["vulcan_app", "vulcan_app.database"],
    package_data={},
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.9',
    install_requires=[
        "aiofiles",
        "fastapi",
        "httpx==0.23.3",
        "pydantic",
        "PyJWT",
        "pytz",
        "requests",
        "requests-async",
        "SQLAlchemy",
        "PyDrive2",
        "pymongo",
        "boto3",
        "asyncpg",
        "shortuuid",
        "python-multipart",
        "sshtunnel==0.4.0"
    ]
)
