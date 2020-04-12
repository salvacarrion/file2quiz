from setuptools import setup, find_packages

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(name='file2quiz',
      version='0.5',
      description='Text processing utility to extract multiple-choice questions from unstructured sources.',
      url='https://github.com/salvacarrion/file2quiz',
      author='Salva Carrión',
      license='MIT',
      packages=find_packages(),
      package_data={
          'examples.raw': ['*.*'],
      },
      install_requires=requirements,
      zip_safe=False,
      entry_points={
          'console_scripts': [
              'file2quiz = file2quiz:main'
          ]
      },
      test_suite='tests.coverage',
      )
