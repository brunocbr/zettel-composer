from setuptools import setup, find_packages

setup(
    name="zettel-compose",
    version="0.1.0",
    packages=find_packages(),
    py_modules=["zettel-compose", "writers_gadget_ble"],
    install_requires=[
        "bleak",
        "pyyaml",
    ],
    entry_points={
        "console_scripts": [
            "zettel-compose=zettel_compose:main", # Assume que sua função principal chama-se main
        ],
    },
    author="Seu Nome",
    description="Compose Zettelkasten notes",
)
