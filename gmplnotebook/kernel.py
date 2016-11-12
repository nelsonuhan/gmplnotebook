from __future__ import print_function

import glpk
import tempfile
import sys
import os
import json
import pkgutil
import shutil
import subprocess
import uuid
from IPython.display import HTML
from metakernel import MetaKernel, Magic
from traitlets.config import Application
from ipykernel.kernelapp import IPKernelApp
from IPython.utils.tempdir import TemporaryDirectory

_module_name = 'jupyter'


class GMPLNotebook(MetaKernel):
    implementation = 'gmplnotebook'
    implementation_version = '0.1'
    language = 'gmpl'
    language_version = 'December 2010'
    banner = "A GNU MathProg (GMPL) kernel for Jupyter"
    language_info = {
        'mimetype': 'text/plain',
        'name': 'GMPL/MathProg',
        'file_extension': '.mod',
        'codemirror_mode': 'mathprog',
        'help_links': MetaKernel.help_links,
    }
    kernel_json = {
        "argv": [sys.executable, '-m', 'gmplnotebook',
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
        GMPLNotebookApp.launch_instance(kernel_class=cls)

    def __init__(self, **kwargs):
        super(GMPLNotebook, self).__init__(**kwargs)
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
            glpk.env.term_on = True 
            glpk.env.term_hook = lambda output: log_file.write(output)

            # Create temporary directory
            temp_dir = tempfile.mkdtemp()

            # Create base filename
            base_name = uuid.uuid4().hex

            # Create output file name
            out_file_name = os.path.join(temp_dir, base_name + '.out') 

            # Create log file
            log_file_name = os.path.join(temp_dir, base_name + '.log')
            log_file = open(log_file_name, 'w')

            # Create model file
            model_file_name = os.path.join(temp_dir, base_name + '.mod')
            model_file = open(model_file_name, 'w')
            model_file.write(self.kernel.model)
            model_file.close()

            # Load .mod file into GLPK
            try:
                lp = glpk.LPX(gmp=(model_file_name, None, None))
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
                elif lp.kind is int:
                    # MIP: branch-and-cut
                    lp.integer(msg_lev=msg_lev, presolve=True)

                # Write output file 
                if lp.kind is float:
                    lp.write(sol=out_file_name)
                elif lp.kind is int:
                    lp.write(mip=out_file_name)

                # Read contents of output file into a string
                out_file = open(out_file_name, 'r')
                out_text = "\n=======================================\n"
                for line in out_file:
                    out_text += line
                out_file.close()    

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
                    status = 'Model is infeasible'
                elif lp.status == 'unbnd':
                    status = 'Model is unbounded'

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
                    <div style="width:50%;float:left;">
                    <table style="border-style:hidden;">
                        <tr style="border-style:hidden;">
                            <th style="border-style:hidden;">Variable</th>
                            <th style="border-style:hidden;">Value</th>
                        </tr>
                '''

                solution_html_table_row = '''
                        <tr style="border-style:hidden;">
                            <td style="border-style:hidden;">{0}</td>
                            <td style="text-align:right;border-style:hidden;">
                            {1:.4f}</td>
                        </tr>
                '''

                for col in lp.cols:
                    solution_html += solution_html_table_row.format(
                        col.name, col.primal
                    )

                solution_html += '''
                    </table>
                    </div>
                '''

                if lp.kind is float:
                    solution_html += '''
                        <div style="width:50%;float:right;">
                        <table style="border-style:hidden;">
                            <tr style="border-style:hidden;">
                                <th style="border-style:hidden;">
                                    Constraint
                                </th>
                                <th style="border-style:hidden;">
                                    Dual Value
                                </th>
                            </tr>
                    '''

                    for row in lp.rows:
                        solution_html += solution_html_table_row.format(
                            row.name, row.dual
                        )

                    solution_html += '''
                        </table>
                        </div>
                    '''
            finally:
                # Close log file
                log_file.close()

            # Read log file into a string
            log_file = open(log_file_name, 'r')
            log_text = ''
            for line in log_file:
                # Don't print GLPK log lines regarding which files
                # the model and data are being read from
                if not (line.startswith('Reading model section') or
                        line.startswith('Reading data section') or
                        line.startswith('Writing basic solution') or
                        line.startswith('Writing MIP solution')):
                    # Replace the temporary model file name
                    # with something more human-readable
                    line = line.replace(model_file_name + ':',
                                        "Line ")
                    log_text += line
            log_file.close()

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
                    <li>
                        <a href="#" style="text-decoration:none;"
                            class="tablinks active"
                            onclick="openTab(event, '_Solution')">
                            Solution</a>
                    </li>
                    <li>
                        <a href="#" style="text-decoration:none;"
                            class="tablinks"
                            onclick="openTab(event, '_Model')">
                            Model</a>
                    </li>
                    <li>
                        <a href="#" style="text-decoration:none;"
                            class="tablinks"
                            onclick="openTab(event, '_Logs')">
                            Logs</a>
                    </li>
                </ul>

                <div id="_Solution" class="tabcontent" style="display:block;
                    overflow:hidden;">
                    {0}
                </div>

                <div id="_Model" class="tabcontent">
                    <pre>{1}</pre>
                </div>

                <div id="_Logs" class="tabcontent">
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

            # Erase model
            self.kernel.model_exists = False
            self.kernel.model = ''

            # Remove the temporary files
            shutil.rmtree(temp_dir)
        else:
            print("Please use the solve button in the toolbar.")


class GMPLNotebookApp(IPKernelApp):
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
                    data = pkgutil.get_data('gmplnotebook', filename)
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
