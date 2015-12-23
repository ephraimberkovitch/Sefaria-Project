
import hashlib
import sys

try:
    from sefaria.settings import USE_VARNISH
except ImportError:
    USE_VARNISH = False

if not hasattr(sys, '_doc_build'):
    from django.core.cache import cache


#functions from here: http://james.lin.net.nz/2011/09/08/python-decorator-caching-your-functions/
#and here: https://github.com/rchrd2/django-cache-decorator

# New cache instance reconnect-apparently
cache_factory = {}

def get_cache_factory(cache_type):
    """
    Helper to only return a single instance of a cache
    As of django 1.7, may not be needed.
    """
    from django.core.cache import get_cache

    if cache_type is None:
        cache_type = 'default'

    if not cache_type in cache_factory:
        cache_factory[cache_type] = get_cache(cache_type)

    return cache_factory[cache_type]


#get the cache key for storage
def cache_get_key(*args, **kwargs):
    serialise = []
    for arg in args:
        serialise.append(str(arg))
    for key,arg in kwargs.items():
        serialise.append(str(key))
        serialise.append(str(arg))
    key = hashlib.md5("".join(serialise)).hexdigest()
    return key


def django_cache_decorator(time=300, cache_key='', cache_type=None):
    """
    Easily add caching to a function in django
    """
    cache = get_cache_factory(cache_type)
    if not cache_key:
        cache_key = None

    def decorator(fn):
        def wrapper(*args, **kwargs):
            #logger.debug([args, kwargs])

            # Inner scope variables are read-only so we set a new var
            _cache_key = cache_key

            if not _cache_key:
                _cache_key = cache_get_key(fn.__name__, *args, **kwargs)

            #logger.debug(['_cach_key.......',_cache_key])
            result = cache.get(_cache_key)

            if not result:
                result = fn(*args, **kwargs)
                cache.set(_cache_key, result, time)

            return result
        return wrapper
    return decorator
#-------------------------------------------------------------#


def get_cache_elem(key):
    return cache.get(key)


def set_cache_elem(key, value, duration = 600000):
    return cache.set(key, value, duration)


def delete_cache_elem(key):
    return cache.delete(key)


def get_template_cache(fragment_name='', *args):
    cache_key = 'template.cache.%s.%s' % (fragment_name, hashlib.md5(u':'.join([arg for arg in args])).hexdigest())
    print cache_key
    return get_cache_elem(cache_key)


def delete_template_cache(fragment_name='', *args):
    delete_cache_elem('template.cache.%s.%s' % (fragment_name, hashlib.md5(u':'.join([arg for arg in args])).hexdigest()))


#-------------------------- cascading cache functions --------------------------------- #
#TODO: should these maybe be somewhere that isn't the main cache module?

def generate_text_toc_cache_key(index_name):
    index_name = index_name.replace("_", " ")
    key = cache_get_key(*['make_toc_html', index_name], **{'zoom' : 1})
    return key

def process_version_save_in_cache(ver, **kwargs):
    delete_cache_elem(generate_text_toc_cache_key(ver.title))

def process_version_delete_in_cache(ver, **kwargs):
    delete_cache_elem(generate_text_toc_cache_key(ver.title))

