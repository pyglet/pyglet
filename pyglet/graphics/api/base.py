from __future__ import annotations

import atexit
import os
import weakref
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Protocol, get_type_hints, Sequence, Callable

if TYPE_CHECKING:
    from pyglet.math import Mat4
    from pyglet.graphics.api.gl import ObjectSpace
    from pyglet.window import Window

class BackendGlobalObject(ABC):  # Temp name for now.
    """A container for backend resources and information that are required throughout the code.

    Meant to be accessed from a global level.
    """
    windows: weakref.WeakKeyDictionary[Window, SurfaceContext]

    def __init__(self) -> None:
        self.windows = weakref.WeakKeyDictionary()
        self._current_window = None

    @property
    @abstractmethod
    def object_space(self) -> ObjectSpace:
        ...

    @abstractmethod
    def get_surface_context(self, window: Window, config) -> SurfaceContext:
        """After a window is created, this will be called.

        This must return a BackendWindowObject object.
        """

    @abstractmethod
    def get_default_configs(self) -> Sequence:
        """Configs to use if none specified."""

    @abstractmethod
    def initialize_matrices(self, window: Window) -> None:
        """Initialize the global matrices."""

    @abstractmethod
    def set_viewport(self, window, x: int, y: int, width: int, height: int) -> None:
        """Set the global viewport."""

    def load_package_shader(self, package, resource_name):
        """Reads a binary resource from the given package or subpackage without external dependencies.

        Args:
            package: The full package path (e.g., 'pyglet.graphics.api.vulkan.shaders').
            resource_name: The resource filename (e.g., 'primitives.vert.spv').

        Returns:
            The binary contents of the resource.
        """
        # Dynamically resolve the package's directory
        package_path = os.path.dirname(__import__(package, fromlist=['']).__file__)
        resource_path = os.path.join(package_path, resource_name)

        # Read the file in binary mode
        with open(resource_path, 'rb') as file:
            return file.read()

class SurfaceContext(ABC):  # Temp name for now.
    """A container for backend resources and information that are tied to a specific Window.

    In OpenGL this would be something like an OpenGL Context, or in Vulkan, a Surface.
    """
    clear_color = (0.2, 0.2, 0.2, 1.0)

    def __init__(self, global_ctx: BackendGlobalObject, window: Window, config: Any) -> None:
        self.core = global_ctx
        self.window = window
        self.config = config

    @abstractmethod
    def set_clear_color(self, r: float, g: float, b: float, a: float) -> None:
        """Sets the clear color for the current Window.

        Default value is black.
        """
        # Backends need to implement setting this value.

    @abstractmethod
    def attach(self, window: Window) -> None:
        """Attaches the specified Window into the backend context.

        This function is called automatically when the operating system Window has been created.
        """

    @abstractmethod
    def destroy(self) -> None:
        """Destroys the graphical context."""

    @abstractmethod
    def flip(self) -> None:
        """Flips the buffers in the graphical context."""

    @abstractmethod
    def clear(self) -> None:
        """Clears the framebuffer."""


class VerifiedGraphicsConfig:
    """Determines if this config is complete and able to create a Window resource context.

    This is kept separate as the original user config may be re-used for multiple windows.

    .. note:: Keep any non-backend attributes as private. Create a property if public use is wanted.
    """
    def __init__(self, window: Window, config: GraphicsConfig) -> None:  # noqa: D107
        self._window = window
        self._config = config

    @property
    def is_finalized(self) -> bool:
        return True

    @abstractmethod
    def apply_format(self) -> None:
        """Commit the selected finalized attributes to the backend."""

    @property
    def attributes(self) -> dict[str, Any]:
        return {attrib: value for attrib, value in self.__dict__.items() if attrib[0] != '_'}

    def __repr__(self) -> str:
        return f"Attributes({self.attributes})"


class GraphicsConfig:
    """User requested values for the graphics configuration.

    A Config stores the user preferences for attributes such as the size of the colour and depth buffers,
    double buffering, multisampling, anisotropic, and so on.

    Different platform and architectures only support certain attributes. Attributes are defined within the
    class attribute namespace.

    These are merely a suggestion to the backends; there is no guarantee that a platform or driver accept the
    combination of attributes together.
    """

    def __init__(self, **kwargs: float | str) -> None:
        """Create a template config with the given attributes.

        Specify attributes as keyword arguments, for example::

            template = UserConfig(double_buffer=True)

        """
        self._finalized_config: VerifiedGraphicsConfig | None = None
        self._attributes = {}
        self._user_set_attributes = set()

        # Fetch the type hints dynamically from the class itself
        attribute_types = get_type_hints(self)

        # Initialize defaults or user-specified values
        for attr_name, attr_type in attribute_types.items():
            default_value = getattr(self, attr_name, None)

            # Set user-provided values or fallback to default
            if attr_name in kwargs:
                user_value = kwargs[attr_name]
                if isinstance(user_value, attr_type):
                    self._attributes[attr_name] = user_value
                    self._user_set_attributes.add(attr_name)  # Track user-set attributes
                    setattr(self, attr_name, user_value)
                else:
                    msg = f"Incorrect type for {attr_name}. Expected {attr_type.__name__}."
                    raise TypeError(msg)
            else:
                self._attributes[attr_name] = default_value
                setattr(self, attr_name, default_value)

    @abstractmethod
    def match(self, window: Window) -> VerifiedGraphicsConfig | None:
        """Matches this config to a given platform Window.

        The subclassed platform config must handle setting the FinalizedAttributes values.

        Returns:
             `True` or `False` the given window matches the OpenGL configuration.
        """

    @property
    def is_finalized(self) -> bool:
        return False

    @classmethod
    def available_attributes(cls) -> dict:
        """Return a list of available attribute names, types, and their default values."""
        attributes = {}
        attribute_types = get_type_hints(cls)
        for attr_name, attr_type in attribute_types.items():
            default_value = getattr(cls, attr_name, None)
            attributes[attr_name] = (attr_type, default_value)
        return attributes

    @property
    def user_set_attributes(self) -> set[str]:
        """Return a set of attribute names that were explicitly set by the user."""
        return self._user_set_attributes


class WindowTransformations:
    def __init__(self, window, projection, view, model):
        self._window = window
        self._projection = projection
        self._view = view
        self._model = model

    @property
    def projection(self) -> Mat4:
        return self._projection

    @projection.setter
    def projection(self, projection: Mat4) -> None:
        self._projection = projection

    @property
    def view(self) -> Mat4:
        return self._view

    @view.setter
    def view(self, view: Mat4) -> None:
        self._view = view

    @property
    def model(self) -> Mat4:
        return self._model

    @model.setter
    def model(self, model: Mat4) -> None:
        self._model = model


class UBOMatrixTransformations(WindowTransformations):  # noqa: D101
    ...

class GraphicsResource(Protocol):  # noqa: D101
    def delete(self) -> None:
        ...

class ResourceManagement:
    """A manager to handle the freeing of resources for an API.

    In some graphical API's, the order in which you free resources can be very specific.
    """
    managers: list[GraphicsResource]
    weak_resources: weakref.WeakSet[GraphicsResource]

    def __init__(self) -> None:  # noqa: D107
        self._func = None
        self.managers = []
        self.weak_resources = weakref.WeakSet()
        atexit.register(self.on_exit_cleanup)

    def set_pre_cleanup_func(self, func: Callable) -> None:
        """Register a function to be called before cleanup.

        Some API's may need to enforce a sync before cleanup.
        """
        self._func = func

    def register_manager(self, resource: GraphicsResource) -> None:
        """A manager handles multiple resources, these will be called in reverse order on cleanup."""
        self.managers.append(resource)

    def register_resource(self, resource: GraphicsResource) -> None:
        """Registers a resource as a weak reference.

        Some resources do not have a manager, but they do need to be freed before others. Keeping them permanently
        may prevent them from being garbage collected prior to shutdown.
        """
        self.weak_resources.add(resource)

    def on_exit_cleanup(self) -> None:
        """Cleans up all graphical resources that have been registered on application exit."""
        self.cleanup_all()

    def cleanup_all(self) -> None:
        """Cleans up all graphical resources that have been registered.

        Weak resources registered are destroyed first.

        Managers are called last, and in reverse order of registered.
        """
        if self._func:
            self._func()

        for resource in self.weak_resources:
            resource.delete()
        for resource in reversed(self.managers):
            resource.delete()
