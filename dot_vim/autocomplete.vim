function! GetPythonInterpeter()
    if !empty($VIRTUAL_ENV)
        return $VIRTUAL_ENV . "/bin/python"
    else
        return ""
    endif
endfunction

let g:ycm_python_interpreter_path = GetPythonInterpeter()
let g:ycm_python_sys_path = []
let g:ycm_extra_conf_vim_data = [
  \  'g:ycm_python_interpreter_path',
  \  'g:ycm_python_sys_path'
  \]
let g:ycm_global_ycm_extra_conf = '$VIM_HOME/global_extra_conf.py'

