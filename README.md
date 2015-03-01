## The ReMX regular expression library for Python

Differences of ReMX to the re library of Python:
 - ReMX supports tuples as regex and objects as checkables
 - ReMX is lightweight and deterministic
 - ReMX has a linear runtime
 - ReMX only supports a subset of regular
   expressions that are supported in re.
 - ReMX does not fully support extractions.

Usage:

```python
import remx
remx.compile(r"[a-zA-Z0-9_]+")                  # => <remx.remx at ...>
remx.match(r"hello( world)?", "hello day")      # => hello
remx.extract(r"hello ([a-z]+)", "hello world!") # => "hello world", ["world"]
```
