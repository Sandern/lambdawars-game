"""
Swarm keeper signals
"""
from core.dispatch import Signal

keeperworldloaded = Signal(providing_args=["keeperworld"])


updatealltasks = Signal(providing_args=["owner"])