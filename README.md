# Cumulus Library LOINC

An installation of the LOINC® ontology. Part of the 
[SMART on FHIR Cumulus Project](https://smarthealthit.org/cumulus)

For more information,
[browse the documentation](https://docs.smarthealthit.org/cumulus/library).

## Usage

You can install this module by running `pip install cumulus-library-loinc`.

This will add a `loinc` target to `cumulus-library`. 

The contents of this dataset are described at the
[LOINC website](https://loinc.org/).
You will need to register an account on their website to use this data. When you build
this study, you'll need to provide your user and password as custom options. Your build
command should look like this:

```bash
cumulus-library build -t loinc --loinc_user your_username --loinc_password your_password [any other cli agurments]
```

You can, if you prefer, create environment variables to hold this data. We'll check for the
prescence of `LOINC_USER` and `LOINC_PASSWORD` if the CLI arguments are not provided.

Note: This study is explicitly namespaced in its own schema, `loinc`. Make sure your
database is not using this schema for another use. Do not create tables inside this
schema by another means.

## Tables

We are currently inserting a subset of Loinc tables, focused on Cumulus use cases:

- The LOINC core table, and its associated mapping table for older versions
- The group tables (see the [groups page](https://loinc.org/groups/) for usage caveats)
- The consumer names of medications
- The document ontology
- The lab order value set

## Licensing details

This material contains content from LOINC (http://loinc.org). LOINC is copyright © Regenstrief
Institute, Inc. and the Logical Observation Identifiers Names and Codes (LOINC) Committee and 
is available at no cost under the license at http://loinc.org/license. LOINC® is a registered 
United States trademark of Regenstrief Institute, Inc.

Where the product or service is distributed with a printed license, this notice must appear in
the printed license. Where the product or service is distributed on a fixed storage medium, a
text file containing this notice also must be stored on the storage medium in a file called 
"LOINC_short_license.txt." Where the product or service is distributed via the Internet, this
notice must be accessible on the same Internet page from which the product is available for
download. Where the product or service is provided as an online resource (e.g., to be accessed
programmatically through an application programming interface (API) or through a user interface),
this notice must be available in the license or terms of use.
