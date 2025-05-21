"""Subscription-observer pattern for MQTT subscriptions."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from homeassistant.components import mqtt
from homeassistant.core import HomeAssistant, callback

if TYPE_CHECKING:
    from collections.abc import Callable

_LOGGER = logging.getLogger(__name__)


class AbstractMqttSubscriptionSubject(ABC):
    """Interface for MQTT message subscription subjects."""

    @abstractmethod
    async def async_attach(
        self, topic: str, observer: AbstractMqttSubscriptionObserver
    ) -> None:
        """Register observer on certain topic."""

    @abstractmethod
    def detach(self, topic: str, observer: AbstractMqttSubscriptionObserver) -> None:
        """Unregister observer on topic."""


class AbstractMqttSubscriptionObserver(ABC):
    """Interface for MQTT message receivers."""

    @abstractmethod
    def notify_observer(
        self, subject: AbstractMqttSubscriptionSubject, msg: mqtt.models.ReceiveMessage
    ) -> None:
        """Call on MQTT message received."""


class MqttSubscriptionSubject(AbstractMqttSubscriptionSubject):
    """
    MQTT subscription subject.

    Each observer only receives messages on its own topic.
    """

    _observers: dict[str, AbstractMqttSubscriptionObserver]
    _call_on_unsubscribe: dict[str, Callable[[], None]]

    _instance = None

    @classmethod
    def get_instance(cls, hass: HomeAssistant) -> MqttSubscriptionSubject:
        """Get unique class instance or create new if it doesn't exist."""
        if cls._instance is None:
            cls._instance = cls(hass)
        return cls._instance

    def __init__(self, hass: HomeAssistant) -> None:
        """Create new instance."""
        self._observers = {}
        self._call_on_unsubscribe = {}

        self.hass = hass

    async def _async_subscribe_to_topic(
        self,
        topic: str,
        observer: AbstractMqttSubscriptionObserver,
    ) -> Callable[[], None]:
        @callback
        async def message_received(
            msg: mqtt.models.ReceiveMessage,
            entity: AbstractMqttSubscriptionObserver = observer,
        ) -> None:
            """Received MQTT message."""
            _LOGGER.debug(
                "Received message on topic %s: %s", msg.topic, str(msg.payload)
            )
            entity.notify_observer(self, msg)

        return await mqtt.async_subscribe(self.hass, topic, message_received)

    async def async_attach(
        self,
        topic: str,
        observer: AbstractMqttSubscriptionObserver,
    ) -> None:
        """Register observer on certain topic."""
        res = await self._async_subscribe_to_topic(topic, observer)

        self._observers[topic] = observer
        self._call_on_unsubscribe[topic] = res

        _LOGGER.debug("Subscribed to topic %s", topic)

    def detach(self, topic: str, _observer: AbstractMqttSubscriptionObserver) -> None:
        """Unregister observer on topic."""
        self._observers.pop(topic)

        self._call_on_unsubscribe[topic]()

        _LOGGER.debug("Unsubcribed from topic %s", topic)
