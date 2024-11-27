"""Run list encoding utilities."""
from __future__ import annotations

from typing import Any, Callable, Generator, Iterable, Iterator


class _Run:
    def __init__(self, value: Any, count: int) -> None:
        self.value = value
        self.count = count

    def __repr__(self) -> str:
        return f"Run({self.value}, {self.count})"


class RunList:
    """List of contiguous runs of values.

    A `RunList` is an efficient encoding of a sequence of values.  For
    example, the sequence ``aaaabbccccc`` is encoded as ``(4, a), (2, b),
    (5, c)``.  The class provides methods for modifying and querying the
    run list without needing to deal with the tricky cases of splitting and
    merging the run list entries.

    Run lists are used to represent formatted character data in pyglet.  A
    separate run list is maintained for each style attribute, for example,
    weight, italic, font size, and so on.  Unless you are overriding the
    document interfaces, the only interaction with run lists is via
    `RunIterator`.

    The length and ranges of a run list always refer to the character
    positions in the decoded list.  For example, in the above sequence,
    ``set_run(2, 5, 'x')`` would change the sequence to ``aaxxxbccccc``.
    """
    runs: list[_Run]

    def __init__(self, size: int, initial: Any) -> None:
        """Create a run list of the given size and a default value.

        Args:
            size:
                Number of characters to represent initially.
            initial:
                The value of all characters in the run list.

        """
        self.runs = [_Run(initial, size)]

    def insert(self, pos: int, length: int) -> None:
        """Insert characters into the run list.

        The inserted characters will take on the value immediately preceding
        the insertion point (or the value of the first character, if `pos` is
        0).

        Args:
            pos:
                Insertion index
            length:
                Number of characters to insert.

        """
        i = 0
        for run in self.runs:
            if i <= pos <= i + run.count:
                run.count += length
                break
            i += run.count

    def delete(self, start: int, end: int) -> None:
        """Remove characters from the run list.

        Args:
            start:
                Starting index to remove from.
            end:
                End index, exclusive.

        """
        i = 0

        for run in self.runs:
            if end - start == 0:
                break
            if i <= start <= i + run.count:
                trim = min(end - start, i + run.count - start)
                run.count -= trim
                end -= trim
            i += run.count
        self.runs = [r for r in self.runs if r.count > 0]

        # Don't leave an empty list
        if not self.runs:
            self.runs = [_Run(run.value, 0)]

    def set_run(self, start: int, end: int, value: Any) -> None:
        """Set the value of a range of characters.

        Args:
            start:
                Start index of range.
            end:
                End of range, exclusive.
            value:
                Value to set over the range.

        """
        if end - start <= 0:
            return

        # Find runs that need to be split
        i = 0
        start_i = None
        start_trim = 0
        end_i = None
        end_trim = 0
        for run_i, run in enumerate(self.runs):
            count = run.count
            if i < start < i + count:
                start_i = run_i
                start_trim = start - i
            if i < end < i + count:
                end_i = run_i
                end_trim = end - i
            i += count

        # Split runs
        if start_i is not None:
            run = self.runs[start_i]
            self.runs.insert(start_i, _Run(run.value, start_trim))
            run.count -= start_trim
            if end_i is not None:
                if end_i == start_i:
                    end_trim -= start_trim
                end_i += 1
        if end_i is not None:
            run = self.runs[end_i]
            self.runs.insert(end_i, _Run(run.value, end_trim))
            run.count -= end_trim

        # Set new value on runs
        i = 0
        for run in self.runs:
            if start <= i and i + run.count <= end:
                run.value = value
            i += run.count

        # Merge adjacent runs
        last_run = self.runs[0]
        for run in self.runs[1:]:
            if run.value == last_run.value:
                run.count += last_run.count
                last_run.count = 0
            last_run = run

        # Delete collapsed runs
        self.runs = [r for r in self.runs if r.count > 0]

    def append(self, length: int):
        """Append characters into end of the run list.

        The appended characters will take on the value immediately preceding
        the end of run list.

        Args:
            length:
                Number of characters to insert.

        """
        self.runs[-1].count += length

    def append_run(self, count: int, value: Any) -> None:
        """
        Append a run to the end of the run list.

        Args:
            count:
                Number of characters to append.
            value:
                Value to append.
        """
        if self.runs[-1].value == value:
            self.runs[-1].count += count
            return
        self.runs.append(_Run(value, count))

    def insert_run(self, pos: int, length: int, value: Any) -> None:
        """
        Insert a run into the run list.

        Args:
            pos:
                Position to insert run.
            length:
                Number of characters to insert.
            value:
                Value to insert.
        """
        i = 0
        for run_i, run in enumerate(self.runs):
            if i <= pos <= i + run.count:
                if run.value == value:
                    run.count += length
                else:
                    self.runs.insert(run_i + 1, _Run(value, length))
                    self.runs.insert(run_i + 2, _Run(run.value, run.count - (pos - i)))
                    run.count = pos - i
                    # Delete collapsed runs
                    self.runs[run_i: run_i+2] = [r for r in self.runs[run_i: run_i+2] if r.count > 0]
                break
            i += run.count

    def __iter__(self) -> Generator[tuple[int, int, Any], Any, None]:
        i = 0
        for run in self.runs:
            yield i, i + run.count, run.value
            i += run.count

    def get_run_iterator(self) -> RunIterator:
        """Get an extended iterator over the run list."""
        return RunIterator(self)

    def __getitem__(self, index: int) -> Any:
        """Get the value at a character position.

        Args:
            index:
                Index of character.  Must be within range and non-negative.

        """
        i = 0
        for run in self.runs:
            if i <= index < i + run.count:
                return run.value
            i += run.count

        # Append insertion point
        if index == i:
            return self.runs[-1].value

        raise IndexError

    def set_runs(self, start: int, end: int, runs: RunList) -> None:
        """Set a range of runs.

        Args:
            start:
                Start index of range.
            end:
                End index of range, exclusive.
            runs:
                Runs to set.
        """
        if end - start <= 0:
            return

        # Find runs that need to be split
        i = 0
        start_i = None
        start_trim = 0
        end_i = None
        end_trim = 0
        for run_i, run in enumerate(self.runs):
            count = run.count
            if i < start < i + count:
                start_i = run_i
                start_trim = start - i
            if i < end < i + count:
                end_i = run_i
                end_trim = end - i
            i += count

        # Split runs
        if start_i is not None:
            run = self.runs[start_i]
            self.runs.insert(start_i, _Run(run.value, start_trim))
            run.count -= start_trim
            if end_i is not None:
                if end_i == start_i:
                    end_trim -= start_trim
                end_i += 1
            start_i += 1
        if end_i is not None:
            run = self.runs[end_i]
            self.runs.insert(end_i, _Run(run.value, end_trim))
            run.count -= end_trim
            end_i += 1

        self.runs[start_i: end_i] = runs.runs

        # Merge adjacent runs
        last_run = self.runs[0]
        for run in self.runs[1:]:
            if run.value == last_run.value:
                run.count += last_run.count
                last_run.count = 0
            last_run = run

        # Delete collapsed runs
        self.runs = [r for r in self.runs if r.count > 0]

    def __repr__(self) -> str:
        return str(list(self))


class AbstractRunIterator:
    """Range iteration over `RunList`.

    `AbstractRunIterator` objects allow any monotonically non-decreasing
    access of the iteration, including repeated iteration over the same index.
    Use the ``[index]`` operator to get the value at a particular index within
    the document.  For example::

        run_iter = iter(run_list)
        value = run_iter[0]
        value = run_iter[0]       # non-decreasing access is OK
        value = run_iter[15]
        value = run_iter[17]
        value = run_iter[16]      # this is illegal, the index decreased.

    Using `AbstractRunIterator` to access increasing indices of the value runs
    is more efficient than calling `RunList.__getitem__` repeatedly.

    You can also iterate over monotonically non-decreasing ranges over the
    iteration.  For example::

        run_iter = iter(run_list)
        for start, end, value in run_iter.ranges(0, 20):
            pass
        for start, end, value in run_iter.ranges(25, 30):
            pass
        for start, end, value in run_iter.ranges(30, 40):
            pass

    Both start and end indices of the slice are required and must be positive.
    """

    def __getitem__(self, index: int) -> Any:
        """Get the value at a given index.

        See the class documentation for examples of valid usage.

        Args:
            index:
                Document position to query.
        """
        raise NotImplementedError("abstract")

    def ranges(self, start: int, end: int) -> Generator[tuple[int, int, Any], None, None]:
        """Iterate over a subrange of the run list.

        See the class documentation for examples of valid usage.

        Args:
            start:
                Start index to iterate from.
            end:
                End index, exclusive.

        Returns:
            Iterator over (start, end, value) tuples.
        """
        raise NotImplementedError("abstract")


class RunIterator(AbstractRunIterator):
    _run_list_iter: Iterator[AbstractRunIterator]

    def __init__(self, run_list: Iterable[AbstractRunIterator] | RunList) -> None:
        self._run_list_iter = iter(run_list)
        self.start, self.end, self.value = next(self)

    def __next__(self) -> AbstractRunIterator:
        return next(self._run_list_iter)

    def __getitem__(self, index: int) -> Any:
        try:
            while index >= self.end and index > self.start:
                # condition has special case for 0-length run (fixes issue 471)
                self.start, self.end, self.value = next(self)
            return self.value
        except StopIteration:
            raise IndexError

    def ranges(self, start: int, end: int) -> Generator[tuple[int, int, Any], None, None]:
        try:
            while start >= self.end:
                self.start, self.end, self.value = next(self)
            yield start, min(self.end, end), self.value
            while end > self.end:
                self.start, self.end, self.value = next(self)
                yield self.start, min(self.end, end), self.value
        except StopIteration:
            return


class OverriddenRunIterator(AbstractRunIterator):
    """Iterator over a `RunIterator`, with a value temporarily replacing a given range."""

    def __init__(self, base_iterator: AbstractRunIterator, start: int, end: int, value: Any) -> None:
        """Create a derived iterator.

        Args:
            base_iterator:
                Source of runs.
            start:
                Start of range to override
            end:
                End of range to override, exclusive
            value:
                Value to replace over the range

        """
        self.iter = base_iterator
        self.override_start = start
        self.override_end = end
        self.override_value = value

    def ranges(self, start: int, end: int) -> Generator[tuple[int, int, Any], None, None]:
        if end <= self.override_start or start >= self.override_end:
            # No overlap
            for r in self.iter.ranges(start, end):
                yield r
        else:
            # Overlap: before, override, after
            if start < self.override_start < end:
                for r in self.iter.ranges(start, self.override_start):
                    yield r
            yield (max(self.override_start, start),
                   min(self.override_end, end),
                   self.override_value)
            if start < self.override_end < end:
                for r in self.iter.ranges(self.override_end, end):
                    yield r

    def __getitem__(self, index: int) -> Any:
        if self.override_start <= index < self.override_end:
            return self.override_value

        return self.iter[index]


class FilteredRunIterator(AbstractRunIterator):
    """Iterate over an `AbstractRunIterator` with filtered values replaced by a default value."""

    def __init__(self, base_iterator: AbstractRunIterator, filter_func: Callable[[Any], bool], default: Any) -> None:
        """Create a filtered run iterator.

        Args:
            base_iterator:
                Source of runs.
            filter_func:
                Function taking a value as parameter, and returning ``True``
                if the value is acceptable, and ``False`` if the default value
                should be substituted.
            default:
                Default value to replace filtered values.

        """
        self.iter = base_iterator
        self.filter = filter_func
        self.default = default

    def ranges(self, start: int, end: int) -> Generator[tuple[int, int, Any], None, None]:
        for start_, end_, value in self.iter.ranges(start, end):
            if self.filter(value):
                yield start_, end_, value
            else:
                yield start_, end_, self.default

    def __getitem__(self, index: int) -> Any:
        value = self.iter[index]
        if self.filter(value):
            return value
        return self.default


class ZipRunIterator(AbstractRunIterator):
    """Iterate over multiple run iterators concurrently."""
    range_iterators: tuple[RunIterator, ...]

    def __init__(self, range_iterators: tuple[RunIterator, ...]) -> None:
        """Create a zipped run iterator.

        Args:
            range_iterators:
                A tuple of ranged iterators.

        """
        self.range_iterators = range_iterators

    def ranges(self, start: int, end: int) -> Generator[tuple[int, int, Any], None, None]:
        try:
            iterators = [i.ranges(start, end) for i in self.range_iterators]
            starts, ends, values = zip(*[next(i) for i in iterators])
            starts = list(starts)
            ends = list(ends)
            values = list(values)
            while start < end:
                min_end = min(ends)
                yield start, min_end, values
                start = min_end
                for i, iterator in enumerate(iterators):
                    if ends[i] == min_end:
                        starts[i], ends[i], values[i] = next(iterator)
        except StopIteration:
            return

    def __getitem__(self, index: int) -> Any:
        return [i[index] for i in self.range_iterators]


class ConstRunIterator(AbstractRunIterator):
    """Iterate over a constant value without creating a RunList."""
    length: int
    end: int
    value: Any

    def __init__(self, length: int, value: Any) -> None:
        self.length = length
        self.end = length
        self.value = value

    def __next__(self) -> Generator[tuple[int, int, Any], Any, None]:
        yield 0, self.length, self.value

    def ranges(self, start: int, end: int) -> Generator[tuple[int, int, Any], None, None]:
        yield start, end, self.value

    def __getitem__(self, index: int) -> Any:
        return self.value
