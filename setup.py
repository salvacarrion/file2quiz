from setuptools import setup, find_packages

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(name='file2quiz',
      version='0.2',
      description='Parse multiple-choice tests from unstructured sources',
      url='https://github.com/salvacarrion/file2quiz',
      author='Salva Carrión',
      license='MIT',
      packages=find_packages(),
      install_requires=requirements,
      zip_safe=False,
      entry_points={
          'console_scripts': [
              'file2quiz = file2quiz:main'
          ]
      },
      )