"""
Test Suite for Pyglet
=====================

NOTE: This description is desired implementation. Still in progress.

The test suite is divided in the following segments:
    - unit tests
    - integration tests
    - interactive test

The unit and integration tests should run without user interaction. Unit tests are limited to
functionality contained in a single module/entity, while integration tests test integration
between different modules and towards the system.
Interactive tests require human interaction to validate the outcomes. They are mostly about
verifying display of rendering.

If any test requires external data files, please put them in the appropriate data directory. This
way the tests can share a limited set of resources.

Running unit and integration tests
----------------------------------
To run the unit tests call:
    python -m unittest discover tests.unit

To run the integration tests call:
    python -m unittest discover tests.integration

These tests should run fully automatic in a limited amount of time. The integration tests might
spawn windows for rendering. No need to interact with these windows.

Running interactive tests
-------------------------
To run the interactive tests call:
    python tests/integration/test.py

These tests require human interaction, so be ready to follow the instructions.
"""
