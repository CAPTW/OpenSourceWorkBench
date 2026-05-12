# Plugin Contract

OSW plugins are planned for importers, solver adapters, post-processing steps,
and report contributors. A plugin should declare:

- stable id and display name;
- supported input formats or workflow stage;
- required optional extras;
- preview capability;
- validation capability;
- execution capability only where the backend policy allows it.

v0.1 plugins must prefer preview-first behavior and structured validation
messages over direct mutation.
