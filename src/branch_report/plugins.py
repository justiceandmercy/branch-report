import os
import importlib.util
from typing import List


class Plugin:
    def __init__(self, name, classify=None):
        self.name = name
        self.classify = classify


def load_plugins(plugin_dir):
    plugins = []
    if not plugin_dir or not os.path.isdir(plugin_dir):
        return plugins
    for fn in sorted(os.listdir(plugin_dir)):
        if not fn.endswith('.py'):
            continue
        path = os.path.join(plugin_dir, fn)
        spec = importlib.util.spec_from_file_location(f'br_plugin_{fn}', path)
        mod = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(mod)
        except Exception:
            continue
        if hasattr(mod, 'register') and callable(mod.register):
            try:
                mod.register(plugins)
            except Exception:
                pass
        if hasattr(mod, 'classify') and callable(mod.classify):
            plugins.append(Plugin(name=fn, classify=mod.classify))
        if hasattr(mod, 'PLUGIN'):
            plugins.append(mod.PLUGIN)
    return plugins


def apply_plugins(plugins, branch, config, labels):
    out = list(labels)
    for p in plugins:
        if p.classify:
            try:
                extra = p.classify(branch, config) or []
                out.extend(extra)
            except Exception:
                pass
    return out
