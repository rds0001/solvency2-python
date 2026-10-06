# Security

Report suspected security issues to riskdatascience@web.de. Include the package
version and a minimal synthetic reproducer; do not email actual policyholder,
portfolio or other confidential data. No response-time guarantee is implied.

The library does not fetch remote data. Treat local inputs as untrusted: control
file size, permissions and provenance in your application. Parsers validate
schemas but are not a resource-isolation sandbox. Do not run untrusted Python
code or untrusted package builds. Protect exported calculation/audit records as
you would the inputs they describe.
