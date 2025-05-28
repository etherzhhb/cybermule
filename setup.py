from setuptools import setup, find_packages

setup(
    name="cybermule",
    version="0.1.0",
    description="An autonomous AI agent for code generation, testing, and self-improvement",
    packages=find_packages(),
    install_requires=[
        "typer",
        "boto3",
        "langchain",
        "openai",
        "pydantic",
    ],
    entry_points={
        "console_scripts": [
            "cybermule=cybermule.cli.main:app",
        ],
    },
    python_requires=">=3.8",
)