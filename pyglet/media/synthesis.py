from __future__ import annotations

import math as _math
import struct as _struct

from typing import TYPE_CHECKING
from random import uniform as _uniform
from dataclasses import dataclass, field

from pyglet.media.codecs.base import AudioData, AudioFormat, Source

if TYPE_CHECKING:
    from typing import Generator


# Envelope classes:

class Envelope:
    """Base class for SynthesisSource amplitude envelopes.

    Custom Envelopes need only provide a single `get_generator`
    method that takes the sample rate, and duration as arguments.
    """

    def get_generator(self, sample_rate: float, duration: float) -> Generator[float]:
        """Get a generator instance.

        Args:
            sample_rate:
                The sample rate of the Source this will be applied to.
            duration:
                The duration of the Source. This is used to calculate
                the number of bytes for some Envelopes.
        """
        raise NotImplementedError


class FlatEnvelope(Envelope):
    """A flat envelope, providing basic amplitude setting.

    Args:
        amplitude:
            The amplitude (volume) of the wave, from 0.0 to 1.0.
            Values outside this range will be clamped.
    """

    def __init__(self, amplitude: float = 0.5):
        self.amplitude = max(min(1.0, amplitude), 0)

    def get_generator(self, sample_rate: float | None = None, duration: float | None = None) -> Generator[float]:
        amplitude = self.amplitude
        while True:
            yield amplitude


class LinearDecayEnvelope(Envelope):
    """A linearly decaying envelope.

    This envelope linearly decays the amplitude from the peak value
    to 0, over the length of the waveform.

    Args:
        peak:
            The Initial peak value of the envelope, from 0.0 to 1.0.
            Values outside this range will be clamped.
    """

    def __init__(self, peak: float = 1.0):
        self.peak = max(min(1.0, peak), 0)

    def get_generator(self, sample_rate: float, duration: float) -> Generator[float]:
        peak = self.peak
        total_bytes = int(sample_rate * duration)
        for i in range(total_bytes):
            yield (total_bytes - i) / total_bytes * peak
        while True:
            yield 0


class ADSREnvelope(Envelope):
    """A four-part Attack, Decay, Suspend, Release envelope.

    This is a four part ADSR envelope. The attack, decay, and release
    parameters should be provided in seconds. For example, a value of
    0.1 would be 100ms. The sustain_amplitude parameter affects the
    sustain volume. This defaults to a value of 0.5, but can be provided
    on a scale from 0.0 to 1.0.

    Args:
        attack:
            The attack time, in seconds.
        decay:
            The decay time, in seconds.
        release:
            The release time, in seconds.
        sustain_amplitude:
            The sustain amplitude (volume), from 0.0 to 1.0.
    """

    def __init__(self, attack: float, decay: float, release: float, sustain_amplitude: float = 0.5):
        self.attack = attack
        self.decay = decay
        self.release = release
        self.sustain_amplitude = max(min(1.0, sustain_amplitude), 0)

    def get_generator(self, sample_rate: float, duration: float) -> Generator[float]:
        sustain_amplitude = self.sustain_amplitude
        total_bytes = int(sample_rate * duration)
        attack_bytes = int(sample_rate * self.attack)
        decay_bytes = int(sample_rate * self.decay)
        release_bytes = int(sample_rate * self.release)
        sustain_bytes = total_bytes - attack_bytes - decay_bytes - release_bytes
        # Guard against zero-length phases to avoid division by zero. A missing
        # phase produces no samples, so its step value is never used:
        decay_step = 0.0 if not decay_bytes else (1 - sustain_amplitude) / decay_bytes
        release_step = 0.0 if not release_bytes else sustain_amplitude / release_bytes
        for i in range(1, attack_bytes + 1):
            yield i / attack_bytes
        for i in range(1, decay_bytes + 1):
            yield 1 - (i * decay_step)
        for i in range(1, sustain_bytes + 1):
            yield sustain_amplitude
        for i in range(1, release_bytes + 1):
            yield sustain_amplitude - (i * release_step)
        while True:
            yield 0


class TremoloEnvelope(Envelope):
    """A tremolo envelope, for modulation amplitude.

    A tremolo envelope that modulates the amplitude of the
    waveform with a sinusoidal pattern. The depth and rate
    of modulation can be specified. Depth is calculated as
    a percentage of the maximum amplitude. For example:
    a depth of 0.2 and amplitude of 0.5 will fluctuate
    the amplitude between 0.4 an 0.5.

    Args:
        depth:
            The amount of fluctuation, from 0.0 to 1.0.
        rate:
            The fluctuation frequency, in seconds.
        amplitude:
            The peak amplitude (volume), from 0.0 to 1.0.
    """

    def __init__(self, depth: float, rate: float, amplitude: float = 0.5):
        self.depth = max(min(1.0, depth), 0)
        self.rate = rate
        self.amplitude = max(min(1.0, amplitude), 0)

    def get_generator(self, sample_rate: float, duration: float) -> Generator[float]:
        total_bytes = int(sample_rate * duration)
        period = total_bytes / duration
        max_amplitude = self.amplitude
        min_amplitude = max(0.0, (1.0 - self.depth) * self.amplitude)
        step = (_math.pi * 2) / period / self.rate
        for i in range(total_bytes):
            value = _math.sin(step * i)
            yield value * (max_amplitude - min_amplitude) + min_amplitude
        while True:
            yield 0


# Waveform generators

def silence_generator(frequency: float, sample_rate: float) -> Generator[float]:
    while True:
        yield 0.0


def noise_generator(frequency: float, sample_rate: float) -> Generator[float]:
    while True:
        yield _uniform(-1.0, 1.0)


def sine_generator(frequency: float, sample_rate: float) -> Generator[float]:
    step = 2.0 * _math.pi * frequency / sample_rate
    i = 0.0
    while True:
        yield _math.sin(i * step)
        i += 1.0


def triangle_generator(frequency: float, sample_rate: float) -> Generator[float]:
    step = 4.0 * frequency / sample_rate
    value = 0.0
    while True:
        if value > 1.0:
            value = 1.0 - (value - 1.0)
            step = -step
        if value < -1.0:
            value = -1.0 - (value - -1.0)
            step = -step
        yield value
        value += step


def sawtooth_generator(frequency: float, sample_rate: float) -> Generator[float]:
    period_length = int(sample_rate / frequency)
    step = 2.0 * frequency / sample_rate
    i = 0.0
    while True:
        yield step * (i % period_length) - 1.0
        i += 1.0


def pulse_generator(frequency: float, sample_rate: float, duty_cycle: float = 50.0) -> Generator[float]:
    period_length = int(sample_rate / frequency)
    duty_cycle = int(duty_cycle * period_length / 100)
    i = 0.0
    while True:
        yield int(i % period_length < duty_cycle) * 2.0 - 1.0
        i += 1.0


# Source classes:

class SynthesisSource(Source):
    """Base class for synthesized waveforms.

    Args:
        generator:
            A waveform generator that produces a stream of floats from (-1.0, 1.0)
        duration:
            The length, in seconds, of audio that you wish to generate.
        sample_rate:
            Audio samples per second. (CD quality is 44100).
        envelope:
            An optional Envelope to apply to the waveform.
    """
    def __init__(self, generator: Generator, duration: float, sample_rate: int = 44800, envelope: Envelope | None = None):
        self._generator = generator
        self._duration = duration
        self.audio_format = AudioFormat(channels=1, sample_size=16, sample_rate=sample_rate)

        self._envelope = envelope or FlatEnvelope(amplitude=1.0)
        self._envelope_generator = self._envelope.get_generator(sample_rate, duration)

        # Two bytes per sample (16-bit):
        self._bytes_per_second = sample_rate * 2
        # Maximum offset, aligned to sample:
        self._max_offset = int(self._bytes_per_second * duration) & 0xfffffffe
        self._offset = 0

    def get_audio_data(self, num_bytes: int) -> AudioData | None:
        """Return ``num_bytes`` bytes of audio data."""
        num_bytes = min(num_bytes, self._max_offset - self._offset)
        if num_bytes <= 0:
            return None

        self._offset += num_bytes

        # Generate bytes:
        samples = num_bytes >> 1
        generator = self._generator
        envelope = self._envelope_generator
        sample_data = (int(next(generator) * next(envelope) * 0x7fff) for _ in range(samples))
        data = _struct.pack(f"{samples}h", *sample_data)

        return AudioData(data, num_bytes)

    def seek(self, timestamp: float) -> None:
        # Bound within duration & align to sample:
        offset = int(timestamp * self._bytes_per_second)
        self._offset = min(max(offset, 0), self._max_offset) & 0xfffffffe
        self._envelope_generator = self._envelope.get_generator(self.audio_format.sample_rate, self._duration)

    def is_precise(self) -> bool:
        return True


class Silence(SynthesisSource):
    def __init__(self, duration: float, frequency: int = 440, sample_rate: int = 44800,
                 envelope: Envelope | None = None):
        """Create a Silent waveform."""
        super().__init__(silence_generator(frequency, sample_rate), duration, sample_rate, envelope)


class WhiteNoise(SynthesisSource):
    def __init__(self, duration: float, frequency: int = 440, sample_rate: int = 44800,
                 envelope: Envelope | None = None):
        """Create a random white noise waveform."""
        super().__init__(noise_generator(frequency, sample_rate), duration, sample_rate, envelope)


class Sine(SynthesisSource):
    def __init__(self, duration: float, frequency: int = 440, sample_rate: int = 44800,
                 envelope: Envelope | None = None):
        """Create a sinusoid (sine) waveform."""
        super().__init__(sine_generator(frequency, sample_rate), duration, sample_rate, envelope)


class Square(SynthesisSource):
    def __init__(self, duration: float, frequency: int = 440, sample_rate: int = 44800,
                 envelope: Envelope | None = None):
        """Create a Square (pulse) waveform."""
        super().__init__(pulse_generator(frequency, sample_rate), duration, sample_rate, envelope)


class Triangle(SynthesisSource):
    def __init__(self, duration: float, frequency: int = 440, sample_rate: int = 44800,
                 envelope: Envelope | None = None):
        """Create a Triangle waveform."""
        super().__init__(triangle_generator(frequency, sample_rate), duration, sample_rate, envelope)


class Sawtooth(SynthesisSource):
    def __init__(self, duration: float, frequency: int = 440, sample_rate: int = 44800,
                 envelope: Envelope | None = None):
        """Create a Sawtooth waveform."""
        super().__init__(sawtooth_generator(frequency, sample_rate), duration, sample_rate, envelope)


#############################################
#   Multi-operator FM synthesis:
#############################################

@dataclass
class Algorithm:
    """Describes how the FM operators are routed.

    An algorithm is a plain description of operator routing built by assigning
    its attributes::

        algorithm = Algorithm("My patch")
        algorithm.carriers = [3]
        algorithm.modulations = [(0, 1), (1, 2)]
        algorithm.feedback = 0

    Validation and evaluation ordering are performed by :class:`FMVoice` when
    the algorithm is compiled.

    Attributes:
        name:
            A descriptive name for the algorithm.
        carriers:
            Operator indices whose output is mixed into the voice.
        modulations:
            ``(source, target)`` pairs. ``source`` phase-modulates ``target``.
        feedback:
            Operator index that feeds back into itself, or ``None``.
    """

    name: str = ""
    carriers: list[int] = field(default_factory=list)
    modulations: list[tuple[int, int]] = field(default_factory=list)
    feedback: int | None = None


class Operator:
    """A single FM operator with optional feedback."""

    def __init__(self, frequency: float = 440.0, sample_rate: int = 44800, index: float = 1.0, feedback: float = 0.0):
        self.sample_rate = sample_rate
        self.index = index
        self.feedback = feedback

        self._frequency = frequency
        self._step = 2.0 * _math.pi * frequency / sample_rate
        self._phase = 0.0
        self._last = 0.0

    @property
    def frequency(self) -> float:
        return self._frequency

    @frequency.setter
    def frequency(self, value: float) -> None:
        self._frequency = value
        self._step = 2.0 * _math.pi * value / self.sample_rate

    def process(self, modulation: float = 0.0) -> float:
        """Return the next sample, given the summed modulator input."""
        modulation += self.feedback * self._last
        value = _math.sin(self._phase + self.index * modulation)
        self._last = value
        self._phase = (self._phase + self._step) % _math.tau
        return value

    def reset(self) -> None:
        self._phase = 0.0
        self._last = 0.0


class FMVoice(SynthesisSource):
    """4-operator FM voice.

    Args:
        duration:
            The length, in seconds, of audio to generate.
        algorithm:
            The operator routing. Defaults to ``ALGORITHM_0``.
        sample_rate:
            Audio samples per second.
        feedback_level:
            The amount of self-feedback applied to the algorithm's feedback
            operator.
        envelope:
            An optional master amplitude envelope.
    """

    def __init__(
        self,
        duration: float,
        algorithm: Algorithm | None = None,
        sample_rate: int = 44800,
        feedback_level: float = 0.0,
        envelope: Envelope | None = None,
    ):
        self.sample_rate = sample_rate
        self.ops: list[Operator] = [Operator(frequency=440.0, sample_rate=sample_rate) for _ in range(4)]
        self._values = [0.0] * 4
        self._feedback_level = feedback_level

        self._algorithm = algorithm or ALGORITHM_0
        self._compile_algorithm()

        super().__init__(self._get_generator(), duration, sample_rate, envelope)

    # ----- internal -----

    def _compile_algorithm(self) -> None:
        self._order = self._build_evaluation_order()

        self._carriers = tuple(self._algorithm.carriers)
        self._modulator_sources: list[list[int]] = [[] for _ in range(4)]

        for source, target in self._algorithm.modulations:
            self._modulator_sources[target].append(source)

        self.set_feedback(self._feedback_level)

    def _build_evaluation_order(self) -> tuple[int, ...]:
        """Validate ``algorithm`` and return operator indices in render order.

        Modulators are returned before the operators they feed so each operator
        advances exactly once per audio sample. Raises ``ValueError`` if the
        routing is invalid or its modulation graph contains a cycle.
        """
        algorithm = self._algorithm

        # Every referenced operator must be an integer index in 0..3:
        def check(operator, role):
            if not isinstance(operator, int) or not 0 <= operator <= 3:
                raise ValueError(f"{role.capitalize()} operator must be an index in 0..3, got {operator!r}")

        seen = set()

        # A voice needs at least one carrier to render...
        if not algorithm.carriers:
            raise ValueError("Algorithm must define at least one carrier")
        if len(set(algorithm.carriers)) != len(algorithm.carriers):
            raise ValueError("Carrier operators must be unique")
        for carrier in algorithm.carriers:
            check(carrier, "carrier")
            seen.add(carrier)

        modulations = list(algorithm.modulations)
        # Modulations must be valid, non-self and unique pairs. Duplicate detection
        # is done on unpacked index tuples so a malformed or unhashable modulation
        # reports "Invalid modulation" / "Duplicate modulation" instead of leaking a
        # confusing TypeError...
        edges = set()
        for modulation in modulations:
            try:
                source, target = modulation
            except (TypeError, ValueError):
                raise ValueError(f"Invalid modulation {modulation!r}; expected a (source, target) pair") from None
            check(source, "modulator")
            check(target, "target")
            edge = (source, target)
            if edge in edges:
                raise ValueError("Duplicate modulation")
            edges.add(edge)
            seen.add(source)
            seen.add(target)
            if source == target:
                raise ValueError("An operator cannot modulate itself; use feedback instead")

        # Feedback must be a valid index and part of the routed operators...
        if algorithm.feedback is not None:
            check(algorithm.feedback, "feedback")
            seen.add(algorithm.feedback)

        # Topologically sort so each operator renders exactly once per sample.
        adjacency = [[] for _ in range(4)]
        nodes = seen
        for source, target in modulations:
            adjacency[source].append(target)

        post_order: list[int] = []
        state: dict[int, int] = {}
        path: list[int] = []

        def visit(operator: int) -> None:
            state[operator] = 1
            path.append(operator)
            for target in adjacency[operator]:
                if state.get(target) == 1:
                    cycle = path[path.index(target):] + [target]
                    raise ValueError("Modulation cycle detected: " + " -> ".join(str(item) for item in cycle))
                if state.get(target, 0) == 0:
                    visit(target)
            path.pop()
            state[operator] = 2
            post_order.append(operator)

        for operator in sorted(nodes):
            if state.get(operator, 0) == 0:
                visit(operator)

        return tuple(reversed(post_order))

    def _render_sample(self) -> float:
        values = self._values
        for operator in self._order:
            modulation = 0.0
            for source in self._modulator_sources[operator]:
                modulation += values[source]
            values[operator] = self.ops[operator].process(modulation)
        return sum(values[op] for op in self._carriers) / len(self._carriers)

    def _get_generator(self) -> Generator[float]:
        while True:
            yield self._render_sample()

    # ----- public API -----

    @property
    def algorithm(self):
        return self._algorithm

    @algorithm.setter
    def algorithm(self, algorithm: Algorithm) -> None:
        """Change the routing and recompile it for this voice."""
        if not isinstance(algorithm, Algorithm):
            raise TypeError("algorithm must be an Algorithm instance")
        self._algorithm = algorithm
        self._compile_algorithm()

    def set_feedback(self, level: float) -> None:
        """Set the amount of self-feedback for the algorithm's feedback operator."""
        self._feedback_level = level
        for op in self.ops:
            op.feedback = 0.0
        if self.algorithm.feedback is not None:
            self.ops[self.algorithm.feedback].feedback = level

    def set_frequency(self, op_index: int, frequency: float) -> None:
        self.ops[op_index].frequency = frequency

    def set_index(self, op_index: int, index: float) -> None:
        self.ops[op_index].index = index

    def seek(self, timestamp: float) -> None:
        """Reset operators when seeking."""
        for op in self.ops:
            op.reset()
        super().seek(timestamp)


# ----------------------------------------------------------------------
#               example of popular default algorithms
# ----------------------------------------------------------------------

#: Four operators in series: OP1 -> OP2 -> OP3 -> OP4.
ALGORITHM_0 = Algorithm("Algorithm 0")
ALGORITHM_0.carriers = [3]
ALGORITHM_0.modulations = [(0, 1), (1, 2), (2, 3)]
ALGORITHM_0.feedback = 0

#: OP1 and OP2 combine to modulate OP3, which modulates OP4.
ALGORITHM_1 = Algorithm("Algorithm 1")
ALGORITHM_1.carriers = [3]
ALGORITHM_1.modulations = [(0, 2), (1, 2), (2, 3)]
ALGORITHM_1.feedback = 0

#: OP2 modulates OP3; OP1 and OP3 modulate OP4.
ALGORITHM_2 = Algorithm("Algorithm 2")
ALGORITHM_2.carriers = [3]
ALGORITHM_2.modulations = [(1, 2), (2, 3), (0, 3)]
ALGORITHM_2.feedback = 0

#: OP1 modulates OP2; OP2 and OP3 modulate OP4.
ALGORITHM_3 = Algorithm("Algorithm 3")
ALGORITHM_3.carriers = [3]
ALGORITHM_3.modulations = [(0, 1), (1, 3), (2, 3)]
ALGORITHM_3.feedback = 0

#: Two independent two-operator pairs: OP1 -> OP2 and OP3 -> OP4.
ALGORITHM_4 = Algorithm("Algorithm 4")
ALGORITHM_4.carriers = [1, 3]
ALGORITHM_4.modulations = [(0, 1), (2, 3)]
ALGORITHM_4.feedback = 0

#: OP1 modulates the three carriers OP2, OP3, and OP4.
ALGORITHM_5 = Algorithm("Algorithm 5")
ALGORITHM_5.carriers = [1, 2, 3]
ALGORITHM_5.modulations = [(0, 1), (0, 2), (0, 3)]
ALGORITHM_5.feedback = 0

#: OP1 modulates OP2; OP3 and OP4 are unmodulated carriers.
ALGORITHM_6 = Algorithm("Algorithm 6")
ALGORITHM_6.carriers = [1, 2, 3]
ALGORITHM_6.modulations = [(0, 1)]
ALGORITHM_6.feedback = 0

#: Four parallel unmodulated carriers.
ALGORITHM_7 = Algorithm("Algorithm 7")
ALGORITHM_7.carriers = [0, 1, 2, 3]
ALGORITHM_7.modulations = []
ALGORITHM_7.feedback = 0

#: A single modulator/carrier pair, as used by OPLL/VRC7-style patches.
ALGORITHM_2OP = Algorithm("2-operator FM")
ALGORITHM_2OP.carriers = [1]
ALGORITHM_2OP.modulations = [(0, 1)]
ALGORITHM_2OP.feedback = 0
