autoload -Uz select-word-style
function _zle-with-style() {
	setopt localoptions
	unsetopt warn_create_global
	local style
	[[ -n "$3" ]] && WORDCHARS=${WORDCHARS/$3}
	[[ $BUFFER =~ '^\s+$' ]] && style=shell || style=$2
	select-word-style $style
	zle $1
	[[ -n "$3" ]] && WORDCHARS="${WORDCHARS}${3}"
	select-word-style normal
}

function _backward-word()		{ _zle-with-style backward-word			bash }
function _forward-word()		{ _zle-with-style forward-word			bash }
function _backward-arg()		{ _zle-with-style backward-word			shell }
function _forward-arg()			{ _zle-with-style forward-word			shell }
function _backward-kill-arg()	{ _zle-with-style backward-kill-word 	shell }
function _forward-kill-arg()	{ _zle-with-style kill-word 			shell }
function _backward-kill-word()	{ _zle-with-style backward-kill-word 	normal }
function _backward-kill-path()	{ _zle-with-style backward-kill-word 	normal	'/' }

zle -N _backward-word
zle -N _forward-word
zle -N _backward-arg
zle -N _forward-arg
zle -N _backward-kill-arg
zle -N _forward-kill-arg
zle -N _backward-kill-word
zle -N _backward-kill-path

# optionally support putty-style cursor keys (application mode when ctrl is pressed).
# this is kind of broken in normal linux terminals that often use application mode by
# default, so we have to make it opt-in. if you use putty, you may want to patch it to
# send proper escape sequences for ctrl/alt/shift+cursor key combinations.
if [[ _custom_zsh_putty_cursor_keys == 1 ]]; then
	bindkey '\C-[OD'	_backward-word	# ctrl-left
	bindkey '\C-[OC'	_forward-word	# ctrl-right
fi

bindkey "\e[1;5D"	_backward-word		# ctrl-left
bindkey "\e[1;5C"	_forward-word		# ctrl-right
bindkey '\e\e[D'	_backward-arg		# alt-left
bindkey '\e[1;3D'	_backward-arg		# alt-left
bindkey '\e[1;3C'	_forward-arg		# alt-right
bindkey '\e\e[C'	_forward-arg		# alt-right
bindkey '\e\C-?'	_backward-kill-arg	# alt-backspace
bindkey '\e\e[3~'	_forward-kill-arg	# alt-del
bindkey '\e[3;3~'	_forward-kill-arg	# alt-del
bindkey '\C-w'		_backward-kill-word
bindkey '\C-f'		_backward-kill-path

