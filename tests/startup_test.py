from ars_cmds.core_cmds.load_object import add_primitive
from ars_cmds.util_cmds.time_cmd import after
# from ars_cmds.render_cmds.render_pass import save_normal


def main(ars_window):
    
    add_primitive("cube")
    # save_normal(ars_window)
    # print("finish")

def run_tests(ars_window):
    after(3000, lambda: main(ars_window))
