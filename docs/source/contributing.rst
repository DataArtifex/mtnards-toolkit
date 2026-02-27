Contributing
============

Thank you for your interest in contributing to the MTNA RDS Toolkit! This page provides 
guidelines for contributing to the project.

Getting Started
---------------

Development Setup
~~~~~~~~~~~~~~~~~

1. Fork and clone the repository:

   .. code-block:: bash

      git clone https://github.com/YOUR-USERNAME/mtnards-toolkit.git
      cd mtnards-toolkit

2. Install development dependencies:

   .. code-block:: bash

      # Using uv (recommended)
      uv sync

      # Or using pip
      pip install -e ".[dev,docs]"

3. Install pre-commit hooks:

   .. code-block:: bash

      pre-commit install

Development Workflow
--------------------

Creating a Feature Branch
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   git checkout -b feature/your-feature-name

Or for bug fixes:

.. code-block:: bash

   git checkout -b fix/bug-description

Making Changes
~~~~~~~~~~~~~~

1. Make your changes following the coding standards (see below)
2. Add tests for new functionality
3. Update documentation as needed
4. Ensure all tests pass
5. Commit your changes with clear messages

Coding Standards
----------------

Python Style
~~~~~~~~~~~~

* Follow `PEP 8 <https://pep8.org/>`_ style guidelines
* Use type hints for all public APIs
* Maximum line length: 100 characters (enforced by Ruff)

Type Hints
~~~~~~~~~~

All public functions and methods must have type hints:

.. code-block:: python

   def process_data(
       data: dict[str, Any],
       options: list[str] | None = None
   ) -> tuple[bool, str]:
       """Process data with optional parameters.
       
       Args:
           data: Input data dictionary
           options: Optional list of processing options
           
       Returns:
           Tuple of (success, message)
       """
       pass

Docstrings
~~~~~~~~~~

Use Google or NumPy style docstrings (Sphinx-compatible):

.. code-block:: python

   def example_function(param1: str, param2: int = 0) -> bool:
       """Brief description of the function.
       
       Longer description if needed, explaining the purpose
       and behavior in more detail.
       
       Args:
           param1: Description of param1
           param2: Description of param2. Defaults to 0.
           
       Returns:
           Description of return value
           
       Raises:
           ValueError: When param2 is negative
           TypeError: When param1 is not a string
           
       Example:
           >>> example_function("test", 5)
           True
       """
       pass

Prefer pathlib
~~~~~~~~~~~~~~

Use ``pathlib.Path`` instead of ``os.path``:

.. code-block:: python

   # Good
   from pathlib import Path
   
   file_path = Path("data") / "file.csv"
   if file_path.exists():
       content = file_path.read_text()
   
   # Avoid
   import os
   
   file_path = os.path.join("data", "file.csv")
   if os.path.exists(file_path):
       with open(file_path) as f:
           content = f.read()

Use Pydantic for Models
~~~~~~~~~~~~~~~~~~~~~~~

Prefer Pydantic BaseModel over dataclasses:

.. code-block:: python

   from pydantic import BaseModel, Field
   
   class MyModel(BaseModel):
       name: str
       count: int = Field(default=0, ge=0)
       tags: list[str] = Field(default_factory=list)

Testing
-------

Writing Tests
~~~~~~~~~~~~~

* Place tests in the ``tests/`` directory
* Name test files ``test_*.py``
* Use pytest fixtures for setup/teardown
* Aim for high test coverage

Example test:

.. code-block:: python

   import pytest
   from dartfx.mtnards import MtnaRdsServer
   
   @pytest.fixture
   def server():
       """Fixture providing a test server instance."""
       return MtnaRdsServer(host="rds.highvaluedata.net")
   
   def test_server_info(server):
       """Test that server info is retrieved correctly."""
       assert server.info is not None
       assert server.info.name
       assert server.info.version

Running Tests
~~~~~~~~~~~~~

.. code-block:: bash

   # Run all tests
   uv run pytest
   
   # Run with coverage
   uv run pytest --cov=dartfx.mtnards
   
   # Run specific test file
   uv run pytest tests/test_model.py
   
   # Run specific test
   uv run pytest tests/test_model.py::test_server_info

Code Quality
------------

Linting and Formatting
~~~~~~~~~~~~~~~~~~~~~~

The project uses Ruff for linting and formatting:

.. code-block:: bash

   # Format code
   uv run ruff format .
   
   # Check for issues
   uv run ruff check .
   
   # Auto-fix issues
   uv run ruff check --fix .

Type Checking
~~~~~~~~~~~~~

.. code-block:: bash

   # Run mypy
   hatch run types:check

Pre-commit Hooks
~~~~~~~~~~~~~~~~

Pre-commit hooks automatically run before each commit:

.. code-block:: bash

   # Install hooks
   pre-commit install
   
   # Run manually
   pre-commit run --all-files

Documentation
-------------

Building Documentation
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Build HTML documentation
   cd docs
   make html
   
   # View in browser
   open build/html/index.html  # macOS
   xdg-open build/html/index.html  # Linux

Documentation Style
~~~~~~~~~~~~~~~~~~~

* Use reStructuredText (.rst) for documentation files
* Include code examples where appropriate
* Keep examples simple and focused
* Cross-reference other documentation pages

Submitting Changes
------------------

Pull Request Process
~~~~~~~~~~~~~~~~~~~~

1. Update your fork:

   .. code-block:: bash

      git fetch upstream
      git rebase upstream/main

2. Push your changes:

   .. code-block:: bash

      git push origin feature/your-feature-name

3. Create a pull request on GitHub

4. Fill out the PR template with:
   
   * Description of changes
   * Motivation and context
   * How it was tested
   * Related issues

Pull Request Checklist
~~~~~~~~~~~~~~~~~~~~~~

Before submitting, ensure:

* ☐ Code follows project style guidelines
* ☐ All tests pass
* ☐ New tests added for new functionality
* ☐ Documentation updated
* ☐ Commit messages are clear and descriptive
* ☐ No merge conflicts with main branch

Commit Messages
~~~~~~~~~~~~~~~

Write clear, concise commit messages:

.. code-block:: text

   Short summary (50 chars or less)
   
   Longer explanation if needed. Wrap at 72 characters.
   Explain the problem this commit solves and why the
   change is needed.
   
   Fixes #123

Good commit message examples:

* ``Add support for custom URI schemes in DCAT export``
* ``Fix variable classification caching issue``
* ``Update installation guide for optional dependencies``

Issue Reporting
---------------

Bug Reports
~~~~~~~~~~~

When reporting bugs, include:

* Python version
* Package version
* Operating system
* Steps to reproduce
* Expected vs actual behavior
* Error messages and stack traces

Feature Requests
~~~~~~~~~~~~~~~~

When requesting features, include:

* Use case description
* Expected behavior
* Why this would be useful
* Potential implementation approach

Code Review
-----------

What to Expect
~~~~~~~~~~~~~~

* Reviews typically within 2-3 business days
* Constructive feedback to improve code quality
* Possible requests for changes or tests
* Discussion about implementation approaches

Responding to Feedback
~~~~~~~~~~~~~~~~~~~~~~

* Address all review comments
* Ask questions if feedback is unclear
* Push additional commits to the same branch
* Mark conversations as resolved when addressed

Release Process
---------------

Version Numbering
~~~~~~~~~~~~~~~~~

The project follows `Semantic Versioning (SemVer) <https://semver.org/>`_:

* **MAJOR**: Incompatible API changes
* **MINOR**: New functionality (backward-compatible)
* **PATCH**: Bug fixes (backward-compatible)

Version is managed in ``src/dartfx/mtnards/__about__.py``

Community Guidelines
--------------------

Code of Conduct
~~~~~~~~~~~~~~~

Please read and follow our `Code of Conduct <https://github.com/DataArtifex/mtnards-toolkit/blob/main/CODE_OF_CONDUCT.md>`_.

Communication
~~~~~~~~~~~~~

* Be respectful and constructive
* Assume good intentions
* Welcome newcomers
* Help others learn

Getting Help
------------

If you need help:

* Check the documentation
* Search existing issues
* Ask in discussions
* Reach out to maintainers

Questions?
----------

Feel free to ask questions by:

* Opening a discussion on GitHub
* Creating an issue with the "question" label
* Checking the `documentation <https://www.dataartifex.org/docs/dartfx-mtnards/>`_

Thank you for contributing! 🎉
