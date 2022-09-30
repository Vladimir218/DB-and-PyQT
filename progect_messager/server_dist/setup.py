from setuptools import setup, find_packages

setup(name="application_server",
      version="0.0.1",
      description="Application Server",
      author="Kamenev Vladimir",
      author_email="kvv23@tut.by",
      packages=find_packages(),
      install_requires=['PyQt5', 'sqlalchemy', 'pycryptodome', 'pycryptodomex']
      )
