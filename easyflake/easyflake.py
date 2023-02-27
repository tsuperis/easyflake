from datetime import timedelta
from typing import Union

from easyflake.clock import TimeScale
from easyflake.logging import warning
from easyflake.node.base import BaseNodeFactory as BaseNodeFactory
from easyflake.node.random import RandomNodeFactory
from easyflake.providers import TimeBasedSequenceProvider

DEFAULT_EPOCH_TIMESTAMP = 1675859040

UNSET = type("UNSET", (), {})


class EasyFlake:
    id_bits = 64

    def __init__(
        self,
        node_id: Union[int, BaseNodeFactory] = RandomNodeFactory(),
        node_id_bits: int = 8,
        sequence_bits: int = 8,
        epoch: float = DEFAULT_EPOCH_TIMESTAMP,
        time_scale: int = TimeScale.MILLI,
        **kwargs,
    ):
        """
        Class for generating 64-bit IDs similar to Snowflake or Sonyflake.

        Args:
            node_id (int): node ID of execution environment. Default to random
            node_id_bits (int): maximum number of bits in node ID part.
            sequence_bits (int): maximum number of bits in sequence ID part.
            epoch (float): Timestamp that is used as a reference when
                                     generating bits of timestamp section.
                                     Defaults to 2023-02-08T12:24:00Z.
            time_scale (int): number of decimal places in timestamp.
        """
        self._node_id_bits = node_id_bits
        self._sequence_bits = sequence_bits

        if isinstance(node_id, BaseNodeFactory):
            self._node_id = node_id.get_node_id(node_id_bits)
        else:
            self._node_id = node_id

        self._sequence_provider = TimeBasedSequenceProvider(
            bits=sequence_bits,
            epoch=epoch,
            time_scale=time_scale,
            **kwargs,
        )
        self._validate()

    def get_id(self):
        """generate next ID by current timestamp"""
        seq = self._sequence_provider.next()
        return (
            (seq.timestamp << (self._sequence_bits + self._node_id_bits))
            | (self._node_id << self._sequence_bits)
            | seq.value
        )

    def _validate(self):
        """validate attributes."""
        self._validate_sequence_bits()
        self._validate_node_id()
        self._validate_id_length()

    def _validate_node_id(self):
        if self._node_id_bits < 1:
            raise ValueError("node_id_bits is required to be >0")

        max_node_id = (1 << self._node_id_bits) - 1
        if not 0 <= self._node_id <= max_node_id:
            raise ValueError(
                f"node_id is required to be >=0 and <={max_node_id}, "
                f"but {self._node_id} is given."
            )

    def _validate_sequence_bits(self):
        if self._sequence_bits < 1:
            raise ValueError("sequence_bits is required to be >0")

    def _validate_id_length(self):
        # Check sufficient node_id bits
        if not self._has_sufficient_timestamp_bits(years=1):
            raise ValueError("Unable to count timestamp within a year.")
        if not self._has_sufficient_timestamp_bits(years=3):
            warning("Unable to count timestamp within 3 years.")

    def _has_sufficient_timestamp_bits(self, years: int):
        delta = timedelta(days=365 * years)
        timestamp_bits = self._sequence_provider.get_required_bits(delta)
        bits = timestamp_bits + self._node_id_bits + self._sequence_bits
        return bits < self.id_bits
