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
        collect_code()  

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
      var solve_prefix = 'GLPK';
      var solve_action_name = 'Solve model';

      var solve = jupyter.actions.register(solve_action, solve_action_name, solve_prefix);

      jupyter.toolbar.add_buttons_group([solve]);

      /* This code was developed by Henri Gourvest and used with his permission. */
      CodeMirror.defineMode("mathprog",
        function(config, parserConfig) {

          function isalpha(c){
            var code = c.charCodeAt(0);
            return (code >= 0x41 && code <= 0x5A)|| (code >= 0x61 && code <= 0x7A) || (code == 0x5F)
          }

          function isalnum(c){
            var code = c.charCodeAt(0);
            return (code >= 0x41 && code <= 0x5A)|| (code >= 0x61 && code <= 0x7A) || (code >= 0x30 && code <= 0x39) || (code == 0x5F)
          }

          function isnum(c){
            var code = c.charCodeAt(0);
            return (code >= 0x30 && code <= 0x39)
          }

          return {
            startState: function(basecolumn) {
              return {state: 0};
            },

            token: function(stream, state) {
              if (stream.eatSpace()) return;

              function getToken(c){
                if (isalpha(c)){
                  tokstart = stream.start;
                  stream.eatWhile(isalnum);
                  var token = stream.string.slice(tokstart, stream.pos).toLowerCase();
                  switch (token){

                    default:
                    return;
                  }
                } else if(isnum(c)) {
                  stream.eatWhile(isnum);
                  return "number";
                }
                return "error";
              }


              var c;
              while (c = stream.next()){
                switch (state.state){
                  case 0:
                  switch (c){
                    case '/':
                    state.state = 1; break;
                    case '#':
                    stream.skipToEnd();
                    return "comment";
                    case "'":
                    case '"':
                    if (!stream.eol()){
                      state.stringChar = c;
                      state.state = 4;
                      break;
                    } else {
                      state.state = 0;
                      return "error";
                    }
                    case '[':
                    case ']':
                    case '(':
                    case ')':
                    case '{':
                    case '}':
                    return "bracket";
                    return "def";
                    default:
                    if (isnum(c)){
                      var s = 0;
                      stream.eatWhile(function(v){
                        switch (s) {
                          case 0:
                          if (isnum(v)) return true;
                          switch (v){
                            case '.': s = 1; return true;
                            case 'e':
                            case 'E':
                            s = 2; return true;
                            default:
                            return false;
                          }
                          case 1:
                          if (isnum(v)) return true;
                          switch (v){
                            case 'e':
                            case 'E':
                            s = 2; return true;
                            default:
                            return false;
                          }
                          case 2:
                          if (isnum(v)){
                            s = 3;
                            return true;
                          }
                          switch (v){
                            case '+':
                            case '-':
                            s = 3;
                            return true;
                            default:
                            return false;
                          }
                          case 3:
                          return isnum(v);
                        }
                      })
                      return "number";
                    } else if (isalpha(c)) {
                      var p = 0;
                      stream.eatWhile(
                        function(v){
                          switch(p){
                            case 0:
                            if (isalnum(v)) return true;
                            if (v == '.' && stream.current() == 's'){
                              p = 1;
                              return true;
                            }
                            return false;
                            case 1:
                            p = 2;
                            return (v == 't');
                            case 2:
                            return (v == '.')
                          }

                        }
                        );
                      var token = stream.current();
                      switch (token) {
                        case 'param':
                        case 'var':
                        case 'maximize':
                        case 'minimize':
                        case 's.t.':
                        case 'data':
                        case 'end':
                        case 'set':
                        case 'table':
                        case 'subject':
                        case 'to':
                        case 'subj':
                        case 'check':
                        case 'display':
                        case 'for':
                        return "keyword";
                        case 'dimen':
                        case 'default':
                        case 'integer':
                        case 'binary':
                        case 'logical':
                        case 'symbolic':
                        case 'OUT':
                        case 'IN':
                        case 'and':
                        case 'by':
                        case 'cross':
                        case 'diff':
                        case 'div':
                        case 'else':
                        case 'if':
                        case 'in':
                        case 'Infinity':
                        case 'inter':
                        case 'less':
                        case 'mod':
                        case 'not':
                        case 'or':
                        case 'symdiff':
                        case 'then':
                        case 'union':
                        case 'within':
                        return "atom";
                        case 'sum':
                        case 'prod':
                        case 'min':
                        case 'max':
                        return "def";
                        case 'printf':
                        return "builtin";
                        case 'abs':
                        case 'atan':
                        case 'card':
                        case 'ceil':
                        case 'cos':
                        case 'exp':
                        case 'floor':
                        case 'gmtime':
                        case 'length':
                        case 'log':
                        case 'log10':
                        case 'max':
                        case 'min':
                        case 'round':
                        case 'sin':
                        case 'sqrt':
                        case 'str2time':
                        case 'trunc':
                        case 'Irand224':
                        case 'Uniform01':
                        case 'Uniform':
                        case 'Normal01':
                        case 'Normal':
                        return "def"
                      }
                      return
                    }
                    return;
                  }
                  break;
                  case 1:
                  if (c == '*'){
                    state.state = 2;
                  }
                  else {
                    state.state = 0
                    return "operator";
                  }
                  break;
                  case 2:
                  if (c == '*') state.state=3; break;
                  case 3:
                  if (c == '/'){
                    state.state = 0;
                    return "comment";
                  } else
                  state.state = 2;
                  break;
                  case 4:
                  if (c == state.stringChar){
                    if (!stream.eol()){
                      state.state = 5;
                      break;
                    } else {
                      state.state = 0;
                      delete(state.stringChar);
                      return "string";
                    }
                  } else if (stream.eol()) {
                    state.state = 0;
                    delete(state.stringChar);
                    return "error";
                  }
                  break;
                  case 5:
                  if (c != state.stringChar){
                    stream.pos--;
                    state.state = 0;
                    delete(state.stringChar);
                    return "string";
                  } else {
                    if (!stream.eol()){
                      state.state = 4;
                      break;
                    } else {
                      state.state = 0;
                      delete(state.stringChar);
                      return "error";
                    }

                  }
                }
              }
              if (state.state == 2) return "comment"
            }
        };
      }
      );
}
  };
});