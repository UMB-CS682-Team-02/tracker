
# Roundup Tracker

## Introduction

Roundup Tracker is an issue-tracking system designed for knowledge workers. It serves as a versatile tool for creating various types of trackers, including:

- Bug trackers
- Help desks
- Agile development trackers
- Customer issue tracking
- Fleet maintenance tracking
- GTD (Getting Things Done) tools

Roundup comes with predefined trackers that are customizable to suit your workflow. These include:

- Generic tracker
- Development bug/feature tracker (with three variations)
- Bare-bones minimal tracker

Users can interact with the system (create, read, update, close issues) via a web interface or email. Additionally, Roundup can be managed programmatically via REST, XMLRPC, CLI, or through local Python scripts.

For a comprehensive guide, refer to the [User's Guide](https://www.roundup-tracker.org/docs/user_guide.html).

## Instant Gratification

If you're eager to try Roundup, you can quickly get started by running `demo.py` from the source directory:

```bash python demo.py```

This will create a new tracker home in the "demo" subdirectory and start a web server. To reset the demo instance:

```bash python demo.py nuke ```


For more details, see the ["For the Really Impatient"](https://roundup-tracker.org/docs/installation.html#for-the-really-impatient) section of the installation document, or use the Docker demo mode.

### Tracker Home

The "Tracker Home" is a central concept in Roundup. It refers to the directory where all your tracker data is stored. This directory is created each time a new tracker is initialized and includes the tracker configuration, database, templates, schema, and extensions.

## Installation

To install Roundup, follow these steps:

1. **Set up a virtual environment:**

   ```bash
   python3 -m venv roundup
   . roundup/bin/activate
   python -m pip install roundup
   ```


2. **Start a test demo instance:**

    ```
    bash roundup-demo 
    ```

For detailed installation instructions and deploying a production instance, see the [Installation Guide](https://roundup-tracker.org/docs/installation.html#for-the-really-impatient).

## Upgrading

For upgrade instructions, please refer to `doc/upgrading.txt`.

## Security Issues

To report security issues, follow the directions in `doc/security.txt`.

## Other Information

For additional documentation, start with the `index.txt` file in the "doc" directory. These files are written in reStructuredText, which can be converted into HTML format using Sphinx:

```bash
python setup.py build_doc 
```

The resulting HTML files will be located in the `share/doc/roundup/html` directory.

## Contributing

If you'd like to contribute to Roundup, please read the `doc/developers.txt` file. This document outlines the project rules, how to set up a development environment, and how to submit patches and tests.

## Support/Contact

For support or to contact the developers, visit the [Roundup Contact Page](https://www.roundup-tracker.org/contact.html).

## License

Roundup is licensed under the MIT, Zope version 2, and Python Software Foundation version 2 licenses. For more information, see the `COPYING.txt` file.
