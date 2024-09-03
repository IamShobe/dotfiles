# WIP
counter=0

get_existing_hook() {
    actual_name="${widgets[$1]#"user:"}"
    if [[ ${widgets[$1]} != "builtin" && ${widgets[$1]} != "user:*" && $actual_name != $2 ]]; then
        # drop the user: prefix
        echo $actual_name
    else
        # Nothing defined (or we're chaining on ourself), call the built-in we want directly
        echo "zle .$1"
    fi
}

# Prints a newline before each char
eval "_self_insert_extended() {
    counter=\$(( counter + 1 ))
    RPROMPT=\"\$counter\"
    zle redraw-prompt
    $(get_existing_hook self-insert _self_insert_extended)
}"

_self-insert() {
  #RBUFFER+="."
  #

  # execute some other command, but ensure they don't produce any output.
  zle redraw-prompt
  zle .self-insert
}

zle -N self-insert _self_insert_extended

