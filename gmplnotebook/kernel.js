// file kernel.js
define([
  'base/js/namespace'
], function (
  Jupyter
) {
  return {
    onload: function () {
      var jupyter = Jupyter;
      var nb = jupyter.notebook;

      // collect code
      var collect_code = function () { 
        var cells = nb.get_cells();
        var code = '';
        for (var i = 0; i < cells.length ; i++) {
            var cell_code = cells[i].get_text();
            var cell_type = cells[i].cell_type;

            if ((cell_code.trim().startsWith("%") == false) && (cell_type === 'code')) {
                code = code.concat(cell_code, "\\n\\n");
            }
        }

        // write code to python workspace 
        var command = "%%python\nkernel.model = \'\'\'\n" + code + "\'\'\'\n" + "kernel.model_exists = True\nkernel.model = kernel.model.strip('\\n') + '\\n'";
        nb.kernel.execute(command);
      }

      var solve_handler = function () {
        // collect code, put in python workspace
        collect_code();  

        // get rid of all existing %solve cells
        cells = nb.get_cells();
        for (var i = 0 ; i < cells.length ; i++) {
          cell_code = cells[i].get_text();
          cell_type = cells[i].cell_type;
          if ((cell_code.trim().startsWith("%solve") == true) && (cell_type === 'code')) {
            nb.delete_cell(i);
          }   
        }

        // insert new cell at bottom, solve
        nb.insert_cell_at_bottom();
        var len = nb.ncells();
        cell = jupyter.notebook.get_cell(len - 1);
        cell.set_text("%solve");
        cell.execute();
        nb.scroll_to_bottom();
      };

      var solve_action = {
          icon:   'fa-calculator',
          help:   'Solve model', 
          handler: solve_handler
      };
      var solve_prefix = 'GMPL';
      var solve_action_name = 'Solve model';

      var solve = jupyter.actions.register(solve_action, solve_action_name, solve_prefix);

      jupyter.toolbar.add_buttons_group([solve]);

      /* 
       * CodeMirror definition
       * Originally used code developed by Henri Gourvest
       * This code is loosely adapted from CodeMirror modes 
       */
      CodeMirror.defineMode("mathprog", function() {
        function wordRegexp(words) {
          return new RegExp("^(?:" + words.join("|") + ")\\b", "i");
        }

        var symbolicNames = new RegExp("^[_A-Za-z\xa1-\uffff][_A-Za-z0-9\xa1-\uffff]*");
        var delimiters = new RegExp("^(\\+|\\-|\\*|/|\\*\\*|\\^|&|<|<=|=|==|>=|>|<>|!=|\\:=|\\:|!|<<|<-)");
        var keywords = wordRegexp(['abs', 'and', 'atan', 'binary', 'by', 'card',
          'ceil', 'check', 'cos', 'cross', 'cross', 'data', 'default', 'diff',
          'dimen', 'display', 'div', 'else', 'end', 'exists', 'exp', 'floor',
          'for', 'forall', 'if', 'integer', 'inter', 'Irand224', 'length',
          'less', 'log', 'log10', 'max', 'maximize', 'min', 'minimize', 'mod',
          'Normal', 'Normal01', 'not', 'or', 'param', 'printf', 'prod', 'round',
          'set', 'setof', 'sin', 'solve', 'sqrt', 'subj to', 'subject to',
          'substr', 'sum', 'symbolic', 'symdiff', 'then', 'tr', 'trunc',
          'Uniform', 'Uniform01', 'union', 'var', 'within', 'table', 'out',
          'gmtime', 'str2time', 'time2str']);

        function tokenIndex(stream, state) {
          if (stream.eatWhile(/[^}]/)) {
            state.tokenize = tokenBase;
            return 'def';
          };
          stream.skipToEnd();
          return 'def';
        }

        function tokenSubscript(stream, state) {
          if (stream.eatWhile(/[^\]]/)) {
            state.tokenize = tokenBase;
            return 'def';
          };
          stream.skipToEnd();
          return 'def';
        }

        function tokenComment(stream, state) {
          if (stream.match(/^.*\*\//)) {
            state.tokenize = tokenBase;
            return 'comment';
          };
          stream.skipToEnd();
          return 'comment';
        }

        function tokenBase(stream, state) {
          // whitespace
          if (stream.eatSpace()) {
            return null;
          }

          // single-line comments
          if (stream.match(/^#/)) {
            stream.skipToEnd();
            return 'comment';
          }

          // block comments
          if (stream.match(/\/\*/)) {
            state.tokenize = tokenComment;
            return tokenComment(stream, state);
          }

          // numberic literals
          if (stream.match(/^[0-9\.+-]/, false)) {
            if (stream.match(/^[+-]?0x[0-9a-fA-F]+[ij]?/)) {
              stream.tokenize = tokenBase;
              return 'number'; };
            if (stream.match(/^[+-]?\d*\.\d+([EeDd][+-]?\d+)?[ij]?/)) { return 'number'; };
            if (stream.match(/^[+-]?\d+([EeDd][+-]?\d+)?[ij]?/)) { return 'number'; };
          }

          // string literals
          if (stream.match(/^['"].*['"]/)) { 
            return 'string'; 
          };
          // if (stream.match(/^'([^'], (''))*'/)) { return 'string'; } ;

          // keywords
          if (stream.match(keywords)) { 
            return 'keyword'; 
          };

          // indexing expressions
          if (stream.match(/^{/)) {
            state.tokenize = tokenIndex;
            return null;
          };

          // subscripts
          if (stream.match(/^\[/)) {
            state.tokenize = tokenSubscript;
            return null;
          };

          // symbolic names (variables, sets, params)
          if (stream.match(symbolicNames)) { 
            return 'variable'; 
          };

          // delimiters
          if (stream.match(delimiters)) {
            return 'operator';
          };

          // Handle non-detected items
          stream.next();
          return null;
        };

        return {
          startState: function() {
            return {
              tokenize: tokenBase
            };
          },

          token: function(stream, state) {
            return state.tokenize(stream, state);
          }
        };
      });
    }
  };
});