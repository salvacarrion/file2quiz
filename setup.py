from setuptools import setup, find_packages

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(name='quiz2test',
      version='0.2',
      description='Parse multiple-choice tests from unstructured sources',
      url='https://github.com/salvacarrion/quiz2test',
      author='Salva Carrión',
      license='MIT',
      packages=find_packages(),
      install_requires=requirements,
      zip_safe=False,
      entry_points={
          'console_scripts': [
              'quiz2test = quiz2test:main'
          ]
      },
      )