import os
from setuptools import setup, find_packages

required_packages = [
    'django>=1.3',
    'django-pagination==1.0.7',
    'django-sorter==0.2',
    'python-dateutil==2.2',
]

def read_file(filename):
    """Read a file into a string"""
    path = os.path.abspath(os.path.dirname(__file__))
    filepath = os.path.join(path, filename)
    try:
        return open(filepath).read()
    except IOError:
        return ''


setup(
    name='rapidsms-broadcast',
    version=__import__('broadcast').__version__,
    author='Caktus Consulting Group',
    author_email='solutions@caktusgroup.com',
    packages=find_packages(),
    include_package_data=True,
    url='https://github.com/caktus/rapidsms-broadcast/',
    license='BSD',
    description=u' '.join(__import__('broadcast').__doc__.splitlines()).strip(),
    classifiers=[
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Framework :: Django',
        'Development Status :: 4 - Beta',
        'Operating System :: OS Independent',
    ],
    long_description=read_file('README.rst'),
    tests_require=required_packages,
    test_suite="runtests.runtests",
    install_requires=required_packages,
    zip_safe=False,
)
