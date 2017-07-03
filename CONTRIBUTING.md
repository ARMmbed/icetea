# Description
This document is cheat sheet for everyone who wants to contribute to [ARMmbed/mbed-test](https://github.com/ARMmbed/mbed-test) GitHub repository at GitHub. 
All changes in code base should originate from GitHub Issues and take advantage of existing GitHub flows. Goal is to attract contributors and allow them contribute to code and documentation at the same time.

Guidelines from this document are created to help new and existing contributors understand process workflow and align to project rules before pull request is submitted. It explains how a participant should do things like format code, test fixes, and submit patches.

# How to contribute
We really appreciate your contributions! We are Open Source project and we need your help. We want to keep it as easy as possible to contribute changes that get things working in your environment. There are a few guidelines that we need contributors to follow so that we can have a chance of keeping on top of things.

You can pick up existing [mbed-test GitHub Issue](https://github.com/ARMmbed/mbed-test/issues) and solve it or implement new feature you find important, attractive or just necessary. We will review your proposal via pull request mechanism, give you comments and merge your changes if we decide your contribution satisfy criteria such as quality.

# Enhancements vs Bugs
Enhancements are:
* New features implementation.
* Code refactoring.
* Coding rules, coding styles improvements.
* Code comments improvement.
* Documentation work.

Bugs are:
* Issues rose internally or externally by [ARMmbed/mbed-test](https://github.com/ARMmbed/mbed-test) users.
* Internally (within mbed-tools team) created issues from Continuous Integration pipeline and build servers.
* Issues detected using CI

# Gate Keeper role
Gate Keeper is a person responsible for GitHub process workflow execution and is responsible for repository / project code base. Gate Keeper is also responsible for code (pull request) quality stamp and approves or rejects code changes in project’s code base.

Gate Keepers will review your pull request code, give you comments in pull request comment section and in the end if everything goes well merge your pull request to one of our branches (most probably default ```master``` branch).

Please be patient, digest Gate Keeper's feedback and respond promptly :)

# Glossary
* Gate Keeper – persons responsible for overall code-base quality of [ARMmbed/mbed-test](https://github.com/ARMmbed/mbed-test) project.
* Enhancement – New feature deployment, code refactoring actions or existing code improvements.
* Bugfix – Issues originated from GitHub Issues pool, raised internally within tools team or issues from automated code validators like linters, static code analysis tools etc.