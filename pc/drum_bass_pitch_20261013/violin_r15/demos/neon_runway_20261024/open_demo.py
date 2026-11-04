import argparse
from pathlib import Path
import sys


HERE = Path(__file__).resolve().parent
APP = HERE.parents[1]
BASE = APP.parent
sys.path[:0] = [str(APP), str(BASE / 'host'), str(BASE / 'tools/python_deps')]

from arrangement_model import Project
from host_controller import ViolinController


def main():
    parser = argparse.ArgumentParser(description='Open the arrangement without connecting or playing hardware.')
    parser.add_argument('--short', action='store_true')
    options = parser.parse_args()
    path = HERE / ('Neon_Runway_8bars.tang.json' if options.short else 'Neon_Runway_32bars.tang.json')
    project = Project.load(path)
    app = ViolinController()
    panel = app.arrangement_panel
    panel._replace(project, str(path))
    panel.ensemble.set(True)
    panel.hardware.set(False)
    panel.loop.set(False)
    app.show_page('arrangement')
    panel.status.set('已载入霓虹航线；未连接、未播放。先连接 FPGA UART 并探测能力，再勾选实机发送。')
    app.mainloop()


if __name__ == '__main__':
    main()
