from __future__ import annotations
import logging
import time
from abc import abstractmethod, ABC
from typing import final, TypeVar, Type, Callable, Optional, Hashable, Any

logger = logging.getLogger()
INDENT = '    '
T = TypeVar('T')

class Updater(ABC):
    """ABC Updater.
    Model for a container which maintains mutable data and needs to update different parts of it in a controlled way.
    """

    @classmethod
    @abstractmethod
    def update_item(cls: Type[Updater], original: T, update: T) -> None:
        """Updater.update_item
        Updated the first argument by interpreting the second as the update.
        """
        if cls.is_atomic(type(original)):
            raise TypeError(
                "Updater {upd} cannot update type {tp}".format(
                    upd=cls, tp=type(original))
            )

    @final
    @classmethod
    def is_atomic(cls: Type[Updater], C: Type[T]) -> bool:
        """Updater.is_atomic
        Alias for `not Updater.is_updatable`.  Returns True if the argument is a type that cannot be updated by the calling class.
        """
        return not cls.is_updatable(C)

    @classmethod
    @abstractmethod
    def is_updatable(cls: Type[Updater], C: Type[T]) -> bool:
        """Updater.is_updatable
        Returns True if the argument is a type that can be updated by the calling class.
        """
        return NotImplemented

class Updatable(ABC):
    """ABC Updatable.
    Model for a container which can accept updates.
    """

    @classmethod
    def __subclasshook__(cls: Type[Updatable], C: Type[T]) -> bool:
        if cls is Updatable:
            if any("update" in Sup.__dict__ for Sup in C.__mro__):
                return True
        return NotImplemented

    @abstractmethod
    def update(self: Updatable, other: Updatable) -> None:
        pass

class State(Updater, Updatable):
    """ABC State.
    Model for a stateful, mutable data container.
    """

    @classmethod
    def update_item(cls: Type[State], first: T, second: T) -> None:
        """
        Raises an ArgumentException through the call to super() if called on non-Updatable objects.
        """
        super().update(first, second)
        # first.update(second)

    @abstractmethod
    def copy(self: State) -> State: ...

    @classmethod
    def is_updatable(cls: Type[State], C: Type[T]) -> bool:
        """Defines objects updatable by State containers: Other State containers."""
        return issubclass(C, Updatable)

    def __or__(self: State, other: State) -> State:
        """Enables use of `state |= update` idiom."""
        # TODO: Think of a better way to do this
        copy = self.copy()
        copy.update(other)
        return copy

class StateDict(dict, State):
    """class StateDict.
    A subclass of dict and State which recursively calls all substates' 'update' methods on update.
    """
    @final
    def __update__(self: StateDict, other: StateDict) -> None:
        for key in other:
            if key in self:
                self._update_item(key, other[key])
            else:
                self._add_item(key, other[key])

    def _update_item(self, key, val) -> None:
        try:
            self.__class__.update_item(self[key], val)
        except TypeError:
            self[key] = val

    def _add_item(self: StateDict, key: Hashable, val: Any = None) -> None:
        self[key] = val

    @final
    def update(self: StateDict, *args, **kwargs) -> None:
        self.__update__(
            self.__class__(*args, **kwargs)
        )

    def copy(self: StateDict) -> StateDict:
        return super().copy()

class View(StateDict):
    """class View.
    A State container whose keys are effectively immutable.
    In other words, it is only possible to update the keys that the View is initialized with.
    """

    def _add_item(self, key, val=None):
        pass

class History(list, Updatable):
    """class History.
    Simple container to remember state or computational information.
    Subclasses list and defines an 'update' method.
    """

    def update(self, other):
        self.extend(other)

    def push(self, item):
        self.update(item)
