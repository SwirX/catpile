from setuptools import setup, find_packages

with open("README.md", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="catpile",
    version="1.0.0",
    packages=find_packages(),
    include_package_data=True,
    package_data={"catpile": ["schema.json"]},
    entry_points={
        "console_scripts": [
            "cpile=catpile.cli:main",
            "cpile-decompile=catpile.decompile_cli:main",
        ],
    },
    python_requires=">=3.10",
    author="SwirX",
    author_email="",
    url="https://github.com/swirx/catpile",
    description="Catpile - Pythonic DSL → CatWeb JSON compiler",
    long_description=long_description,
    long_description_content_type="text/markdown",
    license="GNU General Public License v3.0",
    keywords="catweb, roblox, compiler, dsl, catlua",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Topic :: Software Development :: Compilers",
        "Topic :: Software Development :: Preprocessors",
    ],
    project_urls={
        "Source": "https://github.com/swirx/catpile",
        "Documentation": "https://github.com/swirx/catpile/tree/main/docs",
    },
)
