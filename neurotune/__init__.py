try:
    import importlib.metadata
    __version__ = importlib.metadata.version("neurotune")
except ImportError:
    import importlib_metadata
    __version__ = importlib_metadata.version("neurotune")
