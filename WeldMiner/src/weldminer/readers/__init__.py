"""Document parsing and multimodal input handling.

Imports stay explicit at call sites so loading ``multimodal_input`` does not
eagerly import ``parser`` and create a cycle through ``core.llm_utils``.
"""
