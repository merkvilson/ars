"""Quick manual test for :func:`util_functions.ars_window.ars_window`."""

from util_functions.ars_window import ars_window


if __name__ == "__main__":
	try:
		print(ars_window())
	except RuntimeError as exc:
		print(f"ars_window() is unavailable: {exc}")