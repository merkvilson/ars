import textwrap

with open("ars_scripts/editor/script_header.py", "r") as header_file:
    HEADER = header_file.read()

def ars_script_wrapper(content: str) -> str:
    """
    Wraps the given content in a plugin execution function,
    indenting it appropriately within the function body.
    """
    header = HEADER
    footer = "# End of script"

    indented_content = textwrap.indent(content.strip(), "    ")

    result = f"{header}\n{indented_content}\n{footer}"

    return result