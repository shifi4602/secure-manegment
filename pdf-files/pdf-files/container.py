from __future__ import annotations
import importlib
import inspect
import pkgutil
from dependency_injector import containers, providers

from src.infra.pdf_reader import PdfReader
from src.app.detector               import KeywordDetector
from src.app.validating_decorator   import ValidatingStrategyDecorator
from src.domain.interfaces import IParser, IVariationEngine, IGenerator


def _discover(package_name: str, base_class: type) -> list[type]:
    """
    Return every concrete, zero-arg-constructable subclass of *base_class*
    found inside *package_name*.

    Open/Closed: adding a new module (e.g. parser_type_c.py) to the package
    is all that is required — this file is never touched.

    Classes that require constructor arguments (e.g. decorators) are excluded
    so they are never accidentally auto-instantiated.
    """
    import importlib
    package = importlib.import_module(package_name)
    found: list[type] = []
    for _, module_name, _ in pkgutil.iter_modules(package.__path__):
        mod = importlib.import_module(f"{package_name}.{module_name}")
        for _, obj in inspect.getmembers(mod, inspect.isclass):
            if not (issubclass(obj, base_class) and obj is not base_class and not inspect.isabstract(obj)):
                continue
            # Skip classes whose __init__ requires positional arguments — they
            # are decorators or factories, not standalone strategy instances.
            sig = inspect.signature(obj.__init__)
            required = [
                p for name, p in sig.parameters.items()
                if name != "self"
                and p.default is inspect.Parameter.empty
                and p.kind not in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD)
            ]
            if required:
                continue
            found.append(obj)
    return found


class Container(containers.DeclarativeContainer):
    """
    Dependency-injection container.

    Design (interview note):
    ─────────────────────────────────────────────────────────────────────
    Nothing outside this file calls a constructor directly.
    main.py asks the container for ready-made objects.
    This means every component is swappable for a fake in tests by simply
    overriding the provider:

        container.pdf_reader.override(FakePdfReader())

    Open/Closed — Strategy collections:
    Adding a new report type (Type C, D, …) requires only creating three
    new files (parser_type_c.py, variation_type_c.py, generator_type_c.py).
    This file is never opened.
    ─────────────────────────────────────────────────────────────────────
    """

    config = providers.Configuration()

    # ── Infrastructure ─────────────────────────────────────────────────────────
    pdf_reader = providers.Singleton(PdfReader, dpi=300)
    detector   = providers.Singleton(KeywordDetector)

    # ── Strategy collections — auto-discovered, never manually listed ──────────
    parsers    = providers.Factory(lambda: [cls() for cls in _discover("src.app",   IParser)])
    # Each variation engine is wrapped with ValidatingStrategyDecorator so that
    # pre/post-condition checks run transparently around every strategy call.
    variations = providers.Factory(
        lambda: [
            ValidatingStrategyDecorator(cls())
            for cls in _discover("src.app", IVariationEngine)
        ]
    )
    generators = providers.Factory(lambda: [cls() for cls in _discover("src.infra", IGenerator)])
