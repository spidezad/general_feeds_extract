from setuptools import setup

setup(name='general_feeds_extract',
      version='0.1',
      description='Pulling RSS feeds',
      url='https://github.com/spidezad',
      author='Tan Kok Hua',
      author_email='kokhua81@gmail.com',
      packages=['general_feeds_extract'],
	  install_requires=[
          'pattern',
      ],
      zip_safe=False)