Sprout
======

This is a common Python library which contains reusable components,
developed at Infrae.

Sprout, while mainly XML related, does not have a functional goal as
such. Its goals instead are organizational:

* Enable code reuse between projects, such as Silva and Infrae's
  topicmaps implementation

* Allow us to write modern, pure Python code without external
  dependencies -- it only depends on the Python standard library.

* Allow us to write solid code, covered by a large unit test
  suite. The lack of external dependencies and focus on modern code
  makes this easier.

While Sprout's aim is mainly for use within Infrae at present, the
code inside should be general enough for use in your own projects as
well.

Sprout's focus is mainly currently XML related. It features:

* ``sprout.saxext``, a library to make writing SAX-based code more
  easy.

* ``htmlsubset``, a system to easily create HTML-ish subsets that are
  secure and robust to wrong user input.
