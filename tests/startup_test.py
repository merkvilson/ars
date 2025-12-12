from ars_cmds.core_cmds.load_object import add_primitive, selected_object
from ars_cmds.util_cmds.time_cmd import after, delay
def main(ars_window):
    print("Running startup tests...")



def run_tests(ars_window):
    after(3000, lambda: main(ars_window))
