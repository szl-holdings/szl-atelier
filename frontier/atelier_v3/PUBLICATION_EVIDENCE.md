# Atelier publication evidence

`PUBLICATION_RECEIPT.json` is an immutable preparation receipt. Its
`PACKAGE_BUILT_NOT_PUBLISHED` state describes the moment the package was built.
Uploading the file does not turn it into a publication-completion receipt. It
cannot contain the commit identifier of the upload that contains itself.

The builder returns exactly the receipt stored in the package. Its digest covers
the preparation fields and payload file measurements, excluding the receipt
file itself. The publisher compares the package and receipt against the
canonical source projection before making provider calls, including when a
modified package is accompanied by a newly computed receipt digest.

The separate report selected by the publisher's `--report` argument records
completed provider observations. `EXACT_READBACK_VERIFIED` requires the returned
upload commit, immutable remote file hashes, the provider head, and the running
runtime commit to agree. Provider identity is read before and after the health,
readiness, and application-source requests. Provider head drift fails the run;
missing running-commit evidence cannot produce a success report.

The completion report includes `package_receipt_file_sha256`, binding its
observations to the exact preparation receipt file. It is kept outside the
Space projection, as an artifact of the canonical publication workflow. A
preparation receipt alone is insufficient evidence of runtime readiness.

These checks rely on the release workflow first qualifying the source checkout
and the approved GitHub revision. A SHA supplied to the offline builder is a
declaration, not an authenticated checkout or a deployment authorization.
Readback proves the observations recorded during the run, not future uptime or
independent third-party attestation. Existing credential and release holds still
apply; this change does not rotate credentials or deploy a Space.
