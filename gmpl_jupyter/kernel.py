from __future__ import print_function

from IPython.display import HTML
from metakernel import MetaKernel, Magic
from glpk import LPX, env
from tempfile import NamedTemporaryFile
import sys
import os
import json
import pkgutil
import subprocess
from traitlets.config import Application
from ipykernel.kernelapp import IPKernelApp
from IPython.utils.tempdir import TemporaryDirectory

_module_name = 'jupyter'


class GMPLJupyter(MetaKernel):
    implementation = 'gmpl-jupyter'
    implementation_version = '0.1'
    language = 'gmpl'
    language_version = '1.0'
    banner = "A GNU MathProg (GMPL) kernel for Jupyter"
    language_info = {
        'mimetype': 'text/plain',
        'name': 'GMPL/MathProg',
        'file_extension': '.mod',
        'codemirror_mode': 'mathprog',
        'help_links': MetaKernel.help_links,
    }
    kernel_json = {
        "argv": [sys.executable, '-m', 'gmpl_jupyter',
                 '-f', '{connection_file}'],
        "display_name": "GMPL/MathProg",
        "language": "gmpl",
        "mimetype": "text/plain",
        "name": "gmpl",
    }

    model = ''
    model_exists = False

    @classmethod
    def run_as_main(cls):
        GMPLJupyterApp.launch_instance(kernel_class=cls)

    def __init__(self, **kwargs):
        super(GMPLJupyter, self).__init__(**kwargs)
        self.register_magics(SolveMagic)

    def get_usage(self):
        return "This is the GMPL/MathProg kernel."

    def do_execute_direct(self, code):
        pass

    def repr(self, data):
        return repr(data)


class SolveMagic(Magic):
    def line_solve(self):
        if self.kernel.model_exists:
            # Terminal hook helper function
            def term_hook(output):
                log_file.write(output)
            env.term_hook = term_hook

            # Create temporary log file
            log_file = NamedTemporaryFile(mode='w+t', suffix='.log')

            # Create temporary output file
            out_file = NamedTemporaryFile(mode='w+t', suffix='.out')

            # Create temporary model file
            model_file = NamedTemporaryFile(mode='w+t', suffix='.mod')
            model_file.write(self.kernel.model)
            model_file.seek(0)

            # Load .mod file into GLPK
            try:
                lp = LPX(gmp=(model_file.name, None, None))
            except RuntimeError:
                pass
            else:
                # Solve the .mod file using the simplex method
                msg_lev = lp.MSG_ALL
                simplex_presolve = False
                if lp.kind is float:
                    # LP: simplex method
                    # Turn off presolve to get information about infeasibility
                    #   and unboundedness
                    lp.simplex(msg_lev=msg_lev, presolve=simplex_presolve)
                else:
                    # MIP: branch-and-cut
                    lp.integer(msg_lev=msg_lev, presolve=True)

                # Capture output file into a string
                lp.write(sol=out_file.name)
                out_file.seek(0)
                out_text = "\n=======================================\n"
                for line in out_file:
                    out_text += line

                # Determine status
                if lp.status == 'opt':
                    status = 'Solution found is optimal'
                elif lp.status == 'undef':
                    status = 'Solution found is undefined'
                elif lp.status == 'feas':
                    status = ('Solution found is feasible, ' +
                              'but not necessarily optimal')
                elif lp.status == 'infeas':
                    status = 'Solution found is infeasible'
                elif lp.status == 'nofeas':
                    status = 'LP is infeasible'
                elif lp.status == 'unbnd':
                    status = 'LP is unbounded'

                # Form solution HTML
                solution_html = '''
                    <table style="border-style:hidden;">
                        <tr style="border-style:hidden;">
                            <td style="font-weight:bold;border-style:hidden;
                            text-align:right;">Status</td>
                            <td style="border-style:hidden;">{0}</td>
                        </tr>
                        <tr>
                            <td style="font-weight:bold;border-style:hidden;
                            text-align:right;">Objective value</td>
                            <td style="border-style:hidden;">{1:.4f}</td>
                        </tr>
                    </table>
                '''
                solution_html = solution_html.format(status, lp.obj.value)

                solution_html += '''
                    <table style="border-style:hidden;">
                        <tr style="border-style:hidden;">
                            <th style="border-style:hidden;">Variable</th>
                            <th style="border-style:hidden;">Value</th>
                        </tr>
                '''

                solution_html_variable_row = '''
                        <tr style="border-style:hidden;">
                            <td style="border-style:hidden;">{0}</td>
                            <td style="text-align:right;border-style:hidden;">
                            {1:.4f}</td>
                        </tr>
                '''

                for col in lp.cols:
                    solution_html += solution_html_variable_row.format(
                        col.name, col.primal
                    )

                solution_html += '''
                    </table>
                '''

            # Capture log file into a string
            log_text = ''
            log_file.seek(0)
            for line in log_file:
                # Don't print GLPK log lines regarding which files
                # the model and data are being read from
                if not (line.startswith('Reading model section') or
                        line.startswith('Reading data section')):
                    # Replace the temporary model file name
                    # with something more human-readable
                    # line = line.replace(model_file.name + ':',
                                        # "Error around line ")
                    log_text += line

            # Capture model with line numbers
            model_with_line_numbers = ''
            for i, line in enumerate(self.kernel.model.split('\n')):
                model_with_line_numbers += (
                    "{0:>4}  {1}\n".format(i + 1, line)
                )

            css_code = '''
                <style>
                    body {font-family: sans-serif;}

                    ul.tab {
                        list-style-type: none;
                        margin: 0;
                        padding: 0;
                        overflow: hidden;
                        border: 1px solid #ccc;
                        background-color: #f1f1f1;
                    }

                    /* Float the list items side by side */
                    ul.tab li {float: left;}

                    /* Style the links inside the list items */
                    ul.tab li a {
                        display: inline-block;
                        color: black;
                        text-align: center;
                        padding: 14px 16px;
                        text-decoration: none;
                        transition: 0.3s;
                        font-size: 17px;
                    }

                    /* Change background color of links on hover */
                    ul.tab li a:hover {
                        background-color: #ddd;
                    }

                    /* Create an active/current tablink class */
                    ul.tab li a:focus, .active {
                        background-color: #ccc;
                    }

                    /* Style the tab content */
                    .tabcontent {
                        display: none;
                        padding: 12px;
                        border: 1px solid #ccc;
                        border-top: none;
                    }
                </style>
            '''

            html_code = '''
            <body>
                <ul class="tab">
                <li><a href="#" style="text-decoration:none;"
                  class="tablinks active" onclick="openTab(event, 'Solution')">
                  Solution</a></li>
                <li><a href="#" style="text-decoration:none;"
                  class="tablinks" onclick="openTab(event, 'Model')">
                  Model</a></li>
                <li><a href="#" style="text-decoration:none;"
                  class="tablinks" onclick="openTab(event, 'Logs')">
                  Logs</a></li>
                </ul>

                <div id="Solution" class="tabcontent" style="display:block;">
                    {0}
                </div>

                <div id="Model" class="tabcontent">
                    <pre>{1}</pre>
                </div>

                <div id="Logs" class="tabcontent">
                    <pre>{2}</pre>
                </div>
            '''

            js_code = '''
                <script>
                function openTab(evt, tabName) {
                    var i, tabcontent, tablinks;
                    tabcontent = document.getElementsByClassName("tabcontent");
                    for (i = 0; i < tabcontent.length; i++) {
                        tabcontent[i].style.display = "none";
                    }
                    tablinks = document.getElementsByClassName("tablinks");
                    for (i = 0; i < tablinks.length; i++) {
                        tablinks[i].className = tablinks[i].className
                            .replace(" active", "");
                    }
                    document.getElementById(tabName).style.display = "block";
                    evt.currentTarget.className += " active";
                }
                </script>
            </body>
            '''

            # Fill in the HTML template with stuff
            try:
                solution_html
            except (NameError, UnboundLocalError):
                error_html = 'Error! Check the logs for details.'
                html_code = html_code.format(error_html,
                                             model_with_line_numbers,
                                             log_text)
            else:
                html_code = html_code.format(solution_html,
                                             model_with_line_numbers,
                                             log_text + out_text)

            self.kernel.Display(HTML(css_code + html_code + js_code))

            # Close the temporary files
            model_file.close()
            log_file.close()
            out_file.close()

            # Expose GLPK object
            try: 
                self.kernel.lp = lp
            except (NameError, UnboundLocalError):
                pass

            # Erase model
            self.kernel.model_exists = False
            self.kernel.model = ''
        else:
            print("Please use the solve button in the toolbar.")


class GMPLJupyterApp(IPKernelApp):
    # This is a hacky re-write of MetaKernelApp to accomodate kernel.js
    @property
    def subcommands(self):
        # Slightly awkward way to pass the actual kernel class to the install
        # subcommand.

        class KernelInstallerApp(Application):
            kernel_class = self.kernel_class

            def initialize(self, argv=None):
                self.argv = argv

            def start(self):
                kernel_spec = self.kernel_class.kernel_json
                with TemporaryDirectory() as td:
                    # Create temporary kernelspec directory
                    dirname = os.path.join(td, kernel_spec['name'])
                    os.mkdir(dirname)

                    # Write kernel.json
                    with open(os.path.join(dirname, 'kernel.json'), 'w') as f:
                        json.dump(kernel_spec, f, sort_keys=True)

                    # Write kernel.js
                    filename = 'kernel.js'
                    data = pkgutil.get_data('gmpl_jupyter', filename)
                    with open(os.path.join(dirname, filename), 'wb') as f:
                            f.write(data)

                    # Write logo files, using MetaKernel defaults
                    filenames = ['logo-64x64.png', 'logo-32x32.png']
                    for filename in filenames:
                        data = pkgutil.get_data('metakernel',
                                                'images/' + filename)
                        with open(os.path.join(dirname, filename), 'wb') as f:
                            f.write(data)

                    # Install: python -m jupyter kernelspec install ...
                    try:
                        subprocess.check_call(
                            [sys.executable, '-m', _module_name,
                             'kernelspec', 'install'] + self.argv + [dirname])
                    except subprocess.CalledProcessError as exc:
                        sys.exit(exc.returncode)

        return {'install': (KernelInstallerApp, 'Install this kernel')}
