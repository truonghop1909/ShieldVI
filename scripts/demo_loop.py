"""Opt-in demo loop: Windows Selector avoids observed Proactor accept failure.

The demo ASGI server never starts subprocesses; workers are separately owned by
the launcher. Production factories/uvicorn settings are deliberately unchanged.
"""
import asyncio

def new_event_loop():
    return asyncio.SelectorEventLoop()
